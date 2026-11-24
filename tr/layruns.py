"""Window layouts: translate only the text runs between tags.
  python tr/layruns.py export lay01 > tr/lay01_runs.txt   (label<TAB>idx<TAB>width<TAB>JP run)
  python tr/layruns.py build tr/lay01_runs.txt tr/lay01_ko.txt tr/lay01.tsv
     ko file: one line per run, same order as the runs file ('=' keeps the JP run)
"""
import re, sys, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TAG = re.compile(r'(\{[^}]*\})')


def w(s):
    return sum(12 if ('가' <= c <= '힣' or '\u4e00' <= c <= '\u9fff' or c == '\u3000') else 8 for c in s)


def segs(f):
    lab = None
    for ln in open(os.path.join(ROOT, 'script', f + '.txt'), encoding='utf-8'):
        m = re.match(r'\[(S[0-9A-F]{6})\]', ln)
        if m: lab = m.group(1)
        elif ln.startswith('JP:'): yield lab, ln[4:].rstrip('\n')


if sys.argv[1] == 'export':
    for lab, jp in segs(sys.argv[2]):
        parts = TAG.split(jp)
        k = 0
        for p in parts:
            if p and not TAG.fullmatch(p):
                print('%s\t%d\t%d\t%s' % (lab, k, w(p), p)); k += 1
else:
    runs = [ln.rstrip('\n').split('\t') for ln in open(sys.argv[2], encoding='utf-8') if ln.strip()]
    ko = [ln.rstrip('\n') for ln in open(sys.argv[3], encoding='utf-8')]
    assert len(ko) >= len(runs), (len(ko), len(runs))
    f = os.path.basename(sys.argv[2]).split('_')[0]
    jp = dict(segs(f))
    rep = {}
    for r, k in zip(runs, ko):
        rep.setdefault(r[0], []).append(r[3] if k == '=' else k)
    out = []
    for lab, s in jp.items():
        if lab not in rep: continue
        parts = TAG.split(s); it = iter(rep[lab]); res = ''
        for p in parts:
            res += p if (not p or TAG.fullmatch(p)) else next(it)
        for r, k in zip(runs, ko):
            if r[0] == lab and k != '=' and w(k) > int(r[2]):
                print('WIDE %s run %s: %dpx > %spx  %s' % (lab, r[1], w(k), r[2], k), file=sys.stderr)
        if res != s: out.append(lab + '\t' + res)
    open(sys.argv[4], 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
    print(len(out), 'segments')
