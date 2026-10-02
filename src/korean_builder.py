"""Build-only Pretendard text fonts. No registry, install, elevation or GUI calls."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import sys

from fontTools import subset
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
from fontTools.varLib import build as build_variations
from fontTools.merge import Merger
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.scaleUpem import scale_upem
from fontTools.varLib.instancer import instantiateVariableFont

from font_targets import SEGOE_TARGETS, MALGUN_TARGETS, TARGET_BY_FILENAME
from glyph_policy import HANGUL_RANGES, KOREAN_TEXT_CODEPOINTS

TEST_TEXT = ('가나다라마바사아자차카타파하한글 Windows 시스템 글꼴 테스트'
             'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
             '₩ $ € ¥→ ← ↑ ↓㈜ ① ② ③漢字')
MODERN_HANGUL = frozenset(range(0xAC00, 0xD7A4))
NAME_IDS = {1, 2, 4, 6, 16, 17, 21, 22}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def font_families(font):
    return {r.toUnicode() for r in font['name'].names if r.nameID in (1, 16)}


def check_source(font):
    families = font_families(font)
    if not families & {'Pretendard', 'Pretendard Variable'} or any('JP' in n for n in families):
        raise ValueError('Use the ordinary Pretendard family, not Pretendard JP')
    if 'glyf' not in font:
        raise ValueError('Use official static/alternative TTF or PretendardVariable.ttf; OTF/CFF is unsupported')
    missing = MODERN_HANGUL - set(font.getBestCmap() or {})
    if missing:
        raise ValueError(f'Hangul syllables missing in source: {len(missing)}')


def metrics(font):
    os2, hhea = font['OS/2'], font['hhea']
    return {'em': font['head'].unitsPerEm, 'ascent': hhea.ascent, 'descent': hhea.descent,
            'line_gap': hhea.lineGap, 'typo_ascent': os2.sTypoAscender,
            'typo_descent': os2.sTypoDescender, 'typo_line_gap': os2.sTypoLineGap,
            'win_ascent': os2.usWinAscent, 'win_descent': os2.usWinDescent}


def inspect_font(path, reference_path=None, source_codepoints=None):
    """Decompile every table, check cmap/glyph data, and report clipping bounds."""
    with TTFont(path, checkChecksums=2) as font:
        font.ensureDecompiled()
        for tag in font.keys():
            if tag != 'GlyphOrder':
                font.getTableData(tag)
        cmap = font.getBestCmap() or {}
        missing = MODERN_HANGUL - set(cmap)
        missing_test = {ord(c) for c in TEST_TEXT} - set(cmap)
        if missing or missing_test:
            raise ValueError(f'Hangul/test glyphs missing: {len(missing)}, {sorted(missing_test)}')
        if source_codepoints is not None and not set(source_codepoints) <= set(cmap):
            raise ValueError('Source cmap coverage was lost during generation')
        glyph_order = set(font.getGlyphOrder())
        if any(name not in glyph_order or name == '.notdef' for name in cmap.values()):
            raise ValueError('Invalid cmap glyph reference')
        if 'fvar' in font:
            raise ValueError('Expected a static replacement')
        bounds = []
        boxes = {}
        for name in set(cmap.values()):
            glyph = font['glyf'][name]
            glyph.recalcBounds(font['glyf'])
            if hasattr(glyph, 'yMax'):
                bounds.append((glyph.yMin, glyph.yMax))
                boxes[name] = {'x_min': glyph.xMin, 'x_max': glyph.xMax,
                               'y_min': glyph.yMin, 'y_max': glyph.yMax}
        ymin = min((b[0] for b in bounds), default=0)
        ymax = max((b[1] for b in bounds), default=0)
        result = {'file': Path(path).name, 'sha256': sha256(path),
                  'glyph_count': len(font.getGlyphOrder()), 'cmap_count': len(cmap),
                  'hangul_syllables': len(MODERN_HANGUL & set(cmap)),
                  'hangul_blocks': {f'U+{a:04X}-U+{b:04X}': sum(a <= cp <= b for cp in cmap)
                                    for a, b in HANGUL_RANGES},
                  'family': sorted(font_families(font)), 'weight': font['OS/2'].usWeightClass,
                  'metrics': metrics(font), 'bounds': {'y_min': ymin, 'y_max': ymax},
                  'test_text': TEST_TEXT, 'tables': sorted(font.keys()),
                  'requires_visual_validation': True}
        samples = {c: boxes.get(cmap[ord(c)], {}) for c in 'Ha0가한글漢'}
        text_boxes = [boxes[cmap[ord(c)]] for c in TEST_TEXT if cmap[ord(c)] in boxes]
        result['sample_bounds'] = samples
        result['test_text_bounds'] = {'y_min': min(b['y_min'] for b in text_boxes),
                                      'y_max': max(b['y_max'] for b in text_boxes)}
        if reference_path:
            with TTFont(reference_path) as reference:
                if not set(reference.getBestCmap() or {}) <= set(cmap):
                    raise ValueError('Reference UI glyph coverage was lost')
                if metrics(reference) != metrics(font):
                    raise ValueError('Reference metrics changed')
                result['reference_metrics'] = metrics(reference)
        m = result['metrics']
        result['outline_exceeds_windows_bounds'] = ymax > m['win_ascent'] or ymin < -m['win_descent']
        result['outline_exceeds_hhea_bounds'] = ymax > m['ascent'] or ymin < m['descent']
        tb = result['test_text_bounds']
        result['test_text_exceeds_windows_bounds'] = tb['y_max'] > m['win_ascent'] or tb['y_min'] < -m['win_descent']
        return result


def guard_output(output, references):
    output = Path(output).resolve()
    roots = [Path(references).resolve(), Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts']
    for root in roots:
        root = root.resolve()
        if output == root or root in output.parents:
            raise ValueError('The output must be outside system/reference Fonts directories')


def supply_vertical_metrics(font, template):
    if 'vhea' in font:
        return
    font['vhea'] = copy.deepcopy(template['vhea'])
    font['vmtx'] = newTable('vmtx')
    font['vmtx'].metrics = {}
    for name in font.getGlyphOrder():
        glyph = font['glyf'][name]
        glyph.recalcBounds(font['glyf'])
        top = font['hhea'].ascent - getattr(glyph, 'yMax', 0)
        font['vmtx'].metrics[name] = (font['head'].unitsPerEm, top)


def build_font(source_path, reference_path, output_path, weight=None, fit_bounds=False):
    source_path, reference_path, output_path = map(Path, (source_path, reference_path, output_path))
    target = TARGET_BY_FILENAME.get(reference_path.name.lower())
    if not target or output_path.name != target.output_filename:
        raise ValueError('Unsupported text target or output filename; icons/emoji are protected')
    guard_output(output_path, reference_path.parent)
    if output_path.exists():
        raise ValueError('Refusing to overwrite an existing output')
    with TTFont(source_path) as source, TTFont(reference_path) as reference:
        if target.family not in font_families(reference):
            raise ValueError('Unexpected reference family')
        check_source(source)
        if 'fvar' in source:
            axes = {axis.axisTag: axis for axis in source['fvar'].axes}
            w = target.weight if weight is None else weight
            if 'wght' not in axes or not axes['wght'].minValue <= w <= axes['wght'].maxValue:
                raise ValueError('Requested weight is outside variable font axis')
            limits = {tag: (w if tag == 'wght' else axis.defaultValue) for tag, axis in axes.items()}
            built = instantiateVariableFont(source, limits, inplace=False)
        else:
            built = copy.deepcopy(source)
        try:
            original_cmap = set(built.getBestCmap())
            scale_upem(built, reference['head'].unitsPerEm)
            fallback = set(reference.getBestCmap() or {}) - original_cmap
            donors = [(reference, fallback)]
            korean_donor = None
            # Ordinary Pretendard omits Hanja. Segoe UI is not a Hanja donor;
            # use the installed Malgun text font, never an icon/emoji font.
            if target.family == 'Segoe UI' or target.filename == 'malgunsl.ttf':
                korean_filename = 'malgunbd.ttf' if target.weight >= 600 else 'malgun.ttf'
                korean_path = reference_path.parent / korean_filename
                if korean_path.exists():
                    korean_donor = TTFont(korean_path)
                    if 'Malgun Gothic' not in font_families(korean_donor):
                        korean_donor.close()
                        raise ValueError('Unexpected Korean fallback family')
                    extra = (set(korean_donor.getBestCmap() or {}) &
                             (KOREAN_TEXT_CODEPOINTS | {ord(c) for c in TEST_TEXT})) - original_cmap - fallback
                    donors.append((korean_donor, extra))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='korean-font-', dir=output_path.parent) as tmp:
                if any(points for _, points in donors):
                    if 'vhea' not in built:
                        for donor, points in donors:
                            if points and 'vhea' in donor:
                                supply_vertical_metrics(built, donor)
                                break
                    for tag in ('DSIG', 'STAT'):
                        if tag in built:
                            del built[tag]
                    first = Path(tmp) / 'source.ttf'
                    built.save(first)
                    merge_paths = [str(first)]
                    for index, (donor, points) in enumerate(donors):
                        if not points:
                            continue
                        reference_subset = copy.deepcopy(donor)
                        options = subset.Options()
                        options.name_IDs = ['*']
                        options.name_legacy = True
                        options.name_languages = ['*']
                        sub = subset.Subsetter(options)
                        sub.populate(unicodes=points)
                        sub.subset(reference_subset)
                        scale_upem(reference_subset, reference['head'].unitsPerEm)
                        # Missing vertical tables must be supplied before merge.
                        if 'vhea' in built and 'vhea' not in reference_subset:
                            supply_vertical_metrics(reference_subset, built)
                        for tag in ('DSIG', 'STAT'):
                            if tag in reference_subset:
                                del reference_subset[tag]
                        second = Path(tmp) / f'fallback-{index}.ttf'
                        reference_subset.save(second)
                        reference_subset.close()
                        merge_paths.append(str(second))
                    merged = Merger().merge(merge_paths)
                    built.close()
                    built = merged
                # Text identity only. Retain Pretendard copyright/license records.
                built['name'].names = [r for r in built['name'].names if r.nameID not in NAME_IDS | {3}]
                built['name'].names.extend(copy.deepcopy(r) for r in reference['name'].names if r.nameID in NAME_IDS)
                built['name'].setName('SyrianSegoe-Korean-' + sha256(source_path)[:12] + '-' + target.filename,
                                      3, 3, 1, 0x409)
                for name in ('ascent', 'descent', 'lineGap'):
                    setattr(built['hhea'], name, getattr(reference['hhea'], name))
                for name in ('sTypoAscender', 'sTypoDescender', 'sTypoLineGap', 'usWinAscent',
                             'usWinDescent', 'usWeightClass', 'usWidthClass', 'fsSelection'):
                    setattr(built['OS/2'], name, getattr(reference['OS/2'], name))
                built['head'].macStyle = reference['head'].macStyle
                built['OS/2'].recalcUnicodeRanges(built)
                built['OS/2'].recalcCodePageRanges(built)
                if 'DSIG' in built:
                    del built['DSIG']
                line_top = min(reference['hhea'].ascent, reference['OS/2'].usWinAscent)
                line_bottom = max(reference['hhea'].descent, -reference['OS/2'].usWinDescent)
                fitted = fit_outlines(built, line_top, line_bottom) if fit_bounds else 0
                candidate = Path(tmp) / target.output_filename
                built.save(candidate)
                report = inspect_font(candidate, reference_path, original_cmap)
                candidate.replace(output_path)
            report.update(source_sha256=sha256(source_path), reference_sha256=sha256(reference_path),
                          reference_file=target.filename, source_weight=weight or target.weight,
                          fallback_codepoints=len(fallback), fitted_glyphs=fitted,
                          rollback='Original files are read-only; no system changes were made')
            if korean_donor:
                report['korean_fallback'] = {'reference_file': korean_path.name,
                                             'sha256': sha256(korean_path), 'codepoints': len(extra)}
                korean_donor.close()
            return report
        finally:
            if 'korean_donor' in locals() and korean_donor:
                korean_donor.close()
            built.close()


def build_all(source, references, output, include_malgun=True, installable=False):
    source, references, output = map(Path, (source, references, output))
    guard_output(output, references)
    if output.exists():
        raise ValueError('Choose a new output directory; existing builds are never overwritten')
    if installable and (not source.is_file() or not include_malgun):
        raise ValueError('Installable mode requires Pretendard Variable and Malgun targets')
    if source.is_file():
        with TTFont(source) as input_font:
            if 'fvar' not in input_font:
                raise ValueError('A single file must be Pretendard Variable; use a directory for Static weights')
    targets = SEGOE_TARGETS + (MALGUN_TARGETS if include_malgun else ())
    for target in targets:
        if not (references / target.filename).is_file():
            raise ValueError(f'Missing original reference: {target.filename}')
    if installable and not (references / 'SegUIVar.ttf').is_file():
        raise ValueError('Missing original SegUIVar.ttf')
    paths = {}
    for target in targets:
        path = source if source.is_file() else source / f'Pretendard-{target.static_style}.ttf'
        if not path.is_file():
            raise ValueError(f'Missing Pretendard TTF: {path.name}')
        paths[target.filename] = path
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.korean-build-', dir=output.parent))
    try:
        reports = [build_font(paths[t.filename], references / t.filename,
                              staging / t.output_filename, t.weight, fit_bounds=installable) for t in targets]
        if installable:
            reports.append(build_variable_font(source, references / 'SegUIVar.ttf', staging / 'SegUIVar_system_mod.ttf'))
        report = {'mode': 'build-only', 'system_modified': False, 'fonts': reports,
                  'excluded': ['Segoe Fluent Icons', 'Segoe MDL2 Assets', 'Segoe UI Emoji',
                               'Segoe UI Symbol', 'Segoe UI Variable'],
                  'static_mapping': {'Segoe UI Semilight': 'Pretendard Light (300); target metadata 350'},
                  'apply_supported': installable, 'schema': 1}
        if installable:
            report['excluded'].remove('Segoe UI Variable')
            report['mode'] = 'installable'
            report['optical_size_behavior'] = 'accepted; Pretendard outlines invariant'
        (staging / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        staging.rename(output)
        return report
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def fit_outlines(font, ascent, descent, scales=None, flatten=False):
    """Fit exceptional outlines to the existing line box; keep advance widths.

    No global shrink: ordinary Hangul is left untouched. Remove hint programs
    so stale instructions cannot move the adjusted outlines outside the box.
    """
    glyph_set = font.getGlyphSet()
    recordings = {}
    factors = {}
    for name in font.getGlyphOrder():
        glyph = font['glyf'][name]
        glyph.recalcBounds(font['glyf'])
        factor = 1.0
        if hasattr(glyph, 'yMax'):
            if glyph.yMax > ascent: factor = min(factor, (ascent - 2) / glyph.yMax)
            if glyph.yMin < descent: factor = min(factor, (descent + 2) / glyph.yMin)
        if scales is not None: factor = min(factor, scales.get(name, 1.0))
        factors[name] = factor
        if factor < 1 or flatten:
            recording = DecomposingRecordingPen(glyph_set)
            glyph_set[name].draw(recording)
            recordings[name] = recording
    for name, recording in recordings.items():
        pen = TTGlyphPen(None)
        recording.replay(TransformPen(pen, (1, 0, 0, factors[name], 0, 0)))
        font['glyf'][name] = pen.glyph()
    for glyph in font['glyf'].glyphs.values():
        if hasattr(glyph, 'program'): glyph.program.fromBytecode([])
    for tag in ('fpgm', 'prep', 'cvt ', 'hdmx', 'LTSH', 'VDMX'):
        if tag in font: del font[tag]
    font['maxp'].maxSizeOfInstructions = 0
    return sum(f < 1 for f in factors.values())


def build_variable_font(source_path, reference_path, output_path):
    """Real weight-variable replacement with reference UI names/opsz coordinates.

    Pretendard has no optical-size outlines: opsz is accepted, with invariant
    Pretendard outlines. This is explicit compatibility, not Segoe optical design.
    """
    source_path, reference_path, output_path = map(Path, (source_path, reference_path, output_path))
    guard_output(output_path, reference_path.parent)
    if reference_path.name.lower() != 'seguivar.ttf' or output_path.name != 'SegUIVar_system_mod.ttf':
        raise ValueError('Variable replacement requires the SegUIVar text target')
    if output_path.exists(): raise ValueError('Existing variable output')
    with TTFont(source_path) as source, TTFont(reference_path) as reference:
        check_source(source)
        if 'fvar' not in source or 'fvar' not in reference:
            raise ValueError('Variable replacement requires Pretendard Variable and original SegUIVar')
        if 'Segoe UI Variable' not in font_families(reference):
            raise ValueError('Unexpected variable reference family')
        ref_axes = {a.axisTag:a for a in reference['fvar'].axes}
        if set(ref_axes) - {'wght','opsz'} or 'wght' not in ref_axes:
            raise ValueError('Unsupported SegUIVar axes')
        weight = ref_axes['wght']
        weights = sorted({weight.minValue,weight.defaultValue,weight.maxValue} |
                         {w for w in (300,350,600,700) if weight.minValue <= w <= weight.maxValue})
        source_weights = next(a for a in source['fvar'].axes if a.axisTag == 'wght')
        if source_weights.minValue > min(weights) or source_weights.maxValue < max(weights):
            raise ValueError('Pretendard weight range does not cover SegUIVar')
        output_path.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='korean-variable-',dir=output_path.parent) as tmp:
            tmp = Path(tmp); (tmp/'refs').mkdir()
            donor_reference = copy.deepcopy(reference)
            # Default-only fallback: avoid dangling device variation indices in
            # Windows 25H2 SegUIVar GPOS. Pretendard layout tables stay intact.
            if 'GPOS' in donor_reference: del donor_reference['GPOS']
            fixed_reference = instantiateVariableFont(donor_reference,
                {a.axisTag:a.defaultValue for a in reference['fvar'].axes}, inplace=False)
            fixed_reference['name'].setName('Segoe UI',1,3,1,0x409)
            fixed_reference['name'].setName('Segoe UI',16,3,1,0x409)
            fixed_reference.save(tmp/'refs/segoeui.ttf'); fixed_reference.close(); donor_reference.close()
            # Stable fallback donor, glyph order and topology across every master.
            for n in ('malgun.ttf','malgunbd.ttf'):
                donor=reference_path.parent/n
                if donor.exists(): shutil.copyfile(donor,tmp/'refs'/n)
            masters=[]
            for w in weights:
                master_dir=tmp/str(w); master_dir.mkdir()
                path=master_dir/'segoeui_system_mod.ttf'
                build_font(source_path,tmp/'refs/segoeui.ttf',path,w)
                masters.append((w,path))
            fonts=[TTFont(path) for _,path in masters]
            try:
                order=fonts[0].getGlyphOrder()
                if any(f.getGlyphOrder()!=order for f in fonts):
                    raise ValueError('Variable master glyph orders differ')
                m=metrics(reference); top=min(m['ascent'],m['win_ascent']); bottom=max(m['descent'],-m['win_descent'])
                scales={}
                for f in fonts:
                    for name in order:
                        g=f['glyf'][name];g.recalcBounds(f['glyf']);factor=1.0
                        if hasattr(g,'yMax'):
                            if g.yMax>top:factor=min(factor,(top-2)/g.yMax)
                            if g.yMin<bottom:factor=min(factor,(bottom+2)/g.yMin)
                        scales[name]=min(scales.get(name,1.0),factor)
                # ponytail: fixed default shaping; use compatible variable OTL
                # reconstruction only if weight-dependent feature selection is needed.
                default_font = fonts[weights.index(weight.defaultValue)]
                layout = {tag:copy.deepcopy(default_font[tag]) for tag in ('GSUB','GPOS','GDEF') if tag in default_font}
                for (w,path),f in zip(masters,fonts):
                    for tag in ('GSUB','GPOS','GDEF'):
                        if tag in layout: f[tag]=copy.deepcopy(layout[tag])
                        elif tag in f: del f[tag]
                    fit_outlines(f,top,bottom,scales=scales,flatten=True)
                    f['OS/2'].usWeightClass=round(w);f.save(path)
            finally:
                for f in fonts:f.close()
            ds=DesignSpaceDocument()
            for a in reference['fvar'].axes:
                desc=AxisDescriptor();desc.name=a.axisTag;desc.tag=a.axisTag
                desc.minimum=a.minValue;desc.default=a.defaultValue;desc.maximum=a.maxValue
                ds.addAxis(desc)
            for w,path in masters:
                desc=SourceDescriptor();desc.path=str(path);desc.name=str(w)
                desc.location={a.axisTag:(w if a.axisTag=='wght' else a.defaultValue) for a in reference['fvar'].axes}
                if w==weight.defaultValue:desc.copyInfo=desc.copyLib=desc.copyFeatures=True
                ds.addSource(desc)
            variable,_,_=build_variations(ds)
            try:
                variable['fvar']=copy.deepcopy(reference['fvar'])
                if 'STAT' in reference:variable['STAT']=copy.deepcopy(reference['STAT'])
                # Keep varLib's weight normalization (identity), not Segoe's avar.
                variable['name'].names=[r for r in variable['name'].names if r.nameID not in NAME_IDS|{3} and r.nameID<256]
                variable['name'].names.extend(copy.deepcopy(r) for r in reference['name'].names if r.nameID in NAME_IDS or r.nameID>=256)
                variable['name'].setName('SyrianSegoe-Korean-Variable-'+sha256(source_path)[:12],3,3,1,0x409)
                candidate=tmp/'SegUIVar_system_mod.ttf';variable.save(candidate)
                samples=[]
                validation_weights = sorted(set(weights) | {w for w in (325,375,500,650) if weight.minValue <= w <= weight.maxValue})
                for w in validation_weights:
                    coords={a.axisTag:(w if a.axisTag=='wght' else a.defaultValue) for a in reference['fvar'].axes}
                    instance=instantiateVariableFont(variable,coords,inplace=False)
                    path=tmp/'instance.ttf';instance.save(path);instance.close()
                    check=inspect_font(path,None,set(source.getBestCmap()))
                    if check['outline_exceeds_windows_bounds'] or check['outline_exceeds_hhea_bounds']:
                        raise ValueError('Variable instance exceeds line bounds')
                    samples.append({'weight':w,'bounds':check['bounds']})
                candidate.replace(output_path)
                report=check.copy();report.update(file=output_path.name,sha256=sha256(output_path),
                    family=sorted(font_families(variable)),weight=weight.defaultValue,
                    source_sha256=sha256(source_path),reference_sha256=sha256(reference_path),
                    reference_file=reference_path.name,axes=[{'tag':a.axisTag,'min':a.minValue,'default':a.defaultValue,'max':a.maxValue} for a in variable['fvar'].axes],
                    variable_samples=samples,layout_behavior='default weight GSUB/GPOS across weights',optical_size_behavior='accepted; Pretendard outlines invariant',
                    fitted_glyphs=sum(f<1 for f in scales.values()))
                return report
            finally:variable.close()


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Build-only Korean Pretendard TTFs. Never installs fonts.')
    parser.add_argument('--source', type=Path, required=True, help='Static alternative TTF directory or Variable TTF')
    parser.add_argument('--references', type=Path, default=Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts')
    parser.add_argument('--output', type=Path, required=True, help='New directory outside Windows/Fonts')
    parser.add_argument('--segoe-only', action='store_true')
    parser.add_argument('--installable', action='store_true', help='Build a bounded 10-font installable package; Variable input required')
    args = parser.parse_args()
    try:
        report = build_all(args.source, args.references, args.output, not args.segoe_only, installable=args.installable)
    except Exception as exc:
        parser.exit(1, f'Build failed; no fonts installed: {exc}\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
