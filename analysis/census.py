from dec import ROM, decode
import collections
def snes2file(bank,w): return bank*0x8000+(w-0x8000)
# 1) table blocks: (file offset, entries)
BLOCKS=[(0x40000,64),(0x4031E,177,'cmd'),(0x41293,80),(0x41AF6,256),(0x4500F,256),(0x48000,256),(0x4CA78,256),
        (0x50000,256),(0x58000,256),(0x5AC60,256),(0x5E1A3,256),(0x63D77,128),(0x65F32,177)]
def table_entries():
    out=[]
    for b in BLOCKS:
        T,n=b[0],b[1]; bank=T//0x8000
        for i in range(n):
            w=ROM[T+2*i]|ROM[T+2*i+1]<<8
            if w>=0x8000: out.append((T+2*i,bank,w,len(b)>2))
    return out
def parse_cmd(o,bank,refs,src):
    # battle quote command: FA xx (F7 n ptr*n | F9 ptr)
    if ROM[o]!=0xFA: return False
    b=ROM[o+2]
    if b==0xF7:
        n=ROM[o+3]
        for k in range(n): refs.append((o+4+2*k,bank,ROM[o+4+2*k]|ROM[o+5+2*k]<<8,'quote'))
    elif b==0xF9: refs.append((o+3,bank,ROM[o+3]|ROM[o+4]<<8,'quote'))
    return True
refs=[]
for (po,bank,w,iscmd) in table_entries():
    t=snes2file(bank,w)
    if iscmd or ROM[t]==0xFA and ROM[t+2] in (0xF7,0xF9):
        if parse_cmd(t,bank,refs,po): continue
    refs.append((po,bank,w,'table'))
if __name__=='__main__':
    ctl=collections.defaultdict(collections.Counter)
    targets=set(snes2file(b,w) for _,b,w,_ in refs)
    for t in sorted(targets):
        i=t
        while ROM[i]!=0xFF and i<t+2000:
            c=ROM[i]
            if c in (0xF0,0xF1,0xF2): i+=2; continue
            if c>=0xF4: ctl[c][ROM[i+1:i+4].hex(' ')]+=1
            i+=1
    print(len(refs),'refs',len(targets),'unique targets')
    for c in sorted(ctl): print('%02X'%c, sum(ctl[c].values()), ctl[c].most_common(8))
