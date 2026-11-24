"""Minimal 65816 disassembler for LoROM SRW3.
usage: python dis65816.py <snes_addr_hex e.g. 84AA80> <count> [m8|m16] [x8|x16]
Tracks REP/SEP within a linear sweep (not across branches)."""
import sys
ROM = open(__file__.rsplit('\\', 1)[0].rsplit('/', 1)[0] + '/../Super Robot Taisen EX (J).smc', 'rb').read() if False else None
import os
ROM = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Super Robot Taisen EX (J).smc'), 'rb').read()

def s2f(a):
    bank = (a >> 16) & 0x7F
    return bank * 0x8000 + ((a & 0xFFFF) - 0x8000)

M = ['BRK s','ORA (d,x)','COP s','ORA d,s','TSB d','ORA d','ASL d','ORA [d]','PHP','ORA #m','ASL A','PHD','TSB a','ORA a','ASL a','ORA al',
'BPL r','ORA (d),y','ORA (d)','ORA (d,s),y','TRB d','ORA d,x','ASL d,x','ORA [d],y','CLC','ORA a,y','INC A','TCS','TRB a','ORA a,x','ASL a,x','ORA al,x',
'JSR a','AND (d,x)','JSL al','AND d,s','BIT d','AND d','ROL d','AND [d]','PLP','AND #m','ROL A','PLD','BIT a','AND a','ROL a','AND al',
'BMI r','AND (d),y','AND (d)','AND (d,s),y','BIT d,x','AND d,x','ROL d,x','AND [d],y','SEC','AND a,y','DEC A','TSC','BIT a,x','AND a,x','ROL a,x','AND al,x',
'RTI','EOR (d,x)','WDM s','EOR d,s','MVP bb','EOR d','LSR d','EOR [d]','PHA','EOR #m','LSR A','PHK','JMP a','EOR a','LSR a','EOR al',
'BVC r','EOR (d),y','EOR (d)','EOR (d,s),y','MVN bb','EOR d,x','LSR d,x','EOR [d],y','CLI','EOR a,y','PHY','TCD','JML al','EOR a,x','LSR a,x','EOR al,x',
'RTS','ADC (d,x)','PER rl','ADC d,s','STZ d','ADC d','ROR d','ADC [d]','PLA','ADC #m','ROR A','RTL','JMP (a)','ADC a','ROR a','ADC al',
'BVS r','ADC (d),y','ADC (d)','ADC (d,s),y','STZ d,x','ADC d,x','ROR d,x','ADC [d],y','SEI','ADC a,y','PLY','TDC','JMP (a,x)','ADC a,x','ROR a,x','ADC al,x',
'BRA r','STA (d,x)','BRL rl','STA d,s','STY d','STA d','STX d','STA [d]','DEY','BIT #m','TXA','PHB','STY a','STA a','STX a','STA al',
'BCC r','STA (d),y','STA (d)','STA (d,s),y','STY d,x','STA d,x','STX d,y','STA [d],y','TYA','STA a,y','TXS','TXY','STZ a','STA a,x','STZ a,x','STA al,x',
'LDY #x','LDA (d,x)','LDX #x','LDA d,s','LDY d','LDA d','LDX d','LDA [d]','TAY','LDA #m','TAX','PLB','LDY a','LDA a','LDX a','LDA al',
'BCS r','LDA (d),y','LDA (d)','LDA (d,s),y','LDY d,x','LDA d,x','LDX d,y','LDA [d],y','CLV','LDA a,y','TSX','TYX','LDY a,x','LDA a,x','LDX a,y','LDA al,x',
'CPY #x','CMP (d,x)','REP #8','CMP d,s','CPY d','CMP d','DEC d','CMP [d]','INY','CMP #m','DEX','WAI','CPY a','CMP a','DEC a','CMP al',
'BNE r','CMP (d),y','CMP (d)','CMP (d,s),y','PEI d','CMP d,x','DEC d,x','CMP [d],y','CLD','CMP a,y','PHX','STP','JML [a]','CMP a,x','DEC a,x','CMP al,x',
'CPX #x','SBC (d,x)','SEP #8','SBC d,s','INC d','SBC d','INC d','SBC [d]','INX','SBC #m','NOP','XBA','CPX a','SBC a','INC a','SBC al',
'BEQ r','SBC (d),y','SBC (d)','SBC (d,s),y','PEA a','SBC d,x','INC d,x','SBC [d],y','SED','SBC a,y','PLX','XCE','JSR (a,x)','SBC a,x','INC a,x','SBC al,x']

def dis(addr, count, m8=True, x8=True, out=print):
    pc = addr
    for _ in range(count):
        o = s2f(pc)
        op = ROM[o]
        name = M[op]
        mn, _, mode = name.partition(' ')
        if mode in ('', 'A'): n = 0
        elif mode in ('d', 'd,x', 'd,y', '(d)', '(d,x)', '(d),y', '[d]', '[d],y', 'd,s', '(d,s),y', 'r', 's', '#8'): n = 1
        elif mode in ('a', 'a,x', 'a,y', '(a)', '(a,x)', '[a]', 'rl', 'bb'): n = 2
        elif mode in ('al', 'al,x'): n = 3
        elif mode == '#m': n = 1 if m8 else 2
        elif mode == '#x': n = 1 if x8 else 2
        else: n = 0
        b = ROM[o + 1:o + 1 + n]
        v = int.from_bytes(b, 'little') if n else 0
        if mode == 'r':
            t = (pc & 0xFF0000) | ((pc + 2 + (v - 256 if v > 127 else v)) & 0xFFFF); arg = '$%04X' % (t & 0xFFFF)
        elif mode == 'rl':
            t = (pc & 0xFF0000) | ((pc + 3 + (v - 65536 if v > 32767 else v)) & 0xFFFF); arg = '$%04X' % (t & 0xFFFF)
        elif mode.startswith('#'):
            arg = '#$%0*X' % (n * 2, v)
        elif mode == 'bb':
            arg = '$%02X,$%02X' % (b[1], b[0])
        elif n:
            arg = mode.replace('al', '$%06X' % v).replace('a', '$%04X' % v).replace('d', '$%02X' % v) if mode not in ('s',) else '$%02X' % v
        else:
            arg = 'A' if mode == 'A' else ''
        out('%02X:%04X  %-12s %s %s' % (pc >> 16, pc & 0xFFFF, (bytes([op]) + b).hex(' '), mn, arg))
        if op == 0xC2:
            if v & 0x20: m8 = False
            if v & 0x10: x8 = False
        if op == 0xE2:
            if v & 0x20: m8 = True
            if v & 0x10: x8 = True
        pc = (pc & 0xFF0000) | ((pc + 1 + n) & 0xFFFF)
    return pc

if __name__ == '__main__':
    a = int(sys.argv[1], 16); c = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    m8 = not (len(sys.argv) > 3 and sys.argv[3] == 'm16'); x8 = not (len(sys.argv) > 4 and sys.argv[4] == 'x16')
    dis(a, c, m8, x8)
