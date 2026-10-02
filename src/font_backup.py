"""Immutable original text-font backups. Does not install or restore system files."""
import hashlib
import json
import os
from pathlib import Path

from font_targets import ALL_TARGETS

LEGACY_EXTRA_FILES = ('SegUIVar.ttf', 'segoeuii.ttf', 'segoeuiz.ttf', 'seguili.ttf',
                      'seguisli.ttf', 'seguisbi.ttf', 'seguibli.ttf')
BACKUP_FILES = tuple(t.filename for t in ALL_TARGETS) + LEGACY_EXTRA_FILES


def persistent_state_dir():
    """Survive PyInstaller one-file extraction and application restarts."""
    return os.path.join(os.path.expanduser("~"), "Documents", "SyrianSegoe", "Original_Segoe_Backups")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def backup_originals(fonts_dir, backup_dir, filenames=BACKUP_FILES):
    if any(name not in BACKUP_FILES for name in filenames):
        raise ValueError('Only known text fonts may be backed up')
    fonts_dir, backup_dir = Path(fonts_dir), Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = backup_dir / 'backup_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    for name, expected in manifest.items():
        if name not in BACKUP_FILES or not (backup_dir / name).is_file() or digest(backup_dir / name) != expected:
            raise ValueError(f'Original backup is missing or corrupt: {name}')
    changed, missing = [], []
    for name in filenames:
        source, target = fonts_dir / name, backup_dir / name
        if not source.exists():
            missing.append(name)
            continue
        if target.exists():
            if digest(source) != digest(target):
                changed.append(name)
        else:
            # Exclusive create; a repeat run cannot overwrite the original.
            with target.open('xb') as file:
                file.write(source.read_bytes())
        manifest[name] = digest(target)
    temporary = manifest_path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    temporary.replace(manifest_path)
    return {'changed_sources': changed, 'missing_sources': missing, 'hashes': manifest}
