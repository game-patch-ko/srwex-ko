"""Check translation rows before applying them.

  python tr/check_tsv.py tr/x.tsv [more.tsv ...]

For each row (label<TAB>KO):
  - label exists in script/*.txt
  - tags other than {n} and {w} appear in the same order as in JP
    ({w}/{p} may be added to split a long speech; {n} is free)
  - every hangul is in KS X 1001 (the 2,350 that EUC-KR can encode)
  - no kana / kanji left (they would show as wrong glyphs)
Exit code 1 if anything is wrong.
"""
import glob
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TAG = re.compile(r'\{[^}]*\}')


def load_jp():
    jp = {}
    for f in glob.glob(os.path.join(ROOT, 'script', '*.txt')):
        lab = None
        for ln in open(f, encoding='utf-8'):
            m = re.match(r'\[(S[0-9A-F]{6})\]', ln)
            if m:
                lab = m.group(1)
            elif ln.startswith('JP:') and lab:
                jp[lab] = (os.path.basename(f), ln[4:].rstrip('\n'))
    return jp


def tags(s):
    return [t for t in TAG.findall(s) if t not in ('{n}', '{w}', '{p}')]


def bad_chars(s):
    out = []
    for c in TAG.sub('', s):
        o = ord(c)
        if 0xAC00 <= o <= 0xD7A3:
            try:
                assert len(c.encode('euc-kr')) == 2
            except (UnicodeEncodeError, AssertionError):
                out.append(c + '(not KS X 1001)')
        elif 0x3041 <= o <= 0x30F6 and c not in 'ー':
            out.append(c + '(kana)')
        elif 0x4E00 <= o <= 0x9FFF:
            out.append(c + '(kanji)')
    return out


def main():
    jp = load_jp()
    nerr = 0
    for p in sys.argv[1:]:
        for i, ln in enumerate(open(p, encoding='utf-8'), 1):
            ln = ln.rstrip('\n')
            if not ln.strip():
                continue
            if '\t' not in ln:
                print('%s:%d: no TAB' % (p, i)); nerr += 1; continue
            lab, ko = ln.split('\t', 1)
            if lab not in jp:
                print('%s:%d: unknown label %s' % (p, i, lab)); nerr += 1; continue
            if tags(ko) != tags(jp[lab][1]):
                print('%s:%d: %s tags differ\n   JP %s\n   KO %s' % (p, i, lab, tags(jp[lab][1]), tags(ko))); nerr += 1
            b = bad_chars(ko)
            if b:
                print('%s:%d: %s bad chars: %s' % (p, i, lab, ' '.join(b))); nerr += 1
    print('%d problem(s)' % nerr)
    sys.exit(1 if nerr else 0)


if __name__ == '__main__':
    main()
