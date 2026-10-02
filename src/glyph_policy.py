"""Shared Korean coverage policy for FontForge and FontTools builders."""

# Inclusive Unicode block boundaries; unassigned slots are not invented.
HANGUL_RANGES = ((0x1100, 0x11FF), (0x3130, 0x318F), (0xA960, 0xA97F),
                 (0xAC00, 0xD7AF), (0xD7B0, 0xD7FF))
KOREAN_TEXT_RANGES = HANGUL_RANGES + (
    (0x3000, 0x303F),   # CJK punctuation
    (0x3200, 0x33FF),   # Enclosed CJK and compatibility symbols
    (0x3400, 0x4DBF),   # CJK Extension A
    (0x4E00, 0x9FFF),   # Unified ideographs, not the upstream partial subset
    (0xF900, 0xFAFF),   # Compatibility ideographs
    (0xFF00, 0xFFEF),   # Fullwidth/halfwidth forms
    (0x2460, 0x24FF),   # Enclosed alphanumerics
)
KOREAN_TEXT_CODEPOINTS = frozenset(
    cp for first, last in KOREAN_TEXT_RANGES for cp in range(first, last + 1)
)


def is_hangul(codepoint):
    return any(first <= codepoint <= last for first, last in HANGUL_RANGES)


def glyph_codepoints(glyph):
    """Use actual cmap encodings, including aliases, before interpreting names."""
    points = {getattr(glyph, 'unicode', -1)}
    for alias in getattr(glyph, 'altuni', None) or ():
        points.add(alias[0])
    return points


def protected_korean_glyph(glyph):
    return bool(glyph_codepoints(glyph) & KOREAN_TEXT_CODEPOINTS)


def has_hangul(font):
    return any(any(is_hangul(cp) for cp in glyph_codepoints(g)) for g in font.glyphs())
