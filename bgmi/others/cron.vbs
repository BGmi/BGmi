set ws=wscript.createobject("wscript.shell")
ws.run "powershell.exe bgmi update --download", 0

set ws2=wscript.createobject("wscript.shell")
ws2.run "powershell.exe bgmi cal --force-update --download-cover", 0
