Set objShell = CreateObject("Wscript.Shell")

strPath = Wscript.ScriptFullName

Set objFSO = CreateObject("Scripting.FileSystemObject")

Set objFile = objFSO.GetFile(strPath)
strFolder = objFSO.GetParentFolderName(objFile) & "\usr\lib\astronciaiptv\"

objShell.CurrentDirectory = strFolder

Do
returnCode = objShell.Run("pythonw -m astroncia_iptv", 1, True)
Loop Until returnCode <> 23
