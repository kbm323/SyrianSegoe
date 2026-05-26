import os
import shutil
import io
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools import subset

def slice_variable_font(var_path, weight_val, out_path):
    """Instantiates a static font and prunes it to Segoe UI's character set for speed."""
    font = TTFont(var_path)
    static_font = instantiateVariableFont(font, {"wght": weight_val})

    buf = io.BytesIO()
    static_font.save(buf)
    buf.seek(0)
    static_font = TTFont(buf)

    try:
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        segoe_ref = os.path.join(windir, 'Fonts', 'segoeui.ttf')
        if os.path.exists(segoe_ref):
            ref_font = TTFont(segoe_ref)
            ref_unicodes = set(ref_font.getBestCmap().keys())
            static_cmap = static_font.getBestCmap()
            static_order = set(static_font.getGlyphOrder())
            static_set = static_font.getGlyphSet()
            
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
    try:
        shutil.copy(input_path, output_path)
    except Exception as e:
        print(f"[Slicer] Error copying variable font: {e}")

def resolve_weights(base_path, is_var, reg_path, light_path, semilight_path, semibold_path, bold_path, black_path, lang_prefix):
    """
    Determines the 6 standard weights needed. 
    If variable, it slices them. If static, it maps existing files or defaults to Regular.
    """
    paths = []
    if is_var:
        # Standard Windows weights: Light, Semilight, Reg, Semibold, Bold, Black
        weights = [300, 350, 400, 600, 700, 900] 
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
        
        paths = [lt, sl, r, sb, b, blk]
    return paths
