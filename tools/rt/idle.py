"""python boot.py <outdir> <lastframe> <lua>  : capture every 60 frames; Start pulses then A presses"""
import sys, os
tpl = r'''
local outdir = "OUTDIR/"
local n = 0
emu.addEventCallback(function()
  local inp = {}
  --
  --
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n % 60 == 0 then
    local f = io.open(outdir .. string.format("%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n >= LAST then emu.stop(0) end
end, emu.eventType.endFrame)
'''
outdir, last, path = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
open(path, 'w').write(tpl.replace('OUTDIR', outdir.replace(chr(92), '/')).replace('LAST', last))
