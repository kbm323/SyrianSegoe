"""Journaled legacy installation/rollback. Korean builder never calls this module."""
import hashlib
import json
import os
from pathlib import Path

from fontTools.ttLib import TTFont
from font_targets import ALL_TARGETS

REGISTRY_PATH = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
EXTRA = (
    ('SegUIVar_system_mod.ttf', 'Segoe UI Variable (TrueType)', 'Segoe UI Variable'),
    ('seguili_system_mod.ttf', 'Segoe UI Light Italic (TrueType)', 'Segoe UI'),
    ('seguisli_system_mod.ttf', 'Segoe UI Semilight Italic (TrueType)', 'Segoe UI'),
    ('segoeuii_system_mod.ttf', 'Segoe UI Italic (TrueType)', 'Segoe UI'),
    ('seguisbi_system_mod.ttf', 'Segoe UI Semibold Italic (TrueType)', 'Segoe UI'),
    ('segoeuiz_system_mod.ttf', 'Segoe UI Bold Italic (TrueType)', 'Segoe UI'),
    ('seguibli_system_mod.ttf', 'Segoe UI Black Italic (TrueType)', 'Segoe UI'),
)
ALLOWED = {(t.output_filename, t.registry_name): t.family for t in ALL_TARGETS}
ALLOWED.update({(file, key): family for file, key, family in EXTRA})
JOURNAL = 'font_transaction.json'


class WindowsRegistry:
    def get(self, name):
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY_PATH) as key:
            try:
                return winreg.QueryValueEx(key, name)
            except FileNotFoundError:
                return None

    def set(self, name, value):
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, name, 0, value[1], value[0])

    def delete(self, name):
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, name)
            except FileNotFoundError:
                pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def restore_font_set(state_dir, registry, fonts_dir):
    journal = Path(state_dir) / JOURNAL
    if not journal.exists():
        return False
    data = json.loads(journal.read_text(encoding='utf-8'))
    if Path(data['fonts_dir']).resolve() != Path(fonts_dir).resolve():
        raise ValueError('Rollback Fonts directory does not match the journal')
    entries = data['entries']
    for entry in entries:
        if (entry['file'], entry['key']) not in ALLOWED:
            raise ValueError('Rollback target is not an allowed text font')
        old = entry['old']
        if old is not None and (not isinstance(old[0], str) or old[1] not in (1, 2)):
            raise ValueError('Unsupported original registry value')
    # Restore registry first. Keep the journal if any write fails.
    for entry in entries:
        if entry['old'] is None:
            registry.delete(entry['key'])
        else:
            registry.set(entry['key'], tuple(entry['old']))
    retained = []
    for entry in entries:
        path = Path(fonts_dir) / entry['file']
        if path.exists():
            stat = path.stat()
            owned_partial = (not entry.get('copy_complete', True) and
                             entry.get('created_identity') == [stat.st_dev, stat.st_ino])
            if digest(path) != entry['sha256'] and not owned_partial:
                retained.append(entry['file'])
                continue
            try:
                path.unlink()
            except OSError:
                retained.append(entry['file'])
    if retained:
        raise OSError('Registry restored; restart and retry cleanup: ' + ', '.join(retained))
    journal.unlink()
    return True


def install_font_set(source_dir, fonts_dir, state_dir, entries, registry):
    """Validate the whole set before writing; compensate any partial failure."""
    source_dir, fonts_dir, state_dir = map(Path, (source_dir, fonts_dir, state_dir))
    if not entries or len({key for _, key in entries}) != len(entries):
        raise ValueError('Empty or duplicate font targets')
    if (state_dir / JOURNAL).exists():
        raise ValueError('Restore the previous transaction first')
    records = []
    for file, key in entries:
        family = ALLOWED.get((file, key))
        if not family:
            raise ValueError('Only allowed text fonts may be installed; icons/emoji are protected')
        source = source_dir / file
        if not source.is_file() or (fonts_dir / file).exists():
            raise ValueError('Missing build or existing installed output: ' + file)
        with TTFont(source) as font:
            font.ensureDecompiled()
            names = {r.toUnicode() for r in font['name'].names if r.nameID in (1, 16)}
            if family not in names:
                raise ValueError('Generated font identity mismatch: ' + file)
        old = registry.get(key)
        if old is not None and (not isinstance(old[0], str) or old[1] not in (1, 2)):
            raise ValueError('Cannot safely snapshot original registry value')
        records.append({'file': file, 'key': key, 'old': old, 'sha256': digest(source)})
    state_dir.mkdir(parents=True, exist_ok=True)
    journal = state_dir / JOURNAL
    with journal.open('x', encoding='utf-8') as file:
        json.dump({'fonts_dir': str(fonts_dir.resolve()), 'entries': records}, file, indent=2)
        file.flush()
        import os
        os.fsync(file.fileno())
    def persist():
        temporary = journal.with_suffix('.json.tmp')
        with temporary.open('w', encoding='utf-8') as stream:
            json.dump({'fonts_dir': str(fonts_dir.resolve()), 'entries': records}, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(journal)

    try:
        for entry in records:
            with (fonts_dir / entry['file']).open('xb') as file:
                stat = os.fstat(file.fileno())
                entry['created_identity'] = [stat.st_dev, stat.st_ino]
                entry['copy_complete'] = False
                persist()
                file.write((source_dir / entry['file']).read_bytes())
                file.flush()
                os.fsync(file.fileno())
            entry['copy_complete'] = True
            persist()
            registry.set(entry['key'], (entry['file'], 1))
    except Exception as exc:
        try:
            restore_font_set(state_dir, registry, fonts_dir)
        except Exception as rollback_exc:
            raise RuntimeError(f'Install failed: {exc}; rollback incomplete: {rollback_exc}; journal retained') from exc
        raise
