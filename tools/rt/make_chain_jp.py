"""Show every dialogue segment through the real game renderer.

  python tools/rt/make_chain.py <groups comma> <mode game|demo> <outdir> <lua path> [startframe]

Makes out/srwex_verify.smc (= out/srwex_ko.smc + '{w}{face:12}' at $BF:FFF0) and a Lua script that:
  - waits for the first dialogue read in the KO text banks, then redirects the reader ($AD/$AF)
    to each queued segment in turn (segments reached through branches count as shown);
  - at a segment's end (FF) it detours through F4 (wait key; the next speech starts at column 0 like a real {w}) and continues;
  - logs: seg <label>, wrap <label> (game auto-wrap at $81:85F0 = a character was dropped),
    shot <file> <label>; takes a screenshot at every key wait.
Labels/addresses come from out/srwex_ko_labels.tsv (written by srwtext.py build).
"""
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
SPOT = 0xBFFFF0

groups, mode, outdir, luapath = sys.argv[1:5]
startf = int(sys.argv[5]) if len(sys.argv) > 5 else 2400
groups = groups.split(',')

rom = bytearray(open(os.path.join(ROOT, 'out', 'srwex_reloc_only.smc'), 'rb').read())
o = (SPOT >> 16 & 0x7F) * 0x8000 + (SPOT & 0x7FFF)
assert rom[o:o + 4] == b'\xFF\xFF\xFF\xFF', 'spot not free'
rom[o:o + 4] = b'\xF5\xFE\x12\xFF'   # {w}{face:12}: a real speech boundary (portrait may be wrong)
open(os.path.join(ROOT, 'out', 'srwex_verify_jp.smc'), 'wb').write(rom)

segs = []
for ln in open(os.path.join(ROOT, 'out', 'srwex_reloc_only_labels.tsv'), encoding='utf-8'):
    lab, g, a, n = ln.rstrip('\n').split('\t')
    segs.append((lab, g, int(a, 16), int(n)))
queue = [s for s in segs if s[1] in groups or s[0] in groups]
allseg = [s for s in segs if s[1].startswith('dlg')]

lua = []
lua.append('local OUT = "%s/"' % outdir.replace('\\', '/'))
lua.append('local MODE, STARTF, SPOT = "%s", %d, 0x%06X' % (mode, startf, SPOT))
lua.append('local Q = {' + ','.join('{"%s",0x%06X,%d}' % (l, a, n) for l, g, a, n in queue) + '}')
lua.append('local S = {}')
for l, g, a, n in allseg:
    lua.append('S[0x%06X]={"%s",%d}' % (a, l, n))
lua.append(r'''
local M = emu.memType.snesMemory
local lastread = 0
local log = io.open(OUT .. "chain.txt", "w")
local n, started, qi, done = 0, false, 0, false
local curlab, curstart, curlen = "-", 0, 0
local seen = {}
local waitAt, shotAt, shotNo, page = -1000, -1, 0, 0
local function setptr(a)
  emu.write16(0xCA, a & 0xFFFF, M); emu.write(0xCC, (a >> 16) & 0xFF, M)
  local s = S[a]; if s then curlab, curstart, curlen = s[1], a, s[2]; seen[curlab] = true; page = 0; log:write("seg " .. curlab .. "\n") end
  log:write(string.format("ptr %06X n=%d w=%d line=%d\n", a, n, emu.read(0x0E32, M), emu.read(0x0E33, M))); log:flush()
end
local function nextseg()
  repeat qi = qi + 1 until qi > #Q or not seen[Q[qi][1]]
  if qi > #Q then done = true; log:write("done\n"); return SPOT end
  return Q[qi][2]
end
emu.addMemoryCallback(function()
  lastread = n
  local ad = emu.read16(0xCA, M); local af = emu.read(0xCC, M); local cur = af * 65536 + ad
  if not started then
    if n > STARTF and af >= 0xB3 and af <= 0xBF then started = true; setptr(nextseg()) end
    return
  end
  if done then return end
  if cur == SPOT + 3 then setptr(nextseg()); return end
  local s = S[cur]
  if s then curlab, curstart, curlen = s[1], cur, s[2]; seen[curlab] = true; page = 0; log:write("seg " .. curlab .. "\n") end
  if cur == curstart + curlen - 1 and emu.read(cur, M) == 0xFF then setptr(SPOT) end   -- the segment's own terminator, not a hangul low byte
end, emu.callbackType.exec, 0x018B52)
emu.addMemoryCallback(function()
  if started and not done then
    local lim = emu.read(0x0E34, M); local w = emu.read(0x0E32, M)
    if lim < w then log:write(string.format("wrap %s lim=%d w=%d line=%d n=%d\n", curlab, lim, w, emu.read(0x0E33, M), n)) end
  end
end, emu.callbackType.exec, 0x018617)
emu.addMemoryCallback(function()
  if started and not done then waitAt = n; shotAt = n + 30 end
end, emu.callbackType.exec, 0x0186B6)
emu.addEventCallback(function()
  local inp = {}
  if MODE == "game" and n >= 600 and n < 2400 and (n % 90) < 6 then inp.start = true end
  if MODE == "game" and n >= 2400 and not started and (n % 60) < 6 then inp.a = true end
  if started and n >= waitAt + 32 and n < waitAt + 36 then inp.a = true end
  if started and not done and n - lastread > 600 and (n % 60) < 6 then inp.a = true; inp.b = (n % 120) < 6 end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n == shotAt then
    page = page + 1; shotNo = shotNo + 1
    local name = string.format("%05d_%s_%d.png", shotNo, curlab, page)
    local f = io.open(OUT .. name, "wb"); f:write(emu.takeScreenshot()); f:close()
    log:write("shot " .. name .. " " .. curlab .. "\n")
  end
  if started and n - lastread == 3000 then log:write(string.format("stall n=%d lab=%s\n", n, curlab)); log:flush() end
  if done or n > 400000 or (started and n - lastread > 6000) then log:close(); emu.stop(0) end
end, emu.eventType.endFrame)
''')
os.makedirs(outdir, exist_ok=True)
open(luapath, 'w', encoding='utf-8').write('\n'.join(lua))
print('queue', len(queue), 'segments; lua', luapath)
