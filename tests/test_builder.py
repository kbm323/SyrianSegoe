import importlib
import sys
import tempfile
import unittest
import io
from unittest.mock import patch
from pathlib import Path
from fontTools.ttLib import TTFont
from font_fixtures import make_font

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


class BuilderTests(unittest.TestCase):
    def test_cli_prints_report_on_korean_windows_console(self):
        builder = self.builder()
        raw = io.BytesIO()
        console = io.TextIOWrapper(raw, encoding='cp949')
        with patch.object(sys, 'stdout', console), \
             patch.object(sys, 'argv', ['korean_builder.py', '--source', 'input', '--output', 'out']), \
             patch.object(builder, 'build_all', return_value={'text': '₩ 한글 €'}):
            builder.main()
            console.flush()
        self.assertIn('₩ 한글 €', raw.getvalue().decode('utf-8'))
        console.detach()

    def builder(self):
        self.assertIsNotNone(importlib.util.find_spec('korean_builder'), 'Build-only Korean support is missing')
        return importlib.import_module('korean_builder')

    def test_build_preserves_entire_hangul_and_reference_missing_symbols(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'refs').mkdir()
            chars = set(range(0xAC00, 0xD7A4)) | {ord(c) for c in builder.TEST_TEXT}
            make_font(root / 'source.ttf', codepoints=chars, vertical=True)
            make_font(root / 'refs/segoeui.ttf', 'Segoe UI', {0x41, 0xE000})
            builder.build_font(root / 'source.ttf', root / 'refs/segoeui.ttf', root / 'segoeui_system_mod.ttf')
            with TTFont(root / 'segoeui_system_mod.ttf') as result:
                self.assertTrue(set(range(0xAC00, 0xD7A4)) <= set(result.getBestCmap()))
                self.assertIn(0xE000, result.getBestCmap())
                self.assertEqual(result['name'].getDebugName(1), 'Segoe UI')
                self.assertNotIn('fvar', result)

    def test_missing_hangul_fails_before_output(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'refs').mkdir()
            make_font(root / 'source.ttf')
            make_font(root / 'refs/malgun.ttf', 'Malgun Gothic')
            with self.assertRaisesRegex(ValueError, 'Hangul'):
                builder.build_font(root / 'source.ttf', root / 'refs/malgun.ttf', root / 'malgun_system_mod.ttf')
            self.assertFalse((root / 'malgun_system_mod.ttf').exists())

    def test_light_hanja_fallback_uses_regular_malgun(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'refs').mkdir()
            chars = (set(range(0xAC00, 0xD7A4)) | {ord(c) for c in builder.TEST_TEXT}) - {0x6F22, 0x5B57}
            make_font(root / 'source.ttf', codepoints=chars)
            make_font(root / 'refs/segoeuil.ttf', 'Segoe UI', {0x41})
            make_font(root / 'refs/malgunsl.ttf', 'Malgun Gothic', {0x41})
            make_font(root / 'refs/malgun.ttf', 'Malgun Gothic', {0x41, 0x6F22, 0x5B57}, vertical=True)
            builder.build_font(root / 'source.ttf', root / 'refs/segoeuil.ttf', root / 'segoeuil_system_mod.ttf')
            with TTFont(root / 'segoeuil_system_mod.ttf') as font:
                self.assertTrue({0x6F22, 0x5B57} <= set(font.getBestCmap()))

    def test_icons_target_and_original_filename_are_rejected(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_font(root / 'source.ttf')
            make_font(root / 'seguiemj.ttf', 'Segoe UI Emoji')
            with self.assertRaises(ValueError):
                builder.build_font(root / 'source.ttf', root / 'seguiemj.ttf', root / 'seguiemj_system_mod.ttf')
            make_font(root / 'segoeui.ttf', 'Segoe UI')
            original = (root / 'segoeui.ttf').read_bytes()
            with self.assertRaises(ValueError):
                builder.build_font(root / 'source.ttf', root / 'segoeui.ttf', root / 'segoeui.ttf')
            self.assertEqual((root / 'segoeui.ttf').read_bytes(), original)

    def test_wrong_reference_family_is_rejected(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'refs').mkdir()
            make_font(root / 'source.ttf')
            make_font(root / 'refs/malgun.ttf', 'Segoe UI Emoji')
            with self.assertRaisesRegex(ValueError, 'family'):
                builder.build_font(root / 'source.ttf', root / 'refs/malgun.ttf', root / 'malgun_system_mod.ttf')

    def test_batch_preflight_rejects_system_output_directory(self):
        builder = self.builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root.joinpath('Fonts').mkdir()
            with self.assertRaisesRegex(ValueError, 'output'):
                builder.build_all(root / 'input', root / 'Fonts', root / 'Fonts', include_malgun=True)

    def test_single_static_input_is_not_silently_used_for_all_weights(self):
        builder = self.builder()
        from font_targets import ALL_TARGETS
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'refs').mkdir()
            chars = set(range(0xAC00, 0xD7A4)) | {ord(c) for c in builder.TEST_TEXT}
            make_font(root / 'source.ttf', codepoints=chars)
            for target in ALL_TARGETS:
                make_font(root / 'refs' / target.filename, target.family, {0x41})
            with self.assertRaisesRegex(ValueError, 'Variable'):
                builder.build_all(root / 'source.ttf', root / 'refs', root / 'output')
            self.assertFalse((root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
