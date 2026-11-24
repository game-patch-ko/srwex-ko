"""Set the KO line of a segment in script/*.txt.

  python setko.py S037510 "이동"
  python setko.py --file pairs.tsv      (label<TAB>text per line)
"""
import os
import re
import sys

SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'script')


def load():
    files = {}
    where = {}
    for fn in sorted(os.listdir(SCRIPT_DIR)):
        if fn.endswith('.txt'):
            lines = open(os.path.join(SCRIPT_DIR, fn), encoding='utf-8').read().split('\n')
            files[fn] = lines
            for i, ln in enumerate(lines):
                m = re.match(r'\[(S[0-9A-F]{6})\]', ln)
                if m:
                    where[m.group(1)] = (fn, i)
    return files, where


def set_many(pairs):
    files, where = load()
    touched = set()
    for label, text in pairs:
        if label not in where:
            raise SystemExit('unknown label ' + label)
        fn, i = where[label]
        lines = files[fn]
        j = i + 1
        while j < len(lines) and not lines[j].startswith('KO:') and not lines[j].startswith('['):
            j += 1
        if j >= len(lines) or not lines[j].startswith('KO:'):
            raise SystemExit('%s: segment %s has no KO: line' % (fn, label))
        lines[j] = 'KO: ' + text
        touched.add(fn)
    for fn in touched:
        open(os.path.join(SCRIPT_DIR, fn), 'w', encoding='utf-8', newline='\n').write('\n'.join(files[fn]))
    print('updated %d segment(s) in %s' % (len(pairs), ', '.join(sorted(touched))))


if __name__ == '__main__':
    if sys.argv[1] == '--file':
        pairs = [ln.rstrip('\n').split('\t', 1) for ln in open(sys.argv[2], encoding='utf-8') if '\t' in ln]
    else:
        pairs = [(sys.argv[1], sys.argv[2])]
    set_many(pairs)
