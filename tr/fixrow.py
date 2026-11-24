"""python tr/fixrow.py file.tsv LABEL 'old substring' 'new substring'  (replace inside one row)"""
import sys
p, lab, old, new = sys.argv[1:5]
rows = open(p, encoding='utf-8').read().split('\n')
for i, r in enumerate(rows):
    if r.startswith(lab + '\t'):
        assert old in r, 'not found in ' + lab
        rows[i] = r.replace(old, new, 1)
        break
else:
    raise SystemExit('no row ' + lab)
open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(rows))
