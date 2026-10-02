import sys
import tempfile
import unittest
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from font_fixtures import make_font
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import korean_builder as builder

class InstallableTests(unittest.TestCase):
    def test_clipping_policy_fits_outlines_without_losing_cmap_or_changing_line_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'font.ttf'
            make_font(path)
            with TTFont(path) as font:
                cmap = dict(font.getBestCmap())
                font['glyf']['text'].yMax = 700
                old_metrics = builder.metrics(font)
                self.assertTrue(hasattr(builder, 'fit_outlines'), 'Outline fitting is missing')
                changed = builder.fit_outlines(font, 600, -80)
                self.assertGreater(changed, 0)
                font.save(path)
            with TTFont(path) as font:
                glyph = font['glyf']['text']; glyph.recalcBounds(font['glyf'])
                self.assertLessEqual(glyph.yMax, 600)
                self.assertGreaterEqual(glyph.yMin, -80)
                self.assertEqual(font.getBestCmap(), cmap)
                self.assertEqual(builder.metrics(font), old_metrics)

    def test_variable_replacement_keeps_reference_axes_and_instances_and_hangul(self):
        self.assertTrue(hasattr(builder, 'build_variable_font'), 'Real variable replacement is missing')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'refs').mkdir()
            chars = set(builder.MODERN_HANGUL) | {ord(c) for c in builder.TEST_TEXT}
            make_font(root / 'source.ttf', 'Pretendard Variable', chars, variable=True)
            from fontTools.ttLib.tables.TupleVariation import TupleVariation
            with TTFont(root / 'source.ttf') as source:
                from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
                addOpenTypeFeaturesFromString(source, 'conditionset Heavy { wght 600 900; } Heavy; variation rvrn Heavy { sub text by .notdef; } rvrn;')
                source['gvar'].variations['text'] = [TupleVariation({'wght':(0,1,1)}, [(0,0),(100,0),(100,0),(0,0),(0,0),(100,0),(0,0),(0,0)])]
                source.save(root / 'source.ttf')
            make_font(root / 'refs/SegUIVar.ttf', 'Segoe UI Variable', {0x41,0xE000}, variable=True)
            output = root / 'SegUIVar_system_mod.ttf'
            report = builder.build_variable_font(root / 'source.ttf', root / 'refs/SegUIVar.ttf', output)
            with TTFont(output) as font, TTFont(root / 'refs/SegUIVar.ttf') as reference:
                self.assertEqual([(a.axisTag,a.minValue,a.defaultValue,a.maxValue) for a in font['fvar'].axes],
                                 [(a.axisTag,a.minValue,a.defaultValue,a.maxValue) for a in reference['fvar'].axes])
                self.assertEqual(font['name'].getDebugName(1), 'Segoe UI Variable')
                advances=[]
                for weight in (300,400,700):
                    instance = instantiateVariableFont(font, {'wght':weight}, inplace=False)
                    self.assertTrue(set(builder.MODERN_HANGUL) <= set(instance.getBestCmap()))
                    self.assertIn(0xE000, instance.getBestCmap())
                    advances.append(instance['hmtx'][instance.getBestCmap()[0xAC00]][0])
                    instance.close()
                self.assertLess(advances[0], advances[-1])
            self.assertFalse(report['outline_exceeds_windows_bounds'])

    def test_installable_bundle_requires_variable_input_before_any_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); make_font(root/'source.ttf')
            self.assertIn('installable', __import__('inspect').signature(builder.build_all).parameters,
                          'Installable package mode is missing')
            with self.assertRaisesRegex(ValueError,'Variable'):
                builder.build_all(root/'source.ttf',root/'refs',root/'output',installable=True)
            self.assertFalse((root/'output').exists())
