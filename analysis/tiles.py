"""Render SNES planar tile data as a grayscale sheet.  python tiles.py in.bin out.png bpp [tiles_per_row] [scale]"""
import sys
from PIL import Image


def decode_tile(d, o, bpp):
    px = [[0] * 8 for _ in range(8)]
    for y in range(8):
        for plane in range(bpp):
            # SNES: planes in pairs; pair k at offset 16*k, row y at 2*y (+1 for odd plane)
            b = d[o + 16 * (plane // 2) + 2 * y + (plane & 1)] if o + 16 * (plane // 2) + 2 * y + (plane & 1) < len(d) else 0
            for x in range(8):
                if b & (0x80 >> x):
                    px[y][x] |= 1 << plane
    return px


def render(d, bpp, per_row=16, scale=2):
    tsize = 8 * bpp
    n = len(d) // tsize
    rows = (n + per_row - 1) // per_row
    im = Image.new('L', (per_row * 8, rows * 8))
    mx = (1 << bpp) - 1
    for t in range(n):
        px = decode_tile(d, t * tsize, bpp)
        for y in range(8):
            for x in range(8):
                im.putpixel(((t % per_row) * 8 + x, (t // per_row) * 8 + y), px[y][x] * 255 // mx)
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    bpp = int(sys.argv[3])
    per = int(sys.argv[4]) if len(sys.argv) > 4 else 16
    sc = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    render(d, bpp, per, sc).save(sys.argv[2])
