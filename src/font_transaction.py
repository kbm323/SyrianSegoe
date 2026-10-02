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

    write_restore_reg(state_dir / 'Restore.reg', records)
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


def write_restore_reg(path, records):
    """Registry-only recovery, usable even when the GUI cannot start."""
    def quote(value): return '"' + value.replace('\\','\\\\').replace('"','\\"') + '"'
    lines=['Windows Registry Editor Version 5.00','',
           '[HKEY_LOCAL_MACHINE\\'+REGISTRY_PATH+']']
    for entry in records:
        old=entry['old']; key=quote(entry['key'])
        if old is None: lines.append(key+'=-')
        elif old[1]==1: lines.append(key+'='+quote(old[0]))
        else:
            data=(old[0]+'\0').encode('utf-16-le')
            lines.append(key+'=hex(2):'+','.join(f'{byte:02x}' for byte in data))
    temporary=Path(path).with_suffix('.reg.tmp')
    temporary.write_text('\r\n'.join(lines)+'\r\n',encoding='utf-16',newline='')
    temporary.replace(path)


def plan_install(build_dir, fonts_dir):
    """Read-only verification of a complete Korean package and current originals."""
    from korean_builder import inspect_font, metrics, MODERN_HANGUL
    from fontTools.varLib.instancer import instantiateVariableFont
    import tempfile
    build_dir,fonts_dir=Path(build_dir),Path(fonts_dir)
    data=json.loads((build_dir/'validation.json').read_text(encoding='utf-8'))
    if data.get('schema')!=1 or data.get('mode')!='installable' or data.get('apply_supported') is not True:
        raise ValueError('Build an installable package first')
    targets={t.output_filename:(t.filename,t.registry_name,t.family) for t in ALL_TARGETS}
    targets['SegUIVar_system_mod.ttf']=('SegUIVar.ttf','Segoe UI Variable (TrueType)','Segoe UI Variable')
    reports=data['fonts']
    if len(reports)!=len(targets) or {r['file'] for r in reports}!=set(targets):
        raise ValueError('A complete 10-font package is required')
    entries=[]
    for r in reports:
        name=r['file'];original,key,family=targets[name]
        output=build_dir/name;reference=fonts_dir/original
        if r['reference_file']!=original or digest(reference)!=r['reference_sha256']:
            raise ValueError('Original reference hash changed; rebuild: '+original)
        if digest(output)!=r['sha256']:
            raise ValueError('Output hash mismatch: '+name)
        if (fonts_dir/name).exists():raise ValueError('Installed output already exists; restore first')
        with TTFont(output) as font, TTFont(reference) as ref:
            font.ensureDecompiled()
            names={n.toUnicode() for n in font['name'].names if n.nameID in (1,16)}
            if family not in names:raise ValueError('Font family mismatch')
            if metrics(font)!=metrics(ref):raise ValueError('Original line metrics changed')
            for attr in ('usWeightClass','usWidthClass','fsSelection'):
                if getattr(font['OS/2'],attr)!=getattr(ref['OS/2'],attr):
                    raise ValueError('Original style metadata changed')
            if font['head'].macStyle!=ref['head'].macStyle:
                raise ValueError('Original style flags changed')
            name_records=lambda f:{(n.nameID,n.platformID,n.platEncID,n.langID):n.toUnicode() for n in f['name'].names if n.nameID in (1,2,4,6,16,17,21,22)}
            if name_records(font)!=name_records(ref):raise ValueError('Original style names changed')
            cmap=font.getBestCmap() or {}
            if not (MODERN_HANGUL|set(ref.getBestCmap() or {}))<=set(cmap):
                raise ValueError('Required Korean/UI glyphs missing')
            if name=='SegUIVar_system_mod.ttf':
                if 'fvar' not in font or 'gvar' not in font:raise ValueError('Variable tables missing')
                signature=lambda f:[(a.axisTag,a.minValue,a.defaultValue,a.maxValue) for a in f['fvar'].axes]
                if signature(font)!=signature(ref):raise ValueError('Variable axis mismatch')
                instances=lambda f:[(i.coordinates,i.subfamilyNameID,i.postscriptNameID) for i in f['fvar'].instances]
                if instances(font)!=instances(ref):raise ValueError('Variable named instances changed')
                for n in ref['name'].names:
                    if n.nameID>=256 and (font['name'].getName(n.nameID,n.platformID,n.platEncID,n.langID) is None or font['name'].getName(n.nameID,n.platformID,n.platEncID,n.langID).toUnicode()!=n.toUnicode()):
                        raise ValueError('Variable name reference changed')
                if ('STAT' in ref)!=('STAT' in font) or ('STAT' in ref and ref.getTableData('STAT')!=font.getTableData('STAT')):
                    raise ValueError('Variable STAT metadata changed')
                locations=[{a.axisTag:a.defaultValue for a in font['fvar'].axes}]
                for axis in font['fvar'].axes:
                    for value in (axis.minValue,axis.maxValue):
                        location=dict(locations[0]);location[axis.axisTag]=value;locations.append(location)
                with tempfile.TemporaryDirectory(prefix='font-preflight-') as tmp:
                    for location in locations:
                        instance=instantiateVariableFont(font,location,inplace=False)
                        path=Path(tmp)/'instance.ttf';instance.save(path);instance.close()
                        check=inspect_font(path)
                        if check['outline_exceeds_windows_bounds'] or check['outline_exceeds_hhea_bounds']:
                            raise ValueError('Variable outlines exceed line bounds')
            else:
                check=inspect_font(output,reference)
                if check['outline_exceeds_windows_bounds'] or check['outline_exceeds_hhea_bounds']:
                    raise ValueError('Outlines exceed line bounds')
        entries.append((name,key))
    return {'entries':entries,'system_modified':False,'reboot_required':True,
            'excluded':['Segoe Fluent Icons','Segoe MDL2 Assets','Segoe UI Emoji','Segoe UI Symbol']}


def apply_build(build_dir, fonts_dir, state_dir, registry):
    from font_backup import backup_originals
    plan=plan_install(build_dir,fonts_dir)
    if (Path(state_dir)/JOURNAL).exists():raise ValueError('Restore the previous transaction first')
    backup_originals(fonts_dir,state_dir)
    install_font_set(build_dir,fonts_dir,state_dir,plan['entries'],registry)
    return {'installed':len(plan['entries']),'reboot_required':True}


def main():
    import argparse
    import ctypes
    import sys
    from font_backup import persistent_state_dir
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description='Verified Korean font installation and exact rollback')
    parser.add_argument('action',choices=('plan','apply','restore'))
    parser.add_argument('--build',type=Path)
    args=parser.parse_args()
    fonts=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
    state=Path(persistent_state_dir())
    try:
        if args.action in ('plan','apply') and args.build is None:
            raise ValueError('--build is required')
        if args.action!='plan' and (os.name!='nt' or not ctypes.windll.shell32.IsUserAnAdmin()):
            raise PermissionError('Run this command in an Administrator PowerShell')
        if args.action=='plan':result=plan_install(args.build,fonts)
        elif args.action=='apply':
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,REGISTRY_PATH.replace('Fonts','FontSubstitutes')) as key:
                    for family in ('Segoe UI','Segoe UI Variable','Malgun Gothic'):
                        try: winreg.QueryValueEx(key,family)
                        except FileNotFoundError:continue
                        raise ValueError('Existing FontSubstitutes override; restore it first: '+family)
            except FileNotFoundError:pass
            result=apply_build(args.build,fonts,state,WindowsRegistry())
        else:result={'restored':restore_font_set(state,WindowsRegistry(),fonts),'reboot_required':True}
    except Exception as exc:parser.exit(1,str(exc)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
