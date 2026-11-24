"""Render the 51 stage-title metasprites (ids 0xC0-0xF2) with the title font (asset 3, $20:C182).

  python titles.py out.png            every title x every candidate block for sprite tiles 0x080-0x0FF

VRAM sprite tiles at title time (from the common stage-intro script $80:E2E0):
  0x000-0x07F <- font block 1 ($7F:1000),  0x180-0x1FF <- font block 0 ($7F:0000),
  0x080-0x0FF <- a stage-specific block (unknown: drawn for blocks 2..7 here).
"""
import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lz
from tiles import decode_tile

rom = open(lz.ROM, 'rb').read()
FONT, _ = lz.decompress(rom, 0x20C182)
SET0 = 0x038D8A


def f(a):
    return ((a >> 16) & 0x7F) * 0x8000 + (a & 0x7FFF)


def records():
    out = []
    for i in range(0xC0, 0xF3):
        p = rom[f(SET0) + 2 * i] | rom[f(SET0) + 2 * i + 1] << 8
        o = f(0x030000 | p)
        n = rom[o]
        spr = []
        for k in range(n):
            t, a, dy, dx = rom[o + 1 + 4 * k:o + 5 + 4 * k]
            spr.append(((a & 1) << 8 | t, a, dx - 256 if dx > 127 else dx, dy - 256 if dy > 127 else dy))
        out.append((i, p, spr))
    return out


def vram_tile(t, high_block):
    if t >= 0x180:
        return 0x0000 + (t - 0x180) * 32
    if t >= 0x100:
        return None
    if t >= 0x080:
        return high_block * 0x1000 + (t - 0x080) * 32
    return 0x1000 + t * 32


def glyph16(t, high_block):
    im = Image.new('L', (16, 16))
    for sub, (ox, oy) in zip((0, 1, 16, 17), ((0, 0), (8, 0), (0, 8), (8, 8))):
        o = vram_tile(t + sub, high_block)
        if o is None or o + 32 > len(FONT):
            continue
        px = decode_tile(FONT, o, 4)
        for y in range(8):
            for x in range(8):
                im.putpixel((ox + x, oy + y), 255 if px[y][x] else 0)
    return im


def render(spr, high_block):
    im = Image.new('L', (256, 48))
    for t, a, dx, dy in spr:
        im.paste(glyph16(t, high_block), (128 + dx, 16 + dy))
    return im


if __name__ == '__main__':
    recs = records()
    blocks = list(range(2, 8))
    sheet = Image.new('L', (40 + 256 * len(blocks), 48 * len(recs)), 40)
    d = ImageDraw.Draw(sheet)
    for r, (i, p, spr) in enumerate(recs):
        d.text((2, r * 48 + 18), '%02X' % i, fill=255)
        for c, b in enumerate(blocks):
            sheet.paste(render(spr, b), (40 + c * 256, r * 48))
    sheet.save(sys.argv[1])
    print(len(recs), 'titles')
