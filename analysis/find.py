import sys
from dec import ROM
inv={}
for line in open('srw3_jp.tbl',encoding='utf-8'):
    line=line.rstrip('\n')
    if '=' in line:
        k,v=line.split('=',1)
        if len(v)==1 and v not in inv: inv[v]=bytes.fromhex(k)
for w in sys.argv[1:]:
    pat=b''.join(inv[c] for c in w); hits=[]; i=ROM.find(pat)
    while i!=-1: hits.append(i); i=ROM.find(pat,i+1)
    print(w,pat.hex(),len(hits),' '.join('%06X'%h for h in hits[:25]))
