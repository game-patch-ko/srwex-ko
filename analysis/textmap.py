from dec import ROM
# score: proportion of bytes that look like script (kana 40-DF, kanji prefix F0-F2, F3, FF, 3A-3F, 00)
B=256; flags=[]
for o in range(0,len(ROM),B):
    blk=ROM[o:o+B]
    kana=sum(1 for b in blk if 0x40<=b<=0xDF)
    pre=sum(1 for i in range(len(blk)-1) if blk[i] in (0xF0,0xF1,0xF2))
    term=blk.count(0xFF); punct=sum(blk.count(x) for x in (0x3E,0x3F,0x3B,0x15,0x14))
    s=kana/B
    flags.append(s>0.55 and term>=1 and blk.count(0)<B*0.25)
runs=[];start=None
for i,f in enumerate(flags+[False]):
    if f and start is None: start=i
    if not f and start is not None:
        if i-start>=2: runs.append((start*B,i*B))
        start=None
for a,b in runs: print('%06X-%06X ($%02X:%04X) %6d bytes'%(a,b,0x80+a//0x8000,0x8000+a%0x8000,b-a))
