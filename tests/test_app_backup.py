import ast
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from font_backup import backup_originals


class PackagedStateTests(unittest.TestCase):
    def test_backup_uses_durable_state_instead_of_bundle_extraction(self):
        tree = ast.parse((ROOT / 'src/app.py').read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SyrianSegoeApp')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'run_backup')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Windows/Fonts').mkdir(parents=True)
            (root / 'Windows/Fonts/malgun.ttf').write_bytes(b'original')
            (root / '_MEI').mkdir()
            namespace = {'os': os, '__file__': str(root / '_MEI/app.py'),
                         'backup_originals': backup_originals,
                         'persistent_state_dir': lambda: str(root / 'durable')}
            exec(compile(ast.Module(body=[method], type_ignores=[]), 'app.py', 'exec'), namespace)
            with patch.dict(os.environ, {'WINDIR': str(root / 'Windows')}):
                namespace['run_backup'](types.SimpleNamespace())
            self.assertEqual((root / 'durable/malgun.ttf').read_bytes(), b'original')
            self.assertFalse((root / '_MEI/Original_Segoe_Backups').exists())
