"""Korean title logo 「슈퍼로봇대전」 for SRW EX (the blue "EX" is a separate layer and stays).

Title screen: Mode 1, the logo is BG1 (tilemap word $7000) palette 3, tiles 0x201-0x274 of graphics
asset 47 ($13:8000, LZ, 32 KB, loaded to VRAM word $0000). The logo cells are rows 5-10, columns
7-24, one distinct tile per cell (taken from a VRAM dump, tools/rt/titleppu.lua). We keep that map
and repaint those tiles, then recompress asset 47 to its own bank.

  python logo.py preview out.png
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'analysis'))
import lz
import lzc

FONTDIR = os.path.join(os.environ.get('SRW3_FONTDIR') or os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft/Windows/Fonts'), '')  # SRW3_FONTDIR overrides
ASSET_TABLE = 0xA08000
ASSET = 47
ORIG_SRC = 0x138000
NEW_SRC = 0xBF8000                  # bank $BF is kept free of text (srwtext.TEXT_BANKS)
W, H = 144, 48                      # BG1 columns 7-24, rows 5-10
# palette 3 (title screen CGRAM 48-63)
PAL = [(0, 0, 0), (248, 248, 248), (240, 240, 136), (240, 240, 56), (232, 216, 0), (216, 184, 0),
       (200, 160, 0), (192, 128, 0), (184, 104, 0), (160, 80, 0), (120, 64, 0), (72, 48, 0),
       (0, 80, 136), (0, 64, 112), (0, 48, 88), (0, 24, 56)]
BLANK = None
# BG1 tilemap of the logo, rows 5-10 x columns 8-24 (VRAM dump of the title screen)
MAP = [
    [None, 0x201, 0x202, 0x203, 0x204, 0x205, 0x206, 0x207, 0x208, 0x209, 0x20A, 0x20B, 0x20C, 0x20D, 0x20E, 0x20F, 0x220, 0x221],
    [None, 0x211, 0x212, 0x213, 0x214, 0x215, 0x216, 0x217, 0x218, 0x219, 0x21A, 0x21B, 0x21C, 0x21D, 0x21E, 0x21F, 0x230, 0x231],
    [0x222, 0x223, 0x224, 0x225, 0x226, 0x227, 0x228, 0x229, 0x22A, 0x22B, 0x22C, 0x22D, 0x22E, 0x22F, 0x240, 0x241, 0x242, 0x243],
    [0x232, 0x233, 0x234, 0x235, 0x236, 0x237, 0x238, 0x239, 0x23A, 0x23B, 0x23C, 0x23D, 0x23E, 0x23F, 0x250, 0x251, 0x252, 0x253],
    [0x244, 0x245, 0x246, 0x247, 0x248, 0x249, 0x24A, 0x24B, 0x24C, 0x24D, 0x24E, 0x24F, 0x260, 0x261, 0x262, 0x263, 0x264, 0x265],
    [0x254, 0x255, 0x256, 0x257, 0x258, 0x259, 0x25A, 0x25B, 0x25C, 0x25D, 0x25E, 0x25F, 0x270, 0x271, 0x272, 0x273, 0x274, None],
]


def tile_map():
    return {(r, c): t for r, row in enumerate(MAP) for c, t in enumerate(row) if t != BLANK}


def mask_text(text, font, w, h, skew=0.0, thresh=80):
    """text rendered 4x, sheared, scaled to w x h with box filtering, then thresholded
    (a low threshold thickens strokes without filling the counters)"""
    f = ImageFont.truetype(font, h * 4)
    l, t, r, b = f.getbbox(text)
    im = Image.new('L', (r - l + 16, b - t + 16), 0)
    ImageDraw.Draw(im).text((8 - l, 8 - t), text, font=f, fill=255)
    if skew:
        im = im.transform((im.width + int(im.height * skew) + 2, im.height), Image.AFFINE,
                          (1, skew, -im.height * skew, 0, 1, 0), Image.BILINEAR)
    im = im.crop(im.getbbox())
    im = im.resize((w, h), Image.BOX)
    return im.point(lambda v: 255 if v >= thresh else 0)


def draw():
    canvas = [[0] * W for _ in range(H)]
    # big line, slanted
    big = mask_text('슈퍼로봇대전', FONTDIR + 'NanumSquareEB.ttf', 124, 43, skew=0.18, thresh=70)
    layers = [(big, 8, 1)]            # (mask, x, y)

    def on(m, x, y, px, py):
        u, v = px - x, py - y
        return 0 <= u < m.width and 0 <= v < m.height and m.getpixel((u, v))
    # extrusion: blue, 4 px down-right, darker further back
    for d, colr in ((3, 15), (2, 13), (1, 12)):
        for m, x, y in layers:
            for py in range(H):
                for px in range(W):
                    if on(m, x + d, y + d, px, py):
                        canvas[py][px] = colr
    # face: vertical gradient yellow -> orange, white rim on top-left
    for m, x, y in layers:
        hgt = m.height
        for py in range(H):
            for px in range(W):
                if on(m, x, y, px, py):
                    v = (py - y) / max(1, hgt - 1)
                    idx = [2, 3, 3, 4, 5, 6, 7, 8, 9][min(8, int(v * 9))]
                    if not on(m, x, y, px - 1, py) or not on(m, x, y, px, py - 1):
                        idx = 1 if v < 0.5 else 3
                    canvas[py][px] = idx
    # dark outline around everything for contrast on the dark background
    out = [row[:] for row in canvas]
    for py in range(H):
        for px in range(W):
            if canvas[py][px] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    qx, qy = px + dx, py + dy
                    if 0 <= qx < W and 0 <= qy < H and canvas[qy][qx] in range(1, 12):
                        out[py][px] = 11
                        break
    for r, row in enumerate(MAP):
        for c, t in enumerate(row):
            if t == BLANK:
                for py in range(r * 8, r * 8 + 8):
                    for px in range(c * 8, c * 8 + 8):
                        if out[py][px]:
                            raise SystemExit('logo: pixel in blank cell row %d col %d' % (r, c))
    return out


def encode_into(asset, canvas):
    data = bytearray(asset)
    for (r, c), t in tile_map().items():
        o = t * 32
        for y in range(8):
            row = canvas[r * 8 + y][c * 8:c * 8 + 8]
            for plane in range(4):
                b = 0
                for x in range(8):
                    if row[x] & (1 << plane):
                        b |= 0x80 >> x
                data[o + 16 * (plane // 2) + 2 * y + (plane & 1)] = b
    return bytes(data)


def f(a):
    return ((a >> 16) & 0x7F) * 0x8000 + (a & 0x7FFF)


def apply(rom, rom_orig):
    asset, _ = lz.decompress(rom_orig, ORIG_SRC)
    new = encode_into(asset, draw())
    comp = lzc.compress(new)
    o = f(NEW_SRC)
    assert len(comp) <= 0x8000 - (NEW_SRC & 0x7FFF), 'logo does not fit in bank $B0'
    rom[o:o + len(comp)] = comp
    a = f(ASSET_TABLE) + 3 * ASSET
    assert rom_orig[a:a + 3] == bytes([ORIG_SRC & 0xFF, (ORIG_SRC >> 8) & 0xFF, ORIG_SRC >> 16])
    rom[a:a + 3] = bytes([NEW_SRC & 0xFF, (NEW_SRC >> 8) & 0xFF, NEW_SRC >> 16])
    return len(comp)


def preview(path):
    cv = draw()
    im = Image.new('RGB', (W, H))
    for y in range(H):
        for x in range(W):
            im.putpixel((x, y), PAL[cv[y][x]] if cv[y][x] else (40, 20, 30))
    im.resize((W * 4, H * 4), Image.NEAREST).save(path)


if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        preview(sys.argv[2])
