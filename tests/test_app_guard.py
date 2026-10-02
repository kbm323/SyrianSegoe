import ast
import sys
import tempfile
import types
import unittest
from pathlib import Path
from fontTools.ttLib import TTFont
from font_fixtures import make_font

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from glyph_policy import is_hangul


class AppGuardTests(unittest.TestCase):
    def test_korean_font_never_reaches_admin_or_apply_in_legacy_gui(self):
        tree = ast.parse((ROOT / 'src/app.py').read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SyrianSegoeApp')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'build_and_apply')
        messages = []

        def forbidden():
            self.fail('Korean input reached the system apply/elevation path')

        namespace = {'is_admin': forbidden, 'TTFont': TTFont, 'is_hangul': is_hangul,
                     'messagebox': types.SimpleNamespace(showerror=lambda *args, **kwargs: messages.append(args),
                                                         showinfo=lambda *args, **kwargs: messages.append(args))}
        exec(compile(ast.Module(body=[method], type_ignores=[]), 'app.py', 'exec'), namespace)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Pretendard-Regular.ttf'
            make_font(path)
            app = types.SimpleNamespace(latin_reg=str(path))
            namespace['build_and_apply'](app)
        self.assertEqual(len(messages), 1)
