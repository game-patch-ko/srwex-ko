local n = 0
local f = io.open("C:/work/sfc/srwex-ko/tools/shots/wlim.txt", "w")
emu.addMemoryCallback(function()
  local w = emu.read(0x0E34, emu.memType.snesMemory) 
  local l = emu.read(0x0E35, emu.memType.snesMemory)
  f:write(string.format("%d %d %d\n", n, w, l))
end, emu.callbackType.exec, 0x01861D)
emu.addEventCallback(function()
  n = n + 1
  if n >= 8800 then f:close(); emu.stop(0) end
end, emu.eventType.endFrame)
