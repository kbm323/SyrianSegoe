import json
import sys
import tempfile
import unittest
from pathlib import Path
from font_fixtures import make_font
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import font_transaction as transaction
from font_targets import ALL_TARGETS
from korean_builder import MODERN_HANGUL, TEST_TEXT, sha256
from test_rollback import Registry

class InstallPlanTests(unittest.TestCase):
    def fixture(self,root):
        build=root/'build'; fonts=root/'Fonts'; build.mkdir();fonts.mkdir()
        chars=set(MODERN_HANGUL)|{ord(c) for c in TEST_TEXT}
        entries=[]
        targets=[(t.filename,t.output_filename,t.family) for t in ALL_TARGETS]+[('SegUIVar.ttf','SegUIVar_system_mod.ttf','Segoe UI Variable')]
        for original,output,family in targets:
            make_font(fonts/original,family,chars,variable=original=='SegUIVar.ttf')
            make_font(build/output,family,chars,variable=original=='SegUIVar.ttf')
            entries.append({'file':output,'sha256':sha256(build/output),'reference_file':original,
                            'reference_sha256':sha256(fonts/original)})
        (build/'validation.json').write_text(json.dumps({'schema':1,'mode':'installable','apply_supported':True,'fonts':entries}))
        return build,fonts

    def test_plan_is_read_only_and_rejects_tampered_output(self):
        self.assertTrue(hasattr(transaction,'plan_install'),'Installation preflight is missing')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build,fonts=self.fixture(root)
            plan=transaction.plan_install(build,fonts)
            self.assertEqual(len(plan['entries']),10)
            self.assertEqual(len(list(fonts.iterdir())),10)
            (build/'malgun_system_mod.ttf').write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'hash'):
                transaction.plan_install(build,fonts)

    def test_apply_reuses_transaction_and_persists_registry_restore_file(self):
        self.assertTrue(hasattr(transaction,'apply_build'),'Verified bundle application is missing')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build,fonts=self.fixture(root);registry=Registry()
            original=dict(registry.values)
            transaction.apply_build(build,fonts,root/'state',registry)
            self.assertEqual(registry.get('Malgun Gothic (TrueType)')[0],'malgun_system_mod.ttf')
            self.assertEqual((root/'state/Restore.reg').read_text(encoding='utf-16').splitlines()[0],
                             'Windows Registry Editor Version 5.00')
            transaction.restore_font_set(root/'state',registry,fonts)
            self.assertEqual(registry.values,original)
            self.assertEqual(len(list(fonts.iterdir())),10)

    def test_missing_variable_refuses_before_install(self):
        self.assertTrue(hasattr(transaction,'plan_install'),'Installation preflight is missing')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build,fonts=self.fixture(root)
            data=json.loads((build/'validation.json').read_text());data['fonts'].pop()
            (build/'validation.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'complete'):
                transaction.plan_install(build,fonts)

    def test_wrong_weight_is_rejected_even_with_updated_manifest_hash(self):
        from fontTools.ttLib import TTFont
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build,fonts=self.fixture(root)
            path=build/'malgun_system_mod.ttf'
            with TTFont(path) as font:
                font['OS/2'].usWeightClass=900; font.save(path)
            data=json.loads((build/'validation.json').read_text())
            next(r for r in data['fonts'] if r['file']==path.name)['sha256']=sha256(path)
            (build/'validation.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'style'):
                transaction.plan_install(build,fonts)
