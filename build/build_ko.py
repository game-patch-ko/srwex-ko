"""Hooks and font for the SRW EX Korean patch (called by srwtext.py build).

Steps
  1. expand 1.5MB -> 2MB (banks $B0-$BF)
  2. prefix decode: EC-EF and F0-F3 are 2-byte prefixes (internal code hi = prefix - $EB, 1..8)
       dialogue  $81:85E6   (originally EC-EF = end of string, F0-F3 kanji)
       window text mode $80:B9BD (originally EC-EF = icon glyphs, F0-F3 kanji)
  3. glyph routine: codes >= $100 read the hangul font ($B1:8000 + slot*32)
       $80:BADF (window path) and $80:BC75 (dialogue path) -> JML to hooks in bank $B0
  4. 1-byte font ($20:E1BC): . and , drawn over 。(E4) and 、(3A); the icon glyphs EC-EF are
     copied to free 1-byte codes (ICON_MAP) because EC-EF are hangul prefixes now
  5. hangul font, header checksum
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'Super Robot Taisen EX (J).smc')

CODE_BANK = 0xB0
FONT_BANK = 0xB1
FONT1 = 0x1061BC          # $20:E1BC 1-byte font, 16 bytes per code
# layout icon glyphs EC..EF move to these 1-byte codes (unused in the original text)
ICON_MAP = {0xEC: 0x03, 0xED: 0x04, 0xEE: 0x0C, 0xEF: 0x61}   # codes unused by all extracted text (census 2026-11-24)


def s2f(a):
    return ((a >> 16) & 0x7F) * 0x8000 + ((a & 0xFFFF) - 0x8000)


class Asm:
    """Tiny assembler: raw bytes, labels and 8-bit relative branches."""
    def __init__(self, org):
        self.org = org
        self.buf = bytearray()
        self.labels = {}
        self.fix = []

    def pc(self):
        return self.org + len(self.buf)

    def label(self, name):
        self.labels[name] = self.pc()

    def b(self, *bs):
        for x in bs:
            if isinstance(x, (bytes, bytearray)):
                self.buf += x
            else:
                self.buf.append(x)

    def br(self, op, name):
        self.buf += bytes([op, 0])
        self.fix.append((len(self.buf) - 1, name))

    def long(self, op, addr):
        self.buf += bytes([op, addr & 0xFF, (addr >> 8) & 0xFF, addr >> 16])

    def done(self):
        for pos, name in self.fix:
            d = self.labels[name] - (self.org + pos + 1)
            assert -128 <= d <= 127, name
            self.buf[pos] = d & 0xFF
        return bytes(self.buf)


def glyph_hook(a, name, back):
    """entered by JML with A = glyph code (>= $100), m16/x16, X = tile position (kept).
    Points the 2-byte font pointers $F4/$F7/$FA/$FD at the hangul glyph, Y = 0, JML back."""
    a.label(name)
    a.b(0x38, 0xE9, 0x00, 0x01)        # SEC / SBC #$0100  -> slot
    a.b(0x48)                          # PHA
    a.b(0xEB, 0x29, 0xFF, 0x00)        # XBA / AND #$00FF
    a.b(0x4A, 0x4A)                    # LSR / LSR          -> slot >> 10
    a.b(0x18, 0x69, FONT_BANK, 0x00)   # CLC / ADC #FONT_BANK
    a.b(0xE2, 0x20)                    # SEP #$20
    a.b(0x85, 0xF6, 0x85, 0xF9, 0x85, 0xFC, 0x85, 0xFF)
    a.b(0xC2, 0x20)                    # REP #$20
    a.b(0x68)                          # PLA
    a.b(0x29, 0xFF, 0x03)              # AND #$03FF
    a.b(0x0A, 0x0A, 0x0A, 0x0A, 0x0A)  # ASL x5
    a.b(0x09, 0x00, 0x80)              # ORA #$8000
    a.b(0x85, 0xF4, 0x18)              # STA $F4 / CLC
    a.b(0x69, 0x08, 0x00, 0x85, 0xF7)  # ADC #8 / STA $F7
    a.b(0x69, 0x08, 0x00, 0x85, 0xFA)
    a.b(0x69, 0x08, 0x00, 0x85, 0xFD)
    a.b(0xA0, 0x00, 0x00)              # LDY #$0000
    a.long(0x5C, back)                 # JML back


def build_hooks():
    a = Asm(CODE_BANK << 16 | 0x8000)
    glyph_hook(a, 'glyph_win', 0x00BB9E)   # after TAY at $80:BB9D
    glyph_hook(a, 'glyph_dlg', 0x00BD5A)   # after TAY at $80:BD59
    return a.done(), a.labels


def patch(rom, snes, old, new):
    o = s2f(snes)
    assert rom[o:o + len(old)] == bytes(old), ('%06X' % snes, rom[o:o + len(old)].hex(), bytes(old).hex())
    assert len(new) == len(old)
    rom[o:o + len(new)] = bytes(new)


def jml(addr):
    return [0x5C, addr & 0xFF, (addr >> 8) & 0xFF, addr >> 16]


def fix_checksum(rom):
    hdr = 0x7FC0
    rom[hdr + 0x1C:hdr + 0x20] = b'\xFF\xFF\x00\x00'
    s = sum(rom) & 0xFFFF
    rom[hdr + 0x1E] = s & 0xFF
    rom[hdr + 0x1F] = s >> 8
    c = s ^ 0xFFFF
    rom[hdr + 0x1C] = c & 0xFF
    rom[hdr + 0x1D] = c >> 8
    return s


def build(font):
    """returns the hooked 2MB ROM (bytearray); font = hangul glyph data (32 bytes per slot)"""
    rom = bytearray(open(SRC, 'rb').read())
    assert len(rom) == 0x180000
    rom += b'\xFF' * (0x200000 - len(rom))
    assert rom[0x7FD7] == 0x0B   # header ROM size already says 2MB

    code, L = build_hooks()
    co = s2f(CODE_BANK << 16 | 0x8000)
    rom[co:co + len(code)] = code

    # dialogue: EC-F3 prefix (was: EC-EF end, F0-F3 kanji)
    patch(rom, 0x8185E6,
          [0xC9, 0xF0, 0x00, 0x90, 0x41, 0xC9, 0xF4, 0x00, 0xB0, 0x34, 0x29, 0x03, 0x00, 0x1A],
          [0xC9, 0xF4, 0x00, 0xB0, 0x37, 0x38, 0xE9, 0xEB, 0x00, 0xEA, 0xEA, 0xEA, 0xEA, 0xEA])
    # window text mode: EC-F3 prefix (was: EC-EF icons, F0-F3 kanji)
    patch(rom, 0x80B9BD,
          [0xC9, 0xF0, 0x00, 0x90, 0x3D, 0x1A, 0x29, 0x0F, 0x00, 0x85, 0x00],
          [0xC9, 0xEC, 0x00, 0x90, 0x3D, 0x38, 0xE9, 0xEB, 0x00, 0x85, 0x00])
    # glyph routine, 2-byte codes
    patch(rom, 0x80BADF, [0xE9, 0x00, 0x01, 0x4C, 0x94, 0xBB], jml(L['glyph_win']) + [0xEA, 0xEA])
    patch(rom, 0x80BC75, [0xE9, 0x00, 0x01, 0x4C, 0x54, 0xBD], jml(L['glyph_dlg']) + [0xEA, 0xEA])

    # 1-byte glyphs: icons to free codes, then Korean punctuation over 。 and 、
    for old, new in ICON_MAP.items():
        rom[FONT1 + new * 16:FONT1 + new * 16 + 16] = rom[FONT1 + old * 16:FONT1 + old * 16 + 16]
    PUNCT = {0xE4: {12: 0x60, 13: 0x60},
             0x3A: {11: 0x60, 12: 0x60, 13: 0x20, 14: 0x40}}
    for c, rows in PUNCT.items():
        o = FONT1 + c * 16
        rom[o:o + 16] = bytes(rows.get(y, 0) for y in range(16))

    assert len(font) <= 0x10000
    fo = s2f(FONT_BANK << 16 | 0x8000)
    rom[fo:fo + len(font)] = font
    return rom, L
