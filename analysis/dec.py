import sys
ROM=open('../Super Robot Taisen EX (J).smc','rb').read()
tbl={}
for line in open('srw3_jp.tbl',encoding='utf-8'):
    line=line.rstrip('\n')
    if '=' in line:
        k,v=line.split('=',1); tbl[bytes.fromhex(k)]=v
def decode(o,end=None,maxlen=2000):
    out=[];i=o
    while i<len(ROM) and (end is None or i<end) and i-o<maxlen:
        b=ROM[i]
        if b in (0xF0,0xF1,0xF2):
            out.append(tbl.get(ROM[i:i+2],'{%02X%02X}'%(b,ROM[i+1]))); i+=2; continue
        if b==0xFF: out.append('<END>'); i+=1; break
        if b==0xF3: out.append('\n'); i+=1; continue
        if b>=0xF4: out.append('[%02X]'%b); i+=1; continue
        out.append(tbl.get(bytes([b]),'{%02X}'%b)); i+=1
    return ''.join(out),i
if __name__=='__main__':
    o=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 10
    for _ in range(n):
        s,e=decode(o); print('%06X: %s'%(o,s)); o=e
