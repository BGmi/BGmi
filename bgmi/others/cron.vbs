set ws=wscript.createobject("wscript.shell")
ws.run "powershell.exe $env:BGMI_LOG='error'; bgmi cal --force-update --download-cover ; bgmi update --download", 0
