"""Match set-2 metasprites to stage names (sys0E) and find each title's font block (2..7)."""
import sys, re, json
sys.path.insert(0, '.')
import lz
from tiles import decode_tile
from PIL import Image
R = open('../Super Robot Taisen EX (J).smc', 'rb').read()
def f(a): return ((a >> 16) & 0x7f) * 0x8000 + (a & 0x7fff)
S2 = f(0x84CEFE)
N = ((R[S2] | R[S2 + 1] << 8) - 0xCEFE) // 2
ptr = [R[S2 + 2 * k] | R[S2 + 2 * k + 1] << 8 for k in range(N)]
FONT, _ = lz.decompress(R, 0xA091A6)
INV = {}
for l in open('srwex_jp.tbl', encoding='utf-8'):
    k, v = l.rstrip('\n').split('=', 1)
    INV.setdefault(v, bytes.fromhex(k))
names = [l[4:].replace('{END}', '').strip() for l in open('../script/sys0E.txt', encoding='utf-8') if l.startswith('JP:')]


def rec(k):
    o = f(0x840000 | ptr[k]); n = R[o]; out = []
    for j in range(n):
        t, a, dy, dx = R[o + 1 + 4 * j:o + 5 + 4 * j]
        out.append((t | (a & 1) << 8, dy - 256 if dy > 127 else dy, dx - 256 if dx > 127 else dx))
    return out


def tile_off(t, blk):
    if t >= 0x180: return (t - 0x180) * 32
    if t < 0x080: return 0x1000 + t * 32
    return blk * 0x1000 + (t - 0x080) * 32


def glyph16(t, blk):
    im = Image.new('L', (16, 16))
    for sub, (ox, oy) in zip((0, 1, 16, 17), ((0, 0), (8, 0), (0, 8), (8, 8))):
        px = decode_tile(FONT, tile_off(t + sub, blk), 4)
        for y in range(8):
            for x in range(8):
                if px[y][x] == 8: im.putpixel((ox + x, oy + y), 255)
    return im


def ref(ch):
    b = INV.get(ch)
    im = Image.new('L', (16, 16))
    if b is None: return None
    if len(b) == 2:
        i = (b[0] - 0xF0) * 256 + b[1]; p = 0x21 * 0x8000 + i * 32
        for y in range(16):
            for x in range(16):
                v = R[p + (x // 8) * 16 + y]
                if v >> (7 - x % 8) & 1: im.putpixel((x, y), 255)
    else:
        p = 0x1061BC + b[0] * 16
        for y in range(16):
            for x in range(8):
                if R[p + y] >> (7 - x) & 1: im.putpixel((x, y), 255)
    return im


def norm(im):
    bb = im.getbbox()
    if not bb: return None
    return im.crop(bb).resize((12, 12), Image.BILINEAR)


def sim(a, b):
    if a is None or b is None: return 0.0
    pa, pb = list(a.getdata()), list(b.getdata())
    num = sum(min(x, y) for x, y in zip(pa, pb)); den = sum(max(x, y) for x, y in zip(pa, pb)) or 1
    return num / den


REF = {}
res = {}
for k in range(1, N):
    r = rec(k)
    ts = [t for t, _, _ in r]
    if 0x1AA not in ts or 0x1A8 not in ts: continue
    body = [x for x in r if x[0] not in (0x1AA, 0x1A8)]
    body.sort(key=lambda s: (s[1], s[2]))       # top line first, left to right
    best = None
    for nm in names:
        chars = [c for c in nm if c not in ' 　']
        if len(chars) != len(body): continue
        for blk in (range(2, 8) if any(0x080 <= t < 0x100 for t, _, _ in body) else [2]):
            sc = 0
            for (t, dy, dx), c in zip(body, chars):
                if c not in REF: REF[c] = norm(ref(c)) if ref(c) else None
                sc += sim(norm(glyph16(t, blk)), REF[c])
            sc /= len(chars)
            if best is None or sc > best[0]: best = (sc, nm, blk)
    res[k] = best
    print(k, len(body), best)
json.dump({k: v for k, v in res.items()}, open('titlematch.json', 'w', encoding='utf-8'), ensure_ascii=False)
