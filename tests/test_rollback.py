import importlib
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from font_fixtures import make_font

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


class Registry:
    def __init__(self, fail_on=None):
        self.values = {'Segoe UI (TrueType)': ('custom-original.ttf', 1),
                       'Malgun Gothic (TrueType)': ('malgun.ttf', 1),
                       'Segoe UI Emoji (TrueType)': ('seguiemj.ttf', 1)}
        self.fail_on = fail_on

    def get(self, name):
        return self.values.get(name)

    def set(self, name, value):
        if name == self.fail_on and value[0].endswith('_system_mod.ttf'):
            raise OSError('injected registry failure')
        self.values[name] = value

    def delete(self, name):
        self.values.pop(name, None)


class RollbackTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('font_transaction'), 'Registry rollback support is missing')
        return importlib.import_module('font_transaction')

    def fixture(self, tmp):
        root = Path(tmp)
        for name in ('sources', 'Fonts', 'state'):
            (root / name).mkdir()
        make_font(root / 'sources/segoeui_system_mod.ttf', 'Segoe UI')
        make_font(root / 'sources/malgun_system_mod.ttf', 'Malgun Gothic')
        return root

    def test_middle_failure_restores_exact_values_and_removes_only_new_files(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            (root / 'Fonts/seguiemj.ttf').write_bytes(b'emoji original')
            registry = Registry('Malgun Gothic (TrueType)')
            original = dict(registry.values)
            with self.assertRaisesRegex(OSError, 'injected'):
                module.install_font_set(root / 'sources', root / 'Fonts', root / 'state',
                                        [('segoeui_system_mod.ttf', 'Segoe UI (TrueType)'),
                                         ('malgun_system_mod.ttf', 'Malgun Gothic (TrueType)')], registry)
            self.assertEqual(registry.values, original)
            self.assertEqual([p.name for p in (root / 'Fonts').iterdir()], ['seguiemj.ttf'])
            self.assertFalse((root / 'state/font_transaction.json').exists())

    def test_restore_reads_persisted_journal(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            registry = Registry()
            original = dict(registry.values)
            module.install_font_set(root / 'sources', root / 'Fonts', root / 'state',
                                    [('segoeui_system_mod.ttf', 'Segoe UI (TrueType)')], registry)
            self.assertEqual(registry.get('Segoe UI (TrueType)')[0], 'segoeui_system_mod.ttf')
            module.restore_font_set(root / 'state', registry, root / 'Fonts')
            self.assertEqual(registry.values, original)
            self.assertEqual(list((root / 'Fonts').iterdir()), [])

    def test_missing_weight_preflight_performs_no_writes(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            registry = Registry()
            original = dict(registry.values)
            with self.assertRaises(ValueError):
                module.install_font_set(root / 'sources', root / 'Fonts', root / 'state',
                                        [('segoeui_system_mod.ttf', 'Segoe UI (TrueType)'),
                                         ('segoeuib_system_mod.ttf', 'Segoe UI Bold (TrueType)')], registry)
            self.assertEqual(registry.values, original)
            self.assertEqual(list((root / 'Fonts').iterdir()), [])

    def test_icons_are_rejected_before_copy(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            with self.assertRaises(ValueError):
                module.install_font_set(root / 'sources', root / 'Fonts', root / 'state',
                                        [('seguiemj.ttf', 'Segoe UI Emoji (TrueType)')], Registry())

    def test_partial_copy_is_removed_without_losing_original_registry(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            registry = Registry()
            original = dict(registry.values)
            real_open = Path.open
            class FailingFile:
                def __init__(self, file): self.file = file
                def __enter__(self): return self
                def __exit__(self, *args): self.file.close()
                def fileno(self): return self.file.fileno()
                def write(self, data):
                    self.file.write(data[:80])
                    self.file.flush()
                    raise OSError('injected disk full')
            def opening(path, mode='r', *args, **kwargs):
                file = real_open(path, mode, *args, **kwargs)
                if mode == 'xb' and path.parent == root / 'Fonts':
                    return FailingFile(file)
                return file
            with patch.object(Path, 'open', opening):
                with self.assertRaisesRegex(OSError, 'disk full'):
                    module.install_font_set(root / 'sources', root / 'Fonts', root / 'state',
                        [('segoeui_system_mod.ttf', 'Segoe UI (TrueType)')], registry)
            self.assertEqual(registry.values, original)
            self.assertEqual(list((root / 'Fonts').iterdir()), [])
            self.assertFalse((root / 'state/font_transaction.json').exists())
