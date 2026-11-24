"""python tr/export_todo.py dlg06 > out.txt : untranslated segments (label<TAB>JP), skipping {END}-only and {rand}-only"""
import re, sys, os
f = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'script', sys.argv[1] + '.txt')
l = jp = None
for ln in open(f, encoding='utf-8'):
    m = re.match(r'\[(S[0-9A-F]{6})\]', ln)
    if m: l = m.group(1)
    elif ln.startswith('JP:'): jp = ln[4:].rstrip('\n')
    elif ln.startswith('KO:') and ln.strip() == 'KO:' and jp != '{END}' and not re.fullmatch(r'\{rand:[^}]*\}', jp):
        sys.stdout.buffer.write((l + '\t' + jp + '\n').encode('utf-8'))
