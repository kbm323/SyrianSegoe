import ctypes

# --- Windows System Metrics Structures ---
class LOGFONTW(ctypes.Structure):
    _fields_ = [
        ("lfHeight", ctypes.c_long), ("lfWidth", ctypes.c_long),
        ("lfEscapement", ctypes.c_long), ("lfOrientation", ctypes.c_long),
        ("lfWeight", ctypes.c_long), ("lfItalic", ctypes.c_byte),
        ("lfUnderline", ctypes.c_byte), ("lfStrikeOut", ctypes.c_byte),
        ("lfCharSet", ctypes.c_byte), ("lfOutPrecision", ctypes.c_byte),
        ("lfClipPrecision", ctypes.c_byte), ("lfQuality", ctypes.c_byte),
        ("lfPitchAndFamily", ctypes.c_byte), ("lfFaceName", ctypes.c_wchar * 32),
    ]

class NONCLIENTMETRICSW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("iCaptionWidth", ctypes.c_int), ("iCaptionHeight", ctypes.c_int),
        ("lfCaptionFont", LOGFONTW),
        ("iSmCaptionWidth", ctypes.c_int), ("iSmCaptionHeight", ctypes.c_int),
        ("lfSmCaptionFont", LOGFONTW),
        ("iMenuWidth", ctypes.c_int), ("iMenuHeight", ctypes.c_int),
        ("lfMenuFont", LOGFONTW),
        ("iStatusWidth", ctypes.c_int), ("iStatusHeight", ctypes.c_int),
        ("lfStatusFont", LOGFONTW),
        ("lfMessageFont", LOGFONTW),
        ("iPaddedBorderWidth", ctypes.c_int),
    ]

SPI_GETNONCLIENTMETRICS = 0x0029
SPI_SETNONCLIENTMETRICS = 0x002A
SPI_GETICONTITLELOGFONT = 0x001F
SPI_SETICONTITLELOGFONT = 0x0022
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02

def pt_to_height(pt):
    """Calculates lfHeight from point size. Windows uses negative values for precise scaling."""
    return -round((pt * 96) / 72)

def height_to_pt(height):
    """Converts lfHeight back to point size for UI display."""
    return round(abs(height) * 72 / 96)

def get_current_metrics():
    """Returns current system font sizes in pt."""
    ncm = NONCLIENTMETRICSW()
    ncm.cbSize = ctypes.sizeof(NONCLIENTMETRICSW)
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETNONCLIENTMETRICS, ncm.cbSize, ctypes.byref(ncm), 0)
    
    lf_icon = LOGFONTW()
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETICONTITLELOGFONT, ctypes.sizeof(LOGFONTW), ctypes.byref(lf_icon), 0)
    
    return {
        "caption": height_to_pt(ncm.lfCaptionFont.lfHeight),
        "sm_caption": height_to_pt(ncm.lfSmCaptionFont.lfHeight),
        "menu": height_to_pt(ncm.lfMenuFont.lfHeight),
        "status": height_to_pt(ncm.lfStatusFont.lfHeight),
        "message": height_to_pt(ncm.lfMessageFont.lfHeight),
        "icon": height_to_pt(lf_icon.lfHeight)
    }

def apply_system_metrics(sizes_dict):
    """
    Applies font sizes to various system elements.
    sizes_dict should contain mapping like: {'caption': 9, 'menu': 10, ...}
    """
    ncm = NONCLIENTMETRICSW()
    ncm.cbSize = ctypes.sizeof(NONCLIENTMETRICSW)
    
    # Load current first to preserve other settings (widths, etc)
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETNONCLIENTMETRICS, ncm.cbSize, ctypes.byref(ncm), 0)
    
    # Update fields if provided in dict
    if 'caption' in sizes_dict: ncm.lfCaptionFont.lfHeight = pt_to_height(sizes_dict['caption'])
    if 'sm_caption' in sizes_dict: ncm.lfSmCaptionFont.lfHeight = pt_to_height(sizes_dict['sm_caption'])
    if 'menu' in sizes_dict: ncm.lfMenuFont.lfHeight = pt_to_height(sizes_dict['menu'])
    if 'status' in sizes_dict: ncm.lfStatusFont.lfHeight = pt_to_height(sizes_dict['status'])
    if 'message' in sizes_dict: ncm.lfMessageFont.lfHeight = pt_to_height(sizes_dict['message'])
    
    # Apply Non-Client Metrics
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETNONCLIENTMETRICS, ncm.cbSize, ctypes.byref(ncm), SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)
    
    # Handle Icons separately
    if 'icon' in sizes_dict:
        lf_icon = LOGFONTW()
        ctypes.windll.user32.SystemParametersInfoW(SPI_GETICONTITLELOGFONT, ctypes.sizeof(LOGFONTW), ctypes.byref(lf_icon), 0)
        lf_icon.lfHeight = pt_to_height(sizes_dict['icon'])
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETICONTITLELOGFONT, ctypes.sizeof(LOGFONTW), ctypes.byref(lf_icon), SPIF_UPDATEINIFILE | SPIF_SENDCHANGE)

def apply_entire_size(pt):
    """Applies a single point size to all system elements."""
    new_sizes = {k: pt for k in ['caption', 'sm_caption', 'menu', 'status', 'message', 'icon']}
    apply_system_metrics(new_sizes)