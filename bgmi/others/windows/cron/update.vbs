set ws = WScript.CreateObject("WScript.Shell")
ws.Run "powershell.exe $env:BGMI_LOG='error'; bgmi update -d", 0, true
