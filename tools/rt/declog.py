"""python declog.py <outdir> <lua> <from> <to>: boot game (Start/A), log LZ calls ($80:8AD7) and shoot every 15 frames in [from,to]"""
import sys, os
outdir, lua, a, b = sys.argv[1:5]
os.makedirs(outdir, exist_ok=True)
open(lua, 'w').write(r'''
local OUT = "%s/"
local A, B = %s, %s
local n = 0
local M = emu.memType.snesMemory
local log = io.open(OUT .. "dec.txt", "w")
emu.addMemoryCallback(function()
  local src = emu.read(0x10, M) + emu.read(0x11, M) * 256 + emu.read(0x12, M) * 65536
  local dst = emu.read(0x13, M) + emu.read(0x14, M) * 256 + emu.read(0x15, M) * 65536
  log:write(string.format("%%d dec %%06X -> %%06X\n", n, src, dst)); log:flush()
end, emu.callbackType.exec, 0x008AD7)
emu.addEventCallback(function()
  local inp = {}
  if n >= 600 and n < 2400 and (n %% 90) < 6 then inp.start = true end
  if n >= 2400 and (n %% 50) < 5 then inp.a = true end
  emu.setInput(inp, 0)
end, emu.eventType.inputPolled)
emu.addEventCallback(function()
  n = n + 1
  if n >= A and n <= B and n %% 15 == 0 then
    local f = io.open(OUT .. string.format("%%05d.png", n), "wb"); f:write(emu.takeScreenshot()); f:close()
  end
  if n > B then log:close(); emu.stop(0) end
end, emu.eventType.endFrame)
''' % (outdir.replace(chr(92), '/'), a, b))
