"""Korean stage titles for SRW EX (the 『...』 sprite text shown when a stage starts).

Called from srwtext.build() on the ROM bytearray before the checksum, and standalone:
  python titles.py preview out.png     draw all Korean titles as they will appear

Facts (HANDOFF.md, stage titles):
- Title font = graphics asset 4 (table $20:8000, 3 bytes per entry) = $20:91A6, LZ (analysis/lz.py),
  32 KB = 8 blocks of 4 KB, 32 glyphs of 16x16 each (4bpp sprite tiles; glyph g = tiles
  (g%8)*2 + (g//8)*32, +1, +16, +17). Colours: 8 outline, 6..1 fill gradient top to bottom.
- At title time (intro script $80:DD36) sprite tiles 0x180 <- block 0 (digits, 第 話 『 』 + common
  glyphs), 0x000 <- block 1, 0x080 <- the stage's block (2..7, tr/titles.tsv, read from images).
- Line 1 = set 0 metasprites 0E (第) digits 11 (話). Line 2 = set 2 metasprite <id>
  (set list $03:80C0, set 2 table $04:CEFE, 2-byte pointers into bank $04);
  record = count, then per sprite: tile, attr (bit0 = tile bit 8, 0x10 base), dy, dx.
New layout: glyphs used by more than one block go to block 1 and block 0 slots 14-31; the rest to the
stage's own block. 第/話 become 제/화. The font is recompressed (analysis/lzc.py) to TITLE_SRC and
asset 4 points there; records are rewritten into the space of the original title records.
"""
import collections
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'analysis'))
import lz
import lzc

TSV = os.path.join(HERE, '..', 'tr', 'titles.tsv')
REPO = os.path.dirname(HERE)
FONT_TTF = os.environ.get('SRW3_MONAS12') or os.path.join(REPO, 'tools', 'fonts', 'mona', 'MonaS', '01 Main', 'MonaS12.ttf')
FONT_SIZE = 12
ASSET_TABLE = 0xA08000
ASSET = 4
ORIG_SRC = 0x2091A6
NEW_SRC = 0xB08800
SET2 = 0x84CEFE
SET2_N = 116
EXTRA_FREE = (0x84FF60, 0x850000)    # free bytes at the end of bank $04
OUTLINE = 8
BLOCK0_FREE = list(range(14, 32))
DIGIT_GLYPH = {str(d): d for d in range(10)}


def f(a):
    return ((a >> 16) & 0x7F) * 0x8000 + (a & 0x7FFF)


def load_titles():
    rows = []
    for ln in open(TSV, encoding='utf-8'):
        if ln.strip() and not ln.startswith('#'):
            i, b, jp, ko = ln.rstrip('\n').split('\t')
            rows.append((int(i, 16), int(b), jp, ko))
    return rows


def glyph_pixels(ch, font):
    """16x16 colour indices: 1px strokes, gradient 6 (top) .. 1 (bottom), outline colour 8"""
    im = Image.new('1', (16, 16), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    l, t, r, b = font.getbbox(ch)
    x = (16 - (r - l)) // 2 - l
    y = (16 - (b - t)) // 2 - t
    d.text((x, y), ch, font=font, fill=1)
    p = im.load()
    ink = {(xx, yy) for yy in range(16) for xx in range(16) if p[xx, yy]}
    out = [[0] * 16 for _ in range(16)]
    if not ink:
        return out
    top = min(yy for _, yy in ink)
    bot = max(yy for _, yy in ink)
    h = max(1, bot - top + 1)
    for xx, yy in ink:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                a, bb = xx + dx, yy + dy
                if 0 <= a < 16 and 0 <= bb < 16 and (a, bb) not in ink:
                    out[bb][a] = OUTLINE
    for xx, yy in ink:
        out[yy][xx] = max(1, min(6, 6 - (yy - top) * 6 // h))
    return out


def put_glyph(font_data, block, slot, px):
    base = block * 0x1000
    t0 = (slot % 8) * 2 + (slot // 8) * 32
    for yy in range(16):
        for xx in range(16):
            t = t0 + (xx // 8) + (yy // 8) * 16
            o = base + t * 32
            v = px[yy][xx]
            bit = 0x80 >> (xx % 8)
            r = yy % 8
            for plane in range(4):
                a = o + 16 * (plane // 2) + 2 * r + (plane & 1)
                if v & (1 << plane):
                    font_data[a] |= bit
                else:
                    font_data[a] &= ~bit & 0xFF


def clear_glyph(font_data, block, slot):
    put_glyph(font_data, block, slot, [[0] * 16 for _ in range(16)])


def plan(rows):
    groups = collections.defaultdict(set)
    for i, b, jp, ko in rows:
        for c in ko:
            if c not in ' ' and c not in DIGIT_GLYPH:
                groups[b].add(c)
    share = collections.Counter()
    for g in groups.values():
        for c in g:
            share[c] += 1
    shared = sorted([c for c, k in share.items() if k > 1], key=lambda c: (-share[c], c))
    slots = [(1, s) for s in range(32)] + [(0, s) for s in BLOCK0_FREE]
    # if a stage block overflows, move its most frequent glyphs to the shared area
    while True:
        over = None
        for b, g in sorted(groups.items()):
            own = [c for c in g if c not in shared]
            if len(own) > 32:
                over = (b, own)
                break
        if not over:
            break
        b, own = over
        freq = collections.Counter(c for i, bb, jp, ko in rows if bb == b for c in ko)
        shared.append(max(own, key=lambda c: freq[c]))
    if len(shared) > len(slots):
        raise SystemExit('titles: %d shared glyphs > %d common slots' % (len(shared), len(slots)))
    where = {c: sl for c, sl in zip(shared, slots)}
    for b, g in sorted(groups.items()):
        own = sorted(c for c in g if c not in where)
        for s, c in enumerate(own):
            where[(b, c)] = (b, s)
    return where


def tile_of(where, b, c):
    if c in DIGIT_GLYPH:
        blk, s = 0, DIGIT_GLYPH[c]
    elif c in where:
        blk, s = where[c]
    else:
        blk, s = where[(b, c)]
    t = (s % 8) * 2 + (s // 8) * 32
    return t + {0: 0x180, 1: 0x000}.get(blk, 0x080)


def record(where, b, ko):
    """『 glyphs 』 centred, 14px per hangul (original 16), 6px per space (all at dy -8 like the original)"""
    adv = lambda c: 6 if c == ' ' else 14
    width = sum(adv(c) for c in ko)
    total = 16 + width + 16
    start = -(total // 2)
    start -= start % 2
    out = [(0x1A8, start)]
    x = start + 16
    for c in ko:
        if c != ' ':
            out.append((tile_of(where, b, c), x))
        x += adv(c)
    out.append((0x1AA, x))
    data = bytearray([len(out)])
    for t, dx in out:
        data += bytes([t & 0xFF, 0x10 | (t >> 8), (-8) & 0xFF, dx & 0xFF])
    return bytes(data)


def build_font(rom_orig, where):
    font, _ = lz.decompress(rom_orig, ORIG_SRC | 0x800000)
    font = bytearray(font)
    ttf = ImageFont.truetype(FONT_TTF, FONT_SIZE)
    for blk in range(1, 8):
        for s in range(32):
            clear_glyph(font, blk, s)
    for s in BLOCK0_FREE:
        clear_glyph(font, 0, s)
    put_glyph(font, 0, 10, glyph_pixels('제', ttf))
    put_glyph(font, 0, 11, glyph_pixels('화', ttf))
    for key, (blk, s) in where.items():
        c = key if isinstance(key, str) else key[1]
        put_glyph(font, blk, s, glyph_pixels(c, ttf))
    return bytes(font)


def set2_ptrs(rom):
    o = f(SET2)
    return [rom[o + 2 * k] | rom[o + 2 * k + 1] << 8 for k in range(SET2_N)]


def apply(rom, rom_orig):
    rows = load_titles()
    where = plan(rows)
    font = build_font(rom_orig, where)
    comp = lzc.compress(font)
    o = f(NEW_SRC)
    assert o + len(comp) <= f(NEW_SRC | 0x7FFF) + 1, 'title font does not fit in bank $B0'
    assert all(x == 0xFF for x in rom[o:o + len(comp)]), 'bank $B0 area for the title font is not free'
    rom[o:o + len(comp)] = comp
    a = f(ASSET_TABLE) + 3 * ASSET
    assert rom_orig[a:a + 3] == bytes([ORIG_SRC & 0xFF, (ORIG_SRC >> 8) & 0xFF, ORIG_SRC >> 16])
    rom[a:a + 3] = bytes([NEW_SRC & 0xFF, (NEW_SRC >> 8) & 0xFF, NEW_SRC >> 16])
    # free space = byte ranges of the original title records + the free end of bank $04
    ptr = set2_ptrs(rom_orig)
    holes = []
    for i, b, jp, ko in rows:
        p = ptr[i]
        n = rom_orig[f(0x840000 | p)]
        holes.append([p, p + 1 + 4 * n])
    holes.sort()
    merged = []
    for h in holes:
        if merged and h[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], h[1])
        else:
            merged.append(h)
    merged.append([EXTRA_FREE[0] & 0xFFFF, (EXTRA_FREE[1] - 1 & 0xFFFF) + 1])
    used = 0
    for i, b, jp, ko in rows:
        rec = record(where, b, ko)
        hole = next((h for h in merged if h[1] - h[0] >= len(rec)), None)
        if hole is None:
            raise SystemExit('titles: no room for record %02X (%d bytes)' % (i, len(rec)))
        pos = hole[0]
        hole[0] += len(rec)
        rom[f(0x840000 | pos):f(0x840000 | pos) + len(rec)] = rec
        pt = f(SET2) + 2 * i
        rom[pt] = pos & 0xFF
        rom[pt + 1] = pos >> 8
        used += len(rec)
    return len(comp), used, len(where)


def preview(path):
    rows = load_titles()
    where = plan(rows)
    rom = open(lz.ROM, 'rb').read()
    font = build_font(rom, where)
    from tiles import decode_tile
    pal = {0: (0, 0, 0), OUTLINE: (40, 40, 90)}
    for k in range(1, 7):
        v = 120 + k * 22
        pal[k] = (v, v, 255)

    def g16(t, cur_block):
        im = Image.new('RGB', (16, 16))
        for sub, (ox, oy) in zip((0, 1, 16, 17), ((0, 0), (8, 0), (0, 8), (8, 8))):
            tt = t + sub
            if tt >= 0x180:
                o = (tt - 0x180) * 32
            elif tt < 0x080:
                o = 0x1000 + tt * 32
            else:
                o = cur_block * 0x1000 + (tt - 0x080) * 32
            px = decode_tile(font, o, 4)
            for y in range(8):
                for x in range(8):
                    im.putpixel((ox + x, oy + y), pal.get(px[y][x], (255, 0, 0)))
        return im
    sheet = Image.new('RGB', (256 * 2, 28 * ((len(rows) + 1) // 2)))
    for k, (i, b, jp, ko) in enumerate(rows):
        rec = record(where, b, ko)
        im = Image.new('RGB', (256, 28))
        for j in range(rec[0]):
            t, a, dy, dx = rec[1 + 4 * j:5 + 4 * j]
            t |= (a & 1) << 8
            dx = dx - 256 if dx > 127 else dx
            im.paste(g16(t, b), (128 + dx, 6))
        sheet.paste(im, ((k % 2) * 256, (k // 2) * 28))
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sheet.save(path)
    print(len(rows), 'titles,', len(where), 'glyph placements')


if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        preview(sys.argv[2])
