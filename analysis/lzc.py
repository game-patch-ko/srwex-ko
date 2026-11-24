"""LZ compressor for the SRW3 format decoded by analysis/lz.py ($80:885A).

  literal:      1, byte
  short match:  0 0 b b, off8      len 2..5, distance 1..256
  long match:   0 1, word(be)      w = (dist13 << 3) | (len - 2) for len 3..9   (dist13 = 0x2000 - distance)
                0 1, word, n       w low 3 bits 0, n = len - 1, len 2..256
  end:          0 1, word with low bits 0, n = 0
Control bits are packed MSB first into control bytes placed before the data they govern
(the decoder reads a control byte whenever it runs out of bits, interleaved with data).

  python lzc.py in.bin out.lz       compress
  python lzc.py --test <snes_src>   decompress ROM data, recompress, check round trip
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lz


class BitWriter:
    def __init__(self):
        self.out = bytearray()
        self.ctl_pos = None
        self.nbits = 8

    def bit(self, b):
        if self.nbits == 8:
            self.ctl_pos = len(self.out)
            self.out.append(0)
            self.nbits = 0
        if b:
            self.out[self.ctl_pos] |= 0x80 >> self.nbits
        self.nbits += 1

    def byte(self, v):
        self.out.append(v & 0xFF)


def compress(data):
    w = BitWriter()
    n = len(data)
    i = 0
    heads = {}
    while i < n:
        best_len, best_dist = 0, 0
        if i + 2 <= n:
            key = data[i:i + 2]
            for j in reversed(heads.get(key, [])):
                d = i - j
                if d > 0x2000:
                    break
                l = 2
                while l < 256 and i + l < n and data[j + l] == data[i + l]:
                    l += 1
                if l > best_len:
                    best_len, best_dist = l, d
                    if l == 256:
                        break
        # pick encoding
        if best_len >= 2 and best_dist <= 256 and best_len <= 5:
            w.bit(0); w.bit(0)
            w.bit((best_len - 2) >> 1); w.bit((best_len - 2) & 1)
            w.byte(0x100 - best_dist)
            step = best_len
        elif best_len >= 3:
            dist13 = 0x2000 - best_dist
            w.bit(0); w.bit(1)
            if best_len <= 9:
                v = (dist13 << 3) | (best_len - 2)
                w.byte(v >> 8); w.byte(v)
            else:
                v = dist13 << 3
                w.byte(v >> 8); w.byte(v); w.byte(best_len - 1)
            step = best_len
        else:
            w.bit(1)
            w.byte(data[i])
            step = 1
        for k in range(i, min(i + step, n - 1)):
            heads.setdefault(data[k:k + 2], []).append(k)
        i += step
    # end marker: long form with length byte 0 (distance irrelevant)
    w.bit(0); w.bit(1)
    w.byte(0xFF); w.byte(0xF8); w.byte(0)
    return bytes(w.out)


def decompress_bytes(blob):
    """decode a compressed blob that is not in the ROM"""
    fake = bytearray(blob) + b'\x00' * 4
    out, size = lz.decompress(fake, 0x008000 - 0x008000 + 0x8000)  # file offset 0 == SNES $00:8000
    return out, size


if __name__ == '__main__':
    if sys.argv[1] == '--test':
        rom = open(lz.ROM, 'rb').read()
        src = int(sys.argv[2], 16)
        orig, osize = lz.decompress(rom, src)
        c = compress(orig)
        back, _ = decompress_bytes(c)
        print('original compressed %d, ours %d, round trip %s' % (osize, len(c), back == orig))
    else:
        d = open(sys.argv[1], 'rb').read()
        c = compress(d)
        open(sys.argv[2], 'wb').write(c)
        back, _ = decompress_bytes(c)
        print('in %d -> %d bytes, round trip %s' % (len(d), len(c), back == d))
