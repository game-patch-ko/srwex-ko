"""Re-decode JP: lines of script/*.txt with the current table (KO lines untouched)."""
import os, re, sys, tempfile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'build'))
import srwtext as S
tmp = tempfile.mkdtemp()
S.SCRIPT_DIR = tmp
S.write_scripts(S.discover(open(S.SRC, 'rb').read()), force=True)
n = 0
for fn in os.listdir(tmp):
    new = {}
    lab = None
    for ln in open(os.path.join(tmp, fn), encoding='utf-8'):
        m = re.match(r'\[(S[0-9A-F]{6})\]', ln)
        if m: lab = m.group(1)
        elif ln.startswith('JP:'): new[lab] = ln
    p = os.path.join(ROOT, 'script', fn)
    L = open(p, encoding='utf-8').read().split('\n')
    lab = None
    for i, ln in enumerate(L):
        m = re.match(r'\[(S[0-9A-F]{6})\]', ln)
        if m: lab = m.group(1)
        elif ln.startswith('JP:') and new.get(lab, ln + '\n').rstrip('\n') != ln:
            L[i] = new[lab].rstrip('\n'); n += 1
    open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
print(n, 'JP lines updated')
