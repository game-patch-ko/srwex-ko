from dec import ROM, decode
def plaus(o):
    s,e=decode(o,maxlen=300)
    seg=ROM[o:e-1]
    if not s.endswith('<END>') or not seg: return False
    good=sum(1 for b in seg if b<=0xE7 or b in (0xF0,0xF1,0xF2,0xF3))
    return good==len(seg) and sum(1 for b in seg if 0x16<=b<=0xE5 or b in (0xF0,0xF1,0xF2))>=len(seg)*0.5
def scan(bank,minrun=6):
    base=bank*0x8000; res=[]; i=base
    while i<base+0x8000-1:
        j=i; tg=[]
        while j<base+0x8000-1:
            w=ROM[j]|ROM[j+1]<<8
            if w<0x8000: break
            t=base+w-0x8000
            if not (ROM[t-1]==0xFF and plaus(t)): break
            tg.append(t); j+=2
        if len(tg)>=minrun: res.append((i,len(tg),tg)); i=j
        else: i+=1
    return res
if __name__=='__main__':
    import sys
    allt={}
    for bank in range(0,8):
        for T,n,tg in scan(bank):
            u=sorted(set(tg)); size=sum(decode(t)[1]-t for t in u)
            print('$%02X table %06X n=%3d uniq=%3d bytes=%5d first=%s'%(0x80+bank,T,n,len(u),size,decode(tg[0])[0][:14].replace('\n','/')))
