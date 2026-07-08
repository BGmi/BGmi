set ws=wscript.createobject("wscript.shell")
ws.run "powershell.exe $env:BGMI_LOG='error'; bgmi cal --update --cover ; bgmi update --download", 0
