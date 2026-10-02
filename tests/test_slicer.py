import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fontTools.ttLib import TTFont
from font_fixtures import make_font

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from variable_slicer import slice_variable_font, create_variable_spoof


class SlicerTests(unittest.TestCase):
    def test_spoof_uses_variable_system_identity_without_losing_korean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Fonts').mkdir()
            make_font(root / 'Fonts/SegUIVar.ttf', 'Segoe UI Variable', {0x41})
            make_font(root / 'source.ttf')
            with patch.dict(os.environ, {'WINDIR': tmp}):
                create_variable_spoof(root / 'source.ttf', root / 'spoof.ttf')
            with TTFont(root / 'spoof.ttf') as result:
                self.assertEqual(result['name'].getDebugName(1), 'Segoe UI Variable')
                self.assertIn(0xAC00, result.getBestCmap())

    def test_variable_slice_retains_korean_not_in_segoe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Fonts').mkdir()
            make_font(root / 'Fonts/segoeui.ttf', 'Segoe UI', {0x41})
            make_font(root / 'variable.ttf', variable=True)
            with patch.dict(os.environ, {'WINDIR': tmp}):
                slice_variable_font(root / 'variable.ttf', 350, root / 'slice.ttf')
            with TTFont(root / 'slice.ttf') as result:
                self.assertTrue({0xAC00, 0x3164, 0x6F22, 0x5B57} <= set(result.getBestCmap()))
                self.assertNotIn('fvar', result)
                self.assertEqual(result['OS/2'].usWeightClass, 350)
