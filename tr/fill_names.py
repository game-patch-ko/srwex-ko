"""python tr/fill_names.py sys06 tr/names_sys06.txt : fill empty KO column of tr/<f>_names.tsv from JP=KO lines"""
import sys, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
f, src = sys.argv[1], sys.argv[2]
d = {}
for ln in open(src, encoding='utf-8'):
    ln = ln.rstrip('\n')
    if '=' in ln and not ln.startswith('#'):
        k, v = ln.split('=', 1); d[k] = v
p = os.path.join(ROOT, 'tr', f + '_names.tsv')
rows = [ln.rstrip('\n').split('\t') for ln in open(p, encoding='utf-8') if ln.strip()]
miss = []
for r in rows:
    jp = r[1].replace('{END}', '')
    if jp in d:
        r[2] = d[jp]
    if not r[2] and jp and not set(jp) <= set('ー'):
        miss.append(jp)
open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join('\t'.join(r) for r in rows) + '\n')
print('missing:', ' '.join(miss))
