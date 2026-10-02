"""Exercise the real release CLI using temporary build artifacts."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'package_release.py'


class ReleasePackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dist = self.root / 'dist'
        self.source = self.root / 'source'
        self.dist.mkdir()
        self.source.mkdir()
        for name in ('SyrianSegoe', 'SyrianSegoe-Korean-Build', 'SyrianSegoe-Korean-Install'):
            (self.dist / f'{name}.exe').write_bytes(b'MZ' + name.encode())
        (self.source / 'README.ko.md').write_text('한국어 사용법', encoding='utf-8')
        (self.source / 'LICENSE').write_text('MIT license', encoding='utf-8')

    def package(self, output='release', extra=()):
        return subprocess.run([
            sys.executable, str(SCRIPT), 'build', '--dist', str(self.dist),
            '--source', str(self.source), '--output', str(self.root / output),
            '--version', 'v0.5.0-ko.1', '--source-commit', 'a' * 40, *extra,
        ], capture_output=True, text=True)

    def test_full_bundle_contains_executables_docs_and_verifiable_hashes(self):
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        release = self.root / 'release'
        for line in (release / 'SHA256SUMS.txt').read_text().splitlines():
            expected, name = line.split('  ', 1)
            self.assertEqual(hashlib.sha256((release / name).read_bytes()).hexdigest(), expected)
        with zipfile.ZipFile(release / 'SyrianSegoe-Korean-Windows-x64.zip') as archive:
            self.assertEqual(set(archive.namelist()), {
                'SyrianSegoe-Korean.exe', 'SyrianSegoe-Korean-Build.exe',
                'SyrianSegoe-Korean-Install.exe', 'README.ko.md', 'LICENSE',
                'QUICKSTART.ko.txt', 'VERSION.json', 'SHA256SUMS.txt',
            })
            metadata = json.loads(archive.read('VERSION.json'))
            self.assertEqual(metadata['version'], 'v0.5.0-ko.1')
            self.assertEqual(metadata['source_commit'], 'a' * 40)
            for line in archive.read('SHA256SUMS.txt').decode().splitlines():
                expected, name = line.split('  ', 1)
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), expected)

    def test_missing_cli_cannot_produce_full_bundle(self):
        (self.dist / 'SyrianSegoe-Korean-Install.exe').unlink()
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SyrianSegoe-Korean-Install.exe', result.stderr)
        self.assertFalse((self.root / 'release').exists())

    def test_gui_only_bundle_is_identified_and_keeps_uploaded_binary(self):
        (self.dist / 'SyrianSegoe-Korean-Build.exe').unlink()
        (self.dist / 'SyrianSegoe-Korean-Install.exe').unlink()
        result = self.package(extra=('--gui-only',))
        self.assertEqual(result.returncode, 0, result.stderr)
        notes = (self.root / 'release' / 'RELEASE_NOTES.md').read_text(encoding='utf-8')
        self.assertIn('참고용', notes)
        self.assertNotIn('/releases/download/', notes)
        with zipfile.ZipFile(self.root / 'release' / 'SyrianSegoe-Korean-GUI-Windows-x64.zip') as archive:
            self.assertEqual(archive.read('SyrianSegoe-Korean.exe'), (self.dist / 'SyrianSegoe.exe').read_bytes())
            self.assertFalse(any('-Build.exe' in name or '-Install.exe' in name for name in archive.namelist()))
            self.assertEqual(json.loads(archive.read('VERSION.json'))['edition'], 'gui')

    def test_unrelated_fonts_and_files_are_never_bundled(self):
        (self.dist / 'private.ttf').write_bytes(b'font')
        (self.source / 'secret.txt').write_text('not for distribution')
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(self.root / 'release' / 'SyrianSegoe-Korean-Windows-x64.zip') as archive:
            self.assertNotIn('private.ttf', archive.namelist())
            self.assertNotIn('secret.txt', archive.namelist())

    def test_repeat_builds_match_and_existing_output_is_preserved(self):
        first = self.package()
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.package('second')
        self.assertEqual(second.returncode, 0, second.stderr)
        for name in ('SHA256SUMS.txt', 'SyrianSegoe-Korean-Windows-x64.zip'):
            self.assertEqual((self.root / 'release' / name).read_bytes(), (self.root / 'second' / name).read_bytes())
        before = (self.root / 'release' / 'SHA256SUMS.txt').read_bytes()
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.root / 'release' / 'SHA256SUMS.txt').read_bytes(), before)

    def test_verifier_rejects_tampered_download(self):
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        release = self.root / 'release'
        command = [sys.executable, str(SCRIPT), 'verify', str(release)]
        verified = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(verified.returncode, 0, verified.stderr)
        (release / 'SyrianSegoe-Korean.exe').write_bytes(b'changed')
        verified = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(verified.returncode, 0)
        self.assertIn('SHA-256', verified.stderr)


if __name__ == '__main__':
    unittest.main()
