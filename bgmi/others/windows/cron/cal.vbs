set ws = WScript.CreateObject("WScript.Shell")
ws.Run "powershell.exe $env:BGMI_LOG='error'; bgmi cal --force-update --download-cover", 0, true
