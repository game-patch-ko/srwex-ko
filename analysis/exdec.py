import sys
R=open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'..','Super Robot Taisen EX (J).smc'),'rb').read()
T={}
for l in open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'srwex_jp.tbl'),encoding='utf-8'):
    k,v=l.rstrip('\n').split('=',1); T[bytes.fromhex(k)]=v
def s2f(a): return ((a>>16)&0x7f)*0x8000+(a&0xffff)-0x8000
def dec(o,maxn=400):
    out=[];i=o;base=(o//0x8000)*0x8000-0x8000
    while len(out)<maxn:
        c=R[i]
        if c==0xFF or 0xEC<=c<=0xEF: out.append('{END%s}'%('' if c==0xFF else '%02X'%c)); i+=1; break
        if 0xF0<=c<=0xF3: out.append(T.get(R[i:i+2],'{$%s}'%R[i:i+2].hex())); i+=2; continue
        if c<0xEC: out.append(T.get(bytes([c]),'{$%02X}'%c)); i+=1; continue
        if c==0xF4: out.append('{n}'); i+=1; continue
        if c==0xF5: out.append('{w}'); i+=1; continue
        if c==0xFD: out.append('{p}'); i+=1; continue
        if c==0xF6: out.append('{F6:%02X}'%R[i+1]); i+=2; continue
        if c==0xFE: out.append('{face:%02X}'%R[i+1]); i+=2; continue
        if c==0xFB: out.append('{FB:%02X}'%R[i+1]); i+=2; continue
        if c==0xF7: out.append('{call:%02X:%02X}'%(R[i+1],R[i+2])); i+=3; continue
        if c==0xFC: out.append('{FC:%02X%02X}'%(R[i+2],R[i+1])); i+=3; continue
        if c==0xF9: out.append('{F9:%s}'%R[i+1:i+4].hex()); i+=4; continue
        if c==0xF8:
            n=R[i+1]; out.append('{rand:%s}'%','.join('%04X'%(R[i+2+2*k]|R[i+3+2*k]<<8) for k in range(n))); i+=2+2*n; continue
        if c==0xFA:
            w=R[i+1]|R[i+2]<<8
            if w>=0x8000: out.append('{goto:%04X}'%w); i+=3; break
            p=R[i+3]|R[i+4]<<8; out.append('{if:%04X:%04X}'%(w,p)); i+=5; continue
    return ''.join(out), i
if __name__=='__main__':
    a=int(sys.argv[1],16); o=s2f(a) if a>=0x800000 else a
    n=int(sys.argv[2]) if len(sys.argv)>2 else 1
    for _ in range(n):
        s,e=dec(o); print('%06X'%o, s); o=e
