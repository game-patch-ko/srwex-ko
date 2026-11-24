"""Find speeches whose first line is widened by text from a preceding fall-through segment (e.g. a speaker name).
For every segment A with '-> B' (falls through into B), the last line of A's KO joins the first line of B's KO."""
import glob, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build'))
import srwtext as S
segs = {}
for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'script', 'dlg*.txt')):
    name = os.path.basename(f)[:-4]
    cur = None
    for ln in open(f, encoding='utf-8'):
        m = re.match(r'\[(S[0-9A-F]{6})\](?:\s*->\s*(S[0-9A-F]{6}))?', ln)
        if m:
            cur = m.group(1); segs[cur] = {'next': m.group(2), 'file': name}
        elif ln.startswith('KO:') and cur:
            segs[cur]['ko'] = ln[4:].rstrip('\n') if ln.startswith('KO: ') else ln[3:].rstrip('\n')
        elif ln.startswith('JP:') and cur:
            segs[cur]['jp'] = ln[4:].rstrip('\n')
def text(l):
    s = segs[l]; return s['ko'] if s.get('ko') else s['jp']
def lines(t):
    try:
        return S.dlg_lines(S.text_to_tokens(t, 'x'))
    except Exception:
        return None
bad = 0
for a, s in segs.items():
    b = s['next']
    if not b or b not in segs or not s['file'].startswith('dlg'):
        continue
    la, lb = lines(text(a)), lines(text(b))
    if la is None or lb is None:
        continue
    battle = s['file'] in S.BATTLE_GROUPS
    lim0, limc = (S.BTL_MAX_PX, S.BTL_CONT_PX) if battle else (S.DLG_MAX_PX, S.DLG_CONT_PX)
    li, wa = la[-1]
    lj, wb = lb[0]
    if lj != 0:            # B starts after a new speech/line: nothing joins
        continue
    w = wa + wb
    lim = lim0 if li == 0 else limc
    if w > lim:
        bad += 1
        print('%s %s+%s line %d: %dpx > %dpx  [%s|%s]' % (s['file'], a, b, li + 1, w, lim, text(a)[-30:], text(b)[:40]))
print(bad, 'joined line(s) too wide')
