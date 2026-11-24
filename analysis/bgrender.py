"""Render one SNES BG layer from a VRAM + CGRAM dump.
  python bgrender.py vram.bin cgram.bin map_word_addr chr_word_addr bpp out.png [pal_base]
Prints the set of tile numbers used (non-zero entries)."""
import sys
from PIL import Image
sys.path.insert(0, __import__('os').path.dirname(__file__))
from tiles import decode_tile

vram = open(sys.argv[1], 'rb').read()
cg = open(sys.argv[2], 'rb').read()
mapw, chrw, bpp = int(sys.argv[3], 16), int(sys.argv[4], 16), int(sys.argv[5])
out = sys.argv[6]
pal_base = int(sys.argv[7]) if len(sys.argv) > 7 else 0


def color(i):
    v = cg[2 * i] | cg[2 * i + 1] << 8
    return ((v & 31) * 8, ((v >> 5) & 31) * 8, ((v >> 10) & 31) * 8)


im = Image.new('RGB', (256, 256))
used = set()
for ty in range(32):
    for tx in range(32):
        e = vram[mapw * 2 + (ty * 32 + tx) * 2] | vram[mapw * 2 + (ty * 32 + tx) * 2 + 1] << 8
        t, pal, hf, vf = e & 0x3FF, (e >> 10) & 7, (e >> 14) & 1, (e >> 15) & 1
        if t:
            used.add(t)
        px = decode_tile(vram, chrw * 2 + t * 8 * bpp, bpp)
        for y in range(8):
            for x in range(8):
                v = px[7 - y if vf else y][7 - x if hf else x]
                if v:
                    c = color(pal_base + pal * (1 << bpp) + v)
                    im.putpixel((tx * 8 + x, ty * 8 + y), c)
im.resize((512, 512), Image.NEAREST).save(out)
print('tiles used', len(used), 'min', min(used) if used else None, 'max', max(used) if used else None)
