import collections
from dec import ROM, decode
stats=collections.Counter(); ctx=collections.defaultdict(list)
summary=[]
for bank in (8,9,10,11):
    base=bank*0x8000; first=ROM[base]|ROM[base+1]<<8; n=(first-0x8000)//2
    ptrs=[ROM[base+2*i]|ROM[base+2*i+1]<<8 for i in range(n)]
    uniq=sorted(set(ptrs)); covered=set(); total=0
    with open('script_bank%02X.txt'%(0x80+bank),'w',encoding='utf-8') as f:
        for idx,p in enumerate(ptrs):
            o=base+(p-0x8000)
            if p<0x8000 or o>=base+0x8000: f.write('#%03X ptr %04X (invalid)\n'%(idx,p)); continue
            s,e=decode(o)
            if p not in covered:
                covered.add(p); total+=e-o
                i=o
                while i<e:
                    b=ROM[i]
                    if b in (0xF0,0xF1,0xF2): i+=2; continue
                    if b>=0xF4 and b!=0xFF:
                        stats[b]+=1
                        if len(ctx[b])<4: ctx[b].append('%06X %s'%(i,ROM[i:i+4].hex(' ')))
                    i+=1
            f.write('#%03X $%02X:%04X (file %06X)\n%s\n\n'%(idx,0x88+bank-8,p,o,s))
    endmax=max(decode(base+(p-0x8000))[1] for p in uniq if p>=0x8000)
    summary.append('bank $%02X: %d ptrs (%d unique), text bytes %d, last text end file %06X (free %d bytes)'%(0x80+bank,n,len(uniq),total,endmax,base+0x8000-endmax))
print('\n'.join(summary))
for b in sorted(stats): print('%02X x%d  %s'%(b,stats[b],' | '.join(ctx[b])))
