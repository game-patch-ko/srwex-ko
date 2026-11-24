"""python menu.py <outdir> <lua>: new game, advance dialogue, then open menus on the map (capture every 30 frames)"""
import sys, os
tpl = r'''
local outdir = "OUTDIR/"
local n = 0
local seq = {SEQ}
emu.addEventCallback(function()
  local inp = {}
  if n >= 600 and n < 3200 and (n % 90) < 6 then inp.start = true end
  if n >= 600 and n < 3200 and (n % 90) >= 45 and (n % 90) < 51 then inp.a = true end
  if n >= 3200 and n < 9800 and (n % 50) < 5 then inp.a = true end
  for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 6 then inp[s[2]] = true end end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n % 30 == 0 then
    local f = io.open(outdir .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= LAST then emu.stop(0) end
end, emu.eventType.endFrame)
'''
outdir, lua = sys.argv[1:3]
seq = [(x+800,k) for x,k in [(9200,'b'),(9300,'b'),(9400,'start'),(9600,'down'),(9700,'down'),(9800,'down'),(9900,'down'),(10000,'down'),(10100,'b'),(10200,'b'),(10300,'a'),(10500,'b'),(10600,'b'),(10700,'x'),(10900,'b'),(11000,'y'),(11200,'b')]]
os.makedirs(outdir, exist_ok=True)
s = tpl.replace('OUTDIR', outdir.replace(chr(92), '/')).replace('LAST', '12200').replace('SEQ', ','.join('{%d,"%s"}' % x for x in seq))
open(lua, 'w').write(s)
