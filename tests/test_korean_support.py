import ast
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
import io
import os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


class Glyph:
    def __init__(self, name, unicode, altuni=None):
        self.glyphname, self.unicode, self.altuni = name, unicode, altuni


class Font:
    def __init__(self, glyphs):
        self.items = glyphs
        self.gsub_lookups = ['hangul_compose']
        self.gpos_lookups = ['kern', 'hangul_position']

    def glyphs(self):
        return iter(self.items)

    def removeGlyph(self, name):
        self.items = [g for g in self.items if g.glyphname != name]

    def removeLookup(self, name):
        for lookups in (self.gsub_lookups, self.gpos_lookups):
            if name in lookups:
                lookups.remove(name)


def load_engine(path):
    # Load definitions without running the upstream build entry point.
    tree = ast.parse(path.read_text(encoding='utf-8'))
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'weights_map' for t in node.targets):
            break
        nodes.append(node)
    namespace = {'__file__': str(path)}
    with patch.dict(sys.modules, {'fontforge': types.ModuleType('fontforge')}):
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


class CleanupTests(unittest.TestCase):
    def test_unprotected_problematic_glyph_is_still_removed(self):
        for path in (ROOT / 'src').glob('*engine*.py'):
            with self.subTest(engine=path.name):
                engine = load_engine(path)
                font = Font([Glyph('uniAC00', 0xAC00), Glyph('uniF8FF', 0xF8FF)])
                engine['cleanup_unused_glyphs'](font)
                self.assertEqual([g.glyphname for g in font.items], ['uniAC00'])
    def test_missing_reference_causes_nonzero_engine_exit(self):
        for path in (ROOT / 'src').glob('*engine*.py'):
            with self.subTest(engine=path.name), tempfile.TemporaryDirectory() as tmp:
                namespace = {'__file__': str(path)}
                with patch.dict(sys.modules, {'fontforge': types.ModuleType('fontforge')}), \
                     patch.dict(os.environ, {'WINDIR': tmp}), \
                     patch.object(sys, 'argv', [str(path)] + ['input.ttf'] * 6 + ['NONE'] * 6), \
                     patch.object(sys, 'stdout', io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), namespace)
                    self.assertEqual(raised.exception.code, 1)

    def test_all_engines_preserve_hangul_even_blacklisted_name_or_alias(self):
        for path in (ROOT / 'src').glob('*engine*.py'):
            with self.subTest(engine=path.name):
                engine = load_engine(path)
                glyphs = [Glyph('uni1100', 0x1100), Glyph('uni11FF', 0x11FF),
                          Glyph('uni3164', 0x3164), Glyph('uniA960', 0xA960),
                          Glyph('uniA97F', 0xA97F), Glyph('uniAC00', 0xAC00),
                          Glyph('uniD7AF', 0xD7AF), Glyph('uniD7B0', 0xD7B0),
                          Glyph('uniD7FF', 0xD7FF), Glyph('uniF8FF', -1, ((0xAC01, -1, 0),))]
                font = Font(glyphs)
                engine['cleanup_unused_glyphs'](font)
                self.assertEqual(len(font.items), 10)
                self.assertEqual(font.gsub_lookups, ['hangul_compose'])

    def test_cjk_fullwidth_and_enclosed_symbols_survive(self):
        for path in (ROOT / 'src').glob('*engine*.py'):
            with self.subTest(engine=path.name):
                engine = load_engine(path)
                font = Font([Glyph(f'uni{cp:04X}', cp) for cp in (0x6F22, 0x5B57, 0xFF08, 0x3231, 0x2460)])
                engine['cleanup_unused_glyphs'](font)
                self.assertEqual(len(font.items), 5)


if __name__ == '__main__':
    unittest.main()
