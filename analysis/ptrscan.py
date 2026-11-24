from dec import ROM, decode
import collections
TEXTBANKS=[8,9,10,11,12]
def okchar(b): return b<=0xE7 or b in (0xF0,0xF1,0xF2,0xF3,0xF4,0xF9,0xFA,0xFB,0xFD)
def plausible(o):
    # decode until FF; require mostly kana/kanji and length>=2
    s,e=decode(o,maxlen=1200)
    if not s.endswith('<END>') : return False
    seg=ROM[o:e-1]
    if len(seg)<1: return False
    kana=sum(1 for b in seg if 0x40<=b<=0xE5 or b in (0xF0,0xF1,0xF2))
    bad=sum(1 for b in seg if b in (0xF5,0xF6,0xF7,0xF8,0xFC,0xFE))
    return bad==0 and kana>=len(seg)*0.4
starts={}
for bk in TEXTBANKS:
    base=bk*0x8000; st=set()
    for i in range(base+1,base+0x8000):
        if ROM[i-1]==0xFF and plausible(i): st.add(i)
    starts[bk]=st
# references: every byte offset in same bank whose word hits a start
refs=collections.defaultdict(list)  # target -> list of ref offsets
for bk in TEXTBANKS:
    base=bk*0x8000; st=starts[bk]
    for i in range(base,base+0x8000-1):
        w=ROM[i]|ROM[i+1]<<8
        if 0x8000<=w:
            t=base+w-0x8000
            if t in st: refs[t].append(i)
# tables: runs of consecutive words (step 2) hitting starts
tables=[]
for bk in TEXTBANKS:
    base=bk*0x8000; hit=set(r for t in starts[bk] for r in refs[t])
    i=base
    while i<base+0x8000:
        if i in hit:
            j=i
            while j in hit: j+=2
            if (j-i)//2>=4: tables.append((i,(j-i)//2)); i=j; continue
        i+=1
if __name__=='__main__':
    for bk in TEXTBANKS:
        print('bank $%02X: %d plausible string starts'%(0x80+bk,len(starts[bk])))
    for t,n in tables: print('table %06X ($%02X:%04X) %d entries'%(t,0x80+t//0x8000,0x8000+t%0x8000,n))
