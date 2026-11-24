from dec import ROM, decode
def snes(o): return 0x8000+(o%0x8000)
def find_blocks(banks=(8,9,10,11,12)):
    res=[]
    for bk in banks:
        base=bk*0x8000
        for T in range(base,base+0x8000-4):
            if T>base and ROM[T-1]!=0xFF: continue   # tables follow an FF (or bank start)
            w=ROM[T]|ROM[T+1]<<8
            n2=w-snes(T)
            if n2<8 or n2>0x400 or n2%2: continue
            n=n2//2
            ws=[ROM[T+2*i]|ROM[T+2*i+1]<<8 for i in range(n)]
            nz=[x for x in ws if x]
            if any(x<w for x in nz): continue
            ws=nz
            if min(ws)!=w: continue
            # all targets must begin after an FF or be the first string
            tg=[base+x-0x8000 for x in ws]
            bad=sum(1 for t in tg if not (t==T+n2 or ROM[t-1] in (0xFF,0xF4)))
            if bad>len(tg)//10: continue
            if len(set(ws))>=3: res.append((T,n))
    return res
if __name__=='__main__':
    tot=0
    for T,n in find_blocks():
        base=T//0x8000*0x8000
        ws=[ROM[T+2*i]|ROM[T+2*i+1]<<8 for i in range(n)]; ws=[x for x in ws if x]
        u=sorted(set(ws)); last=base+u[-1]-0x8000; end=decode(last)[1]
        print('block %06X ($%02X:%04X) entries %3d unique %3d  text %06X-%06X'%(T,0x80+T//0x8000,snes(T),n,len(u),T+2*n,end))
