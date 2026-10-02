"""Assemble Windows downloads without running executables or installing fonts."""
import argparse
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'kbm323/SyrianSegoe'
GUI = 'SyrianSegoe-Korean.exe'
CLI = ('SyrianSegoe-Korean-Build.exe', 'SyrianSegoe-Korean-Install.exe')
DOCS = ('README.ko.md', 'LICENSE', 'QUICKSTART.ko.txt', 'VERSION.json')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checksums(files):
    return ''.join(f'{digest(data)}  {name}\n' for name, data in sorted(files.items())).encode('utf-8')


def validate_checksums(contents, files):
    expected = {}
    for line in contents.decode('utf-8').splitlines():
        sha, name = line.split('  ', 1)
        if name in expected or not re.fullmatch(r'[0-9a-f]{64}', sha):
            raise ValueError('Invalid SHA-256 manifest')
        expected[name] = sha
    if set(expected) != set(files):
        raise ValueError('SHA-256 manifest does not cover the exact package contents')
    for name, data in files.items():
        if digest(data) != expected[name]:
            raise ValueError(f'SHA-256 mismatch: {name}')


def render(path, version, source_commit):
    text = path.read_text(encoding='utf-8')
    for key, value in {'VERSION': version, 'SOURCE_COMMIT': source_commit, 'REPOSITORY': REPOSITORY}.items():
        text = text.replace('{{' + key + '}}', value)
    return text.encode('utf-8')


def verify(output):
    names = {path.name for path in output.iterdir() if path.is_file()}
    archive_names = names & {'SyrianSegoe-Korean-Windows-x64.zip', 'SyrianSegoe-Korean-GUI-Windows-x64.zip'}
    if len(archive_names) != 1:
        raise ValueError('Expected exactly one Windows ZIP')
    archive_name = archive_names.pop()
    assets = {name: (output / name).read_bytes() for name in (GUI, archive_name)}
    validate_checksums((output / 'SHA256SUMS.txt').read_bytes(), assets)
    with zipfile.ZipFile(output / archive_name) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError('Duplicate ZIP entries')
        metadata = json.loads(archive.read('VERSION.json'))
        edition = metadata['edition']
        if edition not in ('gui', 'full'):
            raise ValueError('Unknown package edition')
        expected_archive = 'SyrianSegoe-Korean-' + ('GUI-' if edition == 'gui' else '') + 'Windows-x64.zip'
        if archive_name != expected_archive:
            raise ValueError('ZIP name does not match its edition')
        expected = {GUI, *DOCS, 'SHA256SUMS.txt'}
        if edition == 'full':
            expected.update(CLI)
        if set(archive.namelist()) != expected:
            raise ValueError('Unexpected or missing ZIP files')
        files = {name: archive.read(name) for name in expected - {'SHA256SUMS.txt'}}
        validate_checksums(archive.read('SHA256SUMS.txt'), files)
        if files[GUI] != assets[GUI]:
            raise ValueError('ZIP GUI differs from the standalone download')
    print(f'PASS: ZIP contents and all SHA-256 hashes ({edition} edition)')


def build(dist, source, output, version, source_commit, gui_only=False):
    if not re.fullmatch(r'v\d+\.\d+\.\d+-ko\.\d+', version) and not (gui_only and version == 'uploaded-preview'):
        raise ValueError('Expected a version such as v0.5.0-ko.1')
    if not re.fullmatch(r'[0-9a-f]{40}', source_commit) and not (gui_only and source_commit == 'unverified'):
        raise ValueError('Expected the exact 40-character source commit')
    if output.exists():
        raise ValueError(f'Output already exists; choose a new directory: {output}')
    files = {GUI: (dist / 'SyrianSegoe.exe').read_bytes()}
    if not gui_only:
        files.update({name: (dist / name).read_bytes() for name in CLI})
    for name, data in files.items():
        if not data.startswith(b'MZ'):
            raise ValueError(f'Expected a Windows executable: {name}')
    files.update({name: (source / name).read_bytes() for name in ('README.ko.md', 'LICENSE')})
    files['QUICKSTART.ko.txt'] = render(ROOT / 'docs/release/QUICKSTART.ko.txt', version, source_commit)
    files['VERSION.json'] = (json.dumps({
        'product': 'SyrianSegoe Korean', 'version': version,
        'edition': 'gui' if gui_only else 'full', 'platform': 'windows-x64',
        'repository': REPOSITORY, 'source_commit': source_commit,
        'fonts_included': False, 'binary_sha256': digest(files[GUI]),
    }, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    files['SHA256SUMS.txt'] = checksums(files)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.release-', dir=output.parent))
    try:
        archive_name = 'SyrianSegoe-Korean-' + ('GUI-' if gui_only else '') + 'Windows-x64.zip'
        with zipfile.ZipFile(staging / archive_name, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(files.items()):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        (staging / GUI).write_bytes(files[GUI])
        assets = {name: (staging / name).read_bytes() for name in (GUI, archive_name)}
        (staging / 'SHA256SUMS.txt').write_bytes(checksums(assets))
        if gui_only:
            notes = (
                f'# SyrianSegoe Korean · GUI 참고용 패키지 ({version})\n\n'
                '기존 EXE를 실행하지 않고 한국어 안내·라이선스·해시와 함께 묶었습니다.\n'
                '빌드 출처와 Windows 실행 동작을 검증한 공식 릴리즈가 아닙니다.\n'
                'ZIP에는 GUI만 포함하며 빌드·설치 CLI는 포함하지 않습니다.\n'
                'VERSION.json과 내부 SHA256SUMS.txt에서 구성과 파일 해시를 확인하세요.\n'
            ).encode('utf-8')
        else:
            notes = render(ROOT / 'docs/release/NOTES.md', version, source_commit)
        (staging / 'RELEASE_NOTES.md').write_bytes(notes)
        verify(staging)
        staging.rename(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    builder = commands.add_parser('build')
    for name in ('dist', 'source', 'output'):
        builder.add_argument('--' + name, type=Path, required=True)
    builder.add_argument('--version', required=True)
    builder.add_argument('--source-commit', required=True)
    builder.add_argument('--gui-only', action='store_true')
    checker = commands.add_parser('verify')
    checker.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'build':
            build(args.dist, args.source, args.output, args.version, args.source_commit, args.gui_only)
        else:
            verify(args.output)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f'Packaging failed: {error}\n')


if __name__ == '__main__':
    main()
