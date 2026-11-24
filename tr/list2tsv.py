"""python tr/list2tsv.py sys17 tr/sys17_list.txt tr/sys17.tsv
One KO per line, in export_todo order; '=' keeps the original. Adds {END}. Prints widths vs original."""
import re, subprocess, sys, os
name, lst, out = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(__file__))
todo = subprocess.run([sys.executable, os.path.join(here, 'export_todo.py'), name], capture_output=True).stdout.decode('utf-8').splitlines()
ko = [x.rstrip('\n') for x in open(lst, encoding='utf-8') if x.strip()]
assert len(ko) == len(todo), (len(ko), len(todo))
def w(s):
    s = re.sub(r'\{[^}]*\}|\[AL\]|\[L\]', '', s)
    return sum(12 if ('가' <= c <= '힣' or '一' <= c <= '鿿') else 8 for c in s)
rows = []
for t, k in zip(todo, ko):
    lab, jp = t.split('\t', 1)
    if k == '=':
        continue
    if w(k) > w(jp):
        print('wider %3d > %3d  %s  (%s)' % (w(k), w(jp), k, jp.replace('{END}', '')))
    rows.append(lab + '\t' + k + '{END}')
open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(rows) + '\n')
print(len(rows), 'rows')
