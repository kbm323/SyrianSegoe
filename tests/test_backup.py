import importlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


class BackupTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('font_backup'), 'Immutable backup support is missing')
        return importlib.import_module('font_backup')

    def test_original_backup_is_never_overwritten(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Fonts').mkdir()
            (root / 'Fonts/malgun.ttf').write_bytes(b'original')
            module.backup_originals(root / 'Fonts', root / 'backup', ['malgun.ttf'])
            (root / 'Fonts/malgun.ttf').write_bytes(b'updated OS font')
            report = module.backup_originals(root / 'Fonts', root / 'backup', ['malgun.ttf'])
            self.assertEqual((root / 'backup/malgun.ttf').read_bytes(), b'original')
            self.assertEqual(report['changed_sources'], ['malgun.ttf'])

    def test_corrupted_backup_blocks_reuse(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Fonts').mkdir()
            (root / 'Fonts/segoeui.ttf').write_bytes(b'original')
            module.backup_originals(root / 'Fonts', root / 'backup', ['segoeui.ttf'])
            (root / 'backup/segoeui.ttf').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'backup'):
                module.backup_originals(root / 'Fonts', root / 'backup', ['segoeui.ttf'])

    def test_icon_font_is_not_accepted_as_backup_target(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                module.backup_originals(root, root / 'backup', ['seguiemj.ttf'])
