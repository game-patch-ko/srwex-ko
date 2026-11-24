"""Re-wrap dialogue lines that are too wide for the window.

  python tr/reflow.py [--battle] in.tsv [out.tsv]   (label<TAB>KO text; writes in place if no out)
  --battle: battle speech: 200/192px, 2 lines (EX: battle files decided after screen check)

A speech starts after {w}, {p} or {face:..}. Only speeches with a line wider than the limit
(first line 240px incl. speaker name, others 232px; $0E34 = 60 units) are re-wrapped: their {n} are removed
and words are packed greedily at spaces. Speeches that need more than MAX_LINES lines
are reported so they can be shortened or split with {w}.
Widths: hangul 12px, everything else 8px (same rule as build/srwtext.py).
"""
import re
import sys

FIRST, CONT, MAX_LINES = 240, 232, 3
TAG = re.compile(r'(\{[^}]*\})')


def cw(c):
    return 12 if '가' <= c <= '힣' else 8


NAME_PX = 48   # {name:01..06} inserts a name at run time (4 hangul; see build/srwtext.py)


def width(s):
    return sum(cw(c) for c in TAG.sub('', s)) + NAME_PX * len(re.findall(r'\{name:0[1-6]\}', s))


def wrap(text):
    """text: one speech without {w}/{face}; may contain {n} and other tags. returns (text, nlines)"""
    lines = text.split('{n}')
    if all(width(l) <= (FIRST if i == 0 else CONT) for i, l in enumerate(lines)):
        return text, len(lines)
    flat = ''
    for i, l in enumerate(lines):
        l = l.strip(' ') if i else l.rstrip(' ')
        if i and not (flat.endswith('・') or l.startswith('・')):
            flat += ' '
        flat += l
    flat = re.sub(r' {2,}', ' ', flat)
    words = flat.split(' ')
    out, cur = [], ''
    for w in words:
        lim = FIRST if not out else CONT
        cand = (cur + ' ' + w) if cur else w
        if width(cand) <= lim:
            cur = cand
            continue
        if cur:
            out.append(cur)
            cur = ''
        lim = FIRST if not out else CONT
        while width(w) > lim:              # no space to break at: hard break
            k = 0
            while width(w[:k + 1]) <= lim:
                k += 1
            out.append(w[:k]); w = w[k:]
            lim = CONT
        cur = w
    if cur:
        out.append(cur)
    return '{n}'.join(out), len(out)


def split_speech(p):
    """Name「A B」 -> Name「A」{w}Name「B」 at a sentence end, both halves <= MAX_LINES lines."""
    m = re.match(r'^([^「(]{1,12})([「(])(.*)([」)])$', p.replace('{n}', ' '))
    if not m:
        return None
    name, op, body, cl = m.groups()
    body = re.sub(r' {2,}', ' ', body).strip()
    cands = [k.end() for k in re.finditer(r'(?<=[.!?。]) |(?<=・・・) ', body)]
    best = None
    for k in cands:
        a, b = body[:k].rstrip().rstrip('.'), body[k:].lstrip()
        ta, na = wrap(name + op + a + cl)
        tb, nb = wrap(name + op + b + cl)
        if na <= MAX_LINES and nb <= MAX_LINES:
            score = abs(width(a) - width(b))
            if best is None or score < best[0]:
                best = (score, ta + '{w}' + tb)
    return best[1] if best else None


def reflow(ko, label=''):
    parts = re.split(r'((?:\{w\}|\{p\})+(?:\{face:[0-9A-Fa-f]{2}\})?|\{face:[0-9A-Fa-f]{2}\})', ko)
    res = []
    for i, p in enumerate(parts):
        if i % 2:
            res.append(p)
            continue
        end = ''
        m = re.search(r'(\{END\}|\{goto:[^}]*\})$', p)
        if m:
            end = m.group(1); p = p[:m.start()]
        t, n = wrap(p)
        if n > MAX_LINES:
            s = split_speech(p)
            if s:
                t = s
            else:
                print('  LONG %s: %d lines: %s' % (label, n, t), file=sys.stderr)
        res.append(t + end)
    return ''.join(res)


if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--battle':
        args = args[1:]
        FIRST, CONT, MAX_LINES = 200, 192, 2
    src = args[0]
    dst = args[1] if len(args) > 1 else src
    rows = []
    for ln in open(src, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if '\t' in ln:
            l, t = ln.split('\t', 1)
            rows.append(l + '\t' + reflow(t, l))
        elif ln:
            rows.append(ln)
    open(dst, 'w', encoding='utf-8', newline='\n').write('\n'.join(rows) + '\n')
