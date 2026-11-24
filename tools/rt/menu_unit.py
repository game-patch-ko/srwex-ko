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
seq = [(x+800,k) for x,k in [(9200,'b'),(9300,'b'),(9400,'a'),(9550,'down'),(9650,'down'),(9750,'down'),(9850,'down'),(9950,'a'),(10150,'a'),(10350,'a'),(10550,'right'),(10750,'right'),(10950,'a'),(11150,'b'),(11300,'b')]]
os.makedirs(outdir, exist_ok=True)
s = tpl.replace('OUTDIR', outdir.replace(chr(92), '/')).replace('LAST', '12200').replace('SEQ', ','.join('{%d,"%s"}' % x for x in seq))
open(lua, 'w').write(s)
