"""python tr/apply_names.py : tr/*_names.tsv (label, JP, KO) -> script KO lines (adds {END} like JP)"""
import glob, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'build'))
import setko
pairs = []
for p in sorted(glob.glob(os.path.join(ROOT, 'tr', '*_names.tsv'))):
    for ln in open(p, encoding='utf-8'):
        r = ln.rstrip('\n').split('\t')
        if len(r) < 3 or not r[2]:
            continue
        ko = r[2]
        if r[1].endswith('{END}') and not ko.endswith('{END}'):
            ko += '{END}'
        pairs.append((r[0], ko))
setko.set_many(pairs)
