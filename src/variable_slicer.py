import os
import shutil
import io
import copy
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools import subset
from glyph_policy import KOREAN_TEXT_CODEPOINTS

def slice_variable_font(var_path, weight_val, out_path):
    """Instantiate a weight, preserving Korean text beyond Segoe UI's cmap."""
    font = TTFont(var_path)
    static_font = instantiateVariableFont(font, {"wght": weight_val})

    # منطق جديد: تفريغ الجداول وإعادة تحميل الخط في الذاكرة لمنع أخطاء KeyError (مثل tilde)
    # هذه الخطوة تضمن أن فهارس الرموز محدثة تماماً قبل عملية التقليم
    buf = io.BytesIO()
    static_font.save(buf)
    buf.seek(0)
    static_font = TTFont(buf)

    # تحسين السرعة عبر حذف الرموز غير الموجودة في سيغو الأصلي
    try:
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        segoe_ref = os.path.join(windir, 'Fonts', 'segoeui.ttf')
        if os.path.exists(segoe_ref):
            ref_font = TTFont(segoe_ref)
            ref_unicodes = set(ref_font.getBestCmap().keys())
            ref_unicodes.update(KOREAN_TEXT_CODEPOINTS)
            static_cmap = static_font.getBestCmap()
            static_order = set(static_font.getGlyphOrder())
            static_set = static_font.getGlyphSet()
            
            # فحص ثلاثي: يجب أن يكون الرمز في Cmap، وله اسم في GlyphOrder، وبيانات مادية في GlyphSet
            # هذا يمنع أخطاء KeyError لرموز مثل uni200B أو الرموز الرياضية المفقودة
            valid_unicodes = [
                u for u in ref_unicodes 
                if u in static_cmap and static_cmap[u] in static_order and static_cmap[u] in static_set
            ]
            
            options = subset.Options()
            subsetter = subset.Subsetter(options=options)
            subsetter.populate(unicodes=valid_unicodes)
            subsetter.subset(static_font)
            ref_font.close()
        buf.close()
    except Exception as e:
        print(f"[Slicer] Pruning optimization failed (non-critical): {e}")

    static_font.save(out_path)

def create_variable_spoof(input_path, output_path):
    """Creates a copy of the font to be used as a placeholder/spoof."""
    reference = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'SegUIVar.ttf')
    with TTFont(input_path) as font, TTFont(reference) as ref:
        identity_ids = {1, 2, 4, 6, 16, 17, 21, 22}
        font['name'].names = [r for r in font['name'].names if r.nameID not in identity_ids]
        font['name'].names.extend(copy.deepcopy(r) for r in ref['name'].names if r.nameID in identity_ids)
        if 'DSIG' in font:
            del font['DSIG']
        font.save(output_path)

def resolve_weights(base_path, is_var, reg_path, light_path, semilight_path, semibold_path, bold_path, black_path, lang_prefix, weights=None):
    """
    Determines the required weights needed.
    If variable, it slices them. If static, it maps existing files or defaults to Regular.
    """
    if weights is None:
        weights = [300, 350, 400, 600, 700, 900]

    paths = []
    if is_var:
        # Standard Windows weights: Light, Semilight, Reg, Semibold, Bold, Black
        for w in weights:
            out = os.path.join(base_path, f"temp_{lang_prefix}_{w}.ttf")
            slice_variable_font(reg_path, w, out)
            paths.append(out)
    else:
        r = reg_path if reg_path else "NONE"
        lt = light_path if light_path else r
        sl = semilight_path if semilight_path else r
        b = bold_path if bold_path else r
        sb = semibold_path if semibold_path else b
        blk = black_path if black_path else b

        static_map = [lt, sl, r, sb, b, blk]
        # For custom weight lists, map values by position while preserving fallback behavior.
        if len(weights) == 6:
            paths = static_map
        else:
            key_map = {
                0: lt,
                1: sl,
                2: r,
                3: sb,
                4: b,
                5: blk
            }
            for idx in range(len(weights)):
                paths.append(key_map.get(idx, r))
    return paths
