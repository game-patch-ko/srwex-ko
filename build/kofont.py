"""Korean font + encoding for the SRW EX Korean patch.

Hangul glyphs are assigned to slots at build time: only the syllables that the translation
actually uses get a slot (8 prefixes x 256 = 2,048 slots; the 3rd game's whole translation
used 1,012 distinct syllables).

Slot i (0..2047) <-> 2-byte code PREFIX[i >> 8], i & 0xFF
  PREFIX = EC ED EE EF F0 F1 F2 F3  -> internal glyph code 0x100 + i (hook: code hi = prefix - $EB)
Slot order = KS X 1001 order of the used syllables (deterministic for a given translation).

Glyph format = original kanji format: 32 bytes, left 8x16 column then right 8x16 column,
1bpp, drawn area rows 2..13 (like the EX kanji), columns 0..11.
Default font: MonaS12 12px (Monad ABXY, SIL Open Font License 1.1), the font of the 3rd-game patch.
"""
import os
from PIL import Image, ImageDraw, ImageFont

PREFIX = [0xEC, 0xED, 0xEE, 0xEF, 0xF0, 0xF1, 0xF2, 0xF3]
MAX_GLYPHS = len(PREFIX) * 256  # 2048


def ksx1001_hangul():
    out = []
    for hi in range(0xB0, 0xC9):
        for lo in range(0xA1, 0xFF):
            try:
                out.append(bytes([hi, lo]).decode('euc-kr'))
            except UnicodeDecodeError:
                pass
    assert len(out) == 2350, len(out)
    return out


HANGUL = ksx1001_hangul()
KS_ORDER = {c: i for i, c in enumerate(HANGUL)}
KS_ORDER['　'] = 9999   # full-width space: blank 12px glyph (original $F2FF)
# filled by set_charset(); HANGUL_INDEX[c] = slot
HANGUL_INDEX = {}
USED = []


def set_charset(chars):
    """chars: iterable of hangul syllables used by the translation (KS X 1001 only)"""
    global USED
    bad = sorted(set(c for c in chars if c not in KS_ORDER))
    if bad:
        raise ValueError('not in KS X 1001: %s' % ''.join(bad))
    USED = sorted(set(chars), key=KS_ORDER.get)
    if len(USED) > MAX_GLYPHS:
        raise ValueError('%d distinct hangul > %d slots' % (len(USED), MAX_GLYPHS))
    HANGUL_INDEX.clear()
    HANGUL_INDEX.update({c: i for i, c in enumerate(USED)})
    return len(USED)


def is_hangul(c):
    return c in KS_ORDER


def code_bytes(i):
    return bytes([PREFIX[i >> 8], i & 0xFF])


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_FONT = os.environ.get('SRW3_MONAS12') or os.path.join(REPO, 'tools', 'fonts', 'mona', 'MonaS', '01 Main', 'MonaS12.ttf')


def render_glyph(ch, font, yoff):
    im = Image.new('1', (16, 16), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    d.text((0, yoff), ch, font=font, fill=1)
    px = im.load()
    out = bytearray(32)
    for y in range(16):
        for x in range(16):
            if px[x, y] and x < 12 and 1 <= y <= 14:
                out[(x // 8) * 16 + y] |= 0x80 >> (x % 8)
    return bytes(out)


def build_font(path=None, size=12):
    path = path or os.environ.get('SRWEX_KOFONT') or DEFAULT_FONT
    font = ImageFont.truetype(path, size)
    top = min(font.getbbox(c)[1] for c in HANGUL[:200])
    yoff = 2 - top
    data = bytearray()
    for c in USED:
        data += render_glyph(c, font, yoff)
    return bytes(data)
