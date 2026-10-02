from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import newTable
from fontTools.ttLib.tables._f_v_a_r import Axis


def make_font(path, family='Pretendard', codepoints=None, variable=False, vertical=False):
    codepoints = codepoints or {0x41, 0xAC00, 0x3164, 0x6F22, 0x5B57}
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(['.notdef', 'text'])
    fb.setupCharacterMap({cp: 'text' for cp in codepoints})
    glyphs = {}
    for name in ('.notdef', 'text'):
        pen = TTGlyphPen(None)
        if name == 'text':
            pen.moveTo((0, -100))
            pen.lineTo((500, -100))
            pen.lineTo((500, 700))
            pen.lineTo((0, 700))
            pen.closePath()
        glyphs[name] = pen.glyph()
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({name: (600, 0) for name in glyphs})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    if vertical:
        fb.setupVerticalMetrics({name: (1000, 100) for name in glyphs})
        fb.setupVerticalHeader(ascent=800, descent=-200)
    fb.setupNameTable({'familyName': family, 'styleName': 'Regular',
                      'uniqueFontIdentifier': family + '-Test',
                      'fullName': family, 'psName': family.replace(' ', '')})
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    fb.setupPost()
    fb.setupMaxp()
    if variable:
        fb.font['fvar'] = newTable('fvar')
        axis = Axis()
        axis.axisTag, axis.minValue, axis.defaultValue, axis.maxValue = 'wght', 100, 400, 900
        axis.flags, axis.axisNameID = 0, 256
        fb.font['name'].setName('Weight', 256, 3, 1, 0x409)
        fb.font['fvar'].axes = [axis]
        fb.font['fvar'].instances = []
        fb.font['gvar'] = newTable('gvar')
        fb.font['gvar'].variations = {}
    fb.save(path)
