"""Pointer census for SRW3 text. Writes pointers.csv and prints coverage."""
from dec import ROM, decode
import collections, csv
TB=(0x40000,0x41293,0x41AF6,0x4500F,0x48000,0x4CA78,0x50000,0x53BCA,0x58000,0x5AC60,0x5E1A3,0x5F3AF,0x65F32)
TBN={0x40000:64,0x41293:80,0x5F3AF:144,0x65F32:177}
CMDIDX=(0x4031E,177)
def f(bank,w): return bank*0x8000+w-0x8000
refs=[]   # (ptr_location, kind, target)
tables=set(TB)|{CMDIDX[0]}
def add(loc,kind,bank,w):
    t=f(bank,w)
    if t in tables: return   # unused entry pointing at next table
    refs.append((loc,kind,t))
for T in TB:
    n=TBN.get(T,256); bank=T//0x8000
    for i in range(n):
        w=ROM[T+2*i]|ROM[T+2*i+1]<<8
        if w>=0x8000: add(T+2*i,'table',bank,w)
def cmd(o,bank,loc_kind):
    # FA xx then F7 n ptr*n | F9 ptr
    b=ROM[o+2]
    if b==0xF7:
        for k in range(ROM[o+3]): add(o+4+2*k,'quote',bank,ROM[o+4+2*k]|ROM[o+5+2*k]<<8)
    elif b==0xF9: add(o+3,'quote',bank,ROM[o+3]|ROM[o+4]<<8)
T,n=CMDIDX
for i in range(n):
    w=ROM[T+2*i]|ROM[T+2*i+1]<<8; cmd(f(8,w),8,'quote')
# recursive walk of strings
seen=set(); spans={}; ctrl=collections.Counter()
queue=[r[2] for r in refs]
while queue:
    t=queue.pop()
    if t in seen: continue
    seen.add(t); bank=t//0x8000; i=t
    while True:
        c=ROM[i]
        if c==0xFF: i+=1; break
        if c in (0xF0,0xF1,0xF2): i+=2; continue
        if c in (0xF3,0xF4): i+=1; continue
        if c in (0xFA,0xFD): ctrl[c]+=1; i+=2; continue
        if c in (0xF6,0xFB): ctrl[c]+=1; i+=3; continue
        if c==0xF9:
            ctrl[c]+=1; a=ROM[i+1]|ROM[i+2]<<8
            if a>=0x8000:   # F9 pppp : unconditional jump (handler 81:873E)
                add(i+1,'F9jump',bank,a); queue.append(f(bank,a)); i+=3; break
            w=ROM[i+3]|ROM[i+4]<<8; add(i+3,'F9cond',bank,w); queue.append(f(bank,w)); i+=5; continue
        if c==0xF7:
            ctrl[c]+=1; m=ROM[i+1]
            for k in range(m):
                w=ROM[i+2+2*k]|ROM[i+3+2*k]<<8; add(i+2+2*k,'F7rand',bank,w); queue.append(f(bank,w))
            i+=2+2*m; continue
        if c>=0xF4: ctrl[c]+=1; i+=1; continue
        i+=1
    spans[t]=i
# coverage
cov=bytearray(len(ROM))
for t,e in spans.items():
    for x in range(t,e): cov[x]=1
cov[0x4031E:0x40480]=b""*(0x40480-0x4031E)
for T in TB: cov[T:T+2*TBN.get(T,256)]=b'\x02'*(2*TBN.get(T,256))
if __name__=='__main__':
    kinds=collections.Counter(k for _,k,_ in refs)
    print('pointers:',len(refs),dict(kinds),' strings:',len(spans),' text bytes:',sum(e-t for t,e in spans.items()))
    print('ctrl',{('%02X'%k):v for k,v in ctrl.items()})
    with open('pointers.csv','w',newline='',encoding='utf-8') as fp:
        wr=csv.writer(fp); wr.writerow(['ptr_file','kind','target_file','target_snes','preview'])
        for loc,k,t in sorted(refs):
            wr.writerow(['%06X'%loc,k,'%06X'%t,'$%02X:%04X'%(0x80+t//0x8000,0x8000+t%0x8000),decode(t)[0][:30].replace('\n','/')])
    # uncovered text-like runs in banks 88-8C
    import textwrap
    run=None; out=[]
    for i in range(0x40000,0x68000):
        tx= cov[i]==0 and (0x40<=ROM[i]<=0xDF or ROM[i] in (0xF0,0xF1,0xF2,0x3E,0x3F,0x3B))
        if tx and run is None: run=i
        if not tx and run is not None:
            if i-run>=12: out.append((run,i))
            run=None
    print('uncovered text-like runs (>=12B):',len(out),'bytes',sum(b-a for a,b in out))
    for a,b in out[:40]: print('  %06X-%06X %s'%(a,b,decode(a)[0][:40].replace('\n','/')))
