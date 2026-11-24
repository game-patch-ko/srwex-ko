"""LZ decompressor of SRW3 ($80:885A).  python lz.py <snes_src_hex> [out.bin]

Bit stream: control bytes read MSB first, refilled every 8 bits.
  1                 -> literal byte
  0 0 b b  off8     -> copy len = 2 + bb from dst + (off8 | 0xFF00)       (offset -256..-1)
  0 1      word     -> w = word (big-endian: first byte high); off = (w >> 3) | 0xE000;
                       len = w & 7; if len == 0: len = next byte, 0 = end; else len += 2
                       (the long form adds 1 more when the length byte path is taken: see code)
Returns (data, compressed size).
"""
import os
import sys

ROM = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Super Robot Taisen EX (J).smc')


def s2f(a):
    return ((a >> 16) & 0x7F) * 0x8000 + (a & 0x7FFF)


def decompress(rom, src):
    p = s2f(src)
    start = p
    out = bytearray()
    bits = 0
    nbits = 0

    def bit():
        nonlocal bits, nbits, p
        if nbits == 0:
            bits = rom[p]; p += 1; nbits = 8
        b = (bits >> 7) & 1
        bits = (bits << 1) & 0xFF
        nbits -= 1
        return b

    while True:
        if bit():
            out.append(rom[p]); p += 1
            continue
        if not bit():
            n = (bit() << 1) | bit()
            off = rom[p] - 0x100; p += 1
            length = n + 2
        else:
            w = (rom[p] << 8) | rom[p + 1]; p += 2
            off = ((w >> 3) | 0xE000) - 0x10000
            length = w & 7
            if length == 0:
                length = rom[p]; p += 1
                if length == 0:
                    break
                length += 1
            else:
                length += 2
        for _ in range(length):
            out.append(out[len(out) + off])
    return bytes(out), p - start


if __name__ == '__main__':
    rom = open(ROM, 'rb').read()
    data, size = decompress(rom, int(sys.argv[1], 16))
    print('out %d bytes, compressed %d bytes' % (len(data), size))
    if len(sys.argv) > 2:
        open(sys.argv[2], 'wb').write(data)
