"""Cross-check the hand-transcribed kanji table against MS Gothic 12px bitmaps.
For every ROM kanji glyph, find the most similar JIS X 0208 kanji and compare with the table."""
from PIL import Image, ImageDraw, ImageFont
import numpy as np, json, sys
ROM = open('C:/work/sfc/srw3-ko/Super Robot Taisen EX (J).smc', 'rb').read()
tbl = {}
for line in open('C:/work/sfc/srw3-ko/analysis/srw3_jp.tbl', encoding='utf-8'):
    k, _, v = line.rstrip('\n').partition('=')
    if len(k) == 4 and k[0] == 'F' and k[1] in '012':
        tbl[(int(k[1]) << 8) | int(k[2:], 16)] = v

def rom_glyph(i):
    o = 0x81856 + i * 32
    a = np.zeros((16, 16), bool)
    for y in range(16):
        for x in range(16):
            a[y, x] = (ROM[o + (x // 8) * 16 + y] >> (7 - x % 8)) & 1
    return a

font = ImageFont.truetype('C:/Windows/Fonts/msgothic.ttc', 12)
def render(ch):
    im = Image.new('1', (16, 16), 0); d = ImageDraw.Draw(im); d.fontmode = '1'
    d.text((0, 0), ch, font=font, fill=1)
    return np.array(im, bool)

def norm(a):
    ys, xs = np.nonzero(a)
    if len(ys) == 0: return a
    b = np.zeros((16, 16), bool); b[:ys.max()-ys.min()+1, :xs.max()-xs.min()+1] = a[ys.min():ys.max()+1, xs.min():xs.max()+1]
    return b

def sim(a, b):
    best = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            s = np.roll(np.roll(b, dy, 0), dx, 1)
            u = (a | s).sum()
            best = max(best, (a & s).sum() / u if u else 0)
    return best

cands = []
for hi in range(0x88, 0xEB):
    for lo in list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)):
        try: c = bytes([hi, lo]).decode('shift_jis')
        except UnicodeDecodeError: continue
        if '\u4e00' <= c <= '\u9fff': cands.append(c)
extra = list('㎜㎞…々')
cands += extra
C = {c: norm(render(c)) for c in cands}
res = []
for i in range(768):
    g = rom_glyph(i)
    if not g.any(): continue
    ng = norm(g)
    scored = sorted(((sim(ng, C[c]), c) for c in cands), reverse=True)[:3]
    t = tbl.get(i)
    ts = sim(ng, C[t]) if t in C else 0
    res.append((i, t, ts, scored))
bad = [r for r in res if r[3][0][1] != r[1]]
print('glyphs', len(res), 'table==best', len(res) - len(bad), 'disagree', len(bad))
for i, t, ts, sc in bad:
    print('%03X table=%s(%.2f) best=%s' % (i, t, ts, ' '.join('%s(%.2f)' % (c, s) for s, c in sc)))
