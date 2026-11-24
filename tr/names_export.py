"""python tr/names_export.py sys05  -> tr/sys05_names.tsv : label<TAB>JP<TAB>KO(3rd-game suggestion or empty)"""
import re, sys, os, json
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
d = json.load(open(os.path.join(ROOT, 'tr', 'srw3_names.json'), encoding='utf-8'))
f = sys.argv[1]
rows = []
lab = None
for ln in open(os.path.join(ROOT, 'script', f + '.txt'), encoding='utf-8'):
    m = re.match(r'\[(S[0-9A-F]{6})\]', ln)
    if m: lab = m.group(1)
    elif ln.startswith('JP:'):
        jp = ln[4:].rstrip('\n')
        rows.append('%s\t%s\t%s' % (lab, jp, d.get(jp.replace('{END}', ''), '')))
open(os.path.join(ROOT, 'tr', f + '_names.tsv'), 'w', encoding='utf-8', newline='\n').write('\n'.join(rows) + '\n')
print(len(rows))
