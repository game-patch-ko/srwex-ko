"""render EX glyphs to PNG grid: python glyphimg.py one|kanji start count out.png [only-unmatched]"""
import sys, json
from PIL import Image, ImageDraw
b=open('../Super Robot Taisen EX (J).smc','rb').read()
def g1(c): return [b[0x20*0x8000+0x61BC+c*16+r]<<8 for r in range(16)]
def gk(i):
    p=0x21*0x8000+i*32; return [b[p+r]<<8|b[p+16+r] for r in range(16)]
kind,st,n,out=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3]),sys.argv[4]
items=list(range(st,st+n))
if len(sys.argv)>5:
    m=json.load(open('glyphmap.json'))
    if kind=='one': items=[c for c in items if m['o'].get(str(c)) is None]
    else: items=[c for c in items if str(c) not in m['k']]
S=4; cols=16; cw=16*S+8; ch=16*S+18
img=Image.new('RGB',(cols*cw,((len(items)+cols-1)//cols)*ch),'white'); d=ImageDraw.Draw(img)
for k,c in enumerate(items):
    x0=(k%cols)*cw; y0=(k//cols)*ch
    rows=g1(c) if kind=='one' else gk(c)
    d.text((x0+2,y0),'%X'%(c if kind=='one' else c+0x100+0xF000-0x100 if False else c),fill='red')
    for r,v in enumerate(rows):
        for i in range(16):
            if v>>(15-i)&1: d.rectangle([x0+i*S,y0+14+r*S,x0+i*S+S-1,y0+14+r*S+S-1],fill='black')
    d.rectangle([x0,y0+14,x0+16*S,y0+14+16*S],outline='#ccc')
img.save(out); print(len(items),'glyphs ->',out)
