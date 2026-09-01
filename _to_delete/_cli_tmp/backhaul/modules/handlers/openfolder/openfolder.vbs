' openfolder.vbs — handler for the openfolder: custom URL protocol.
'
' Registered (by install.py) as the shell\open\command for HKCU\Software\Classes\openfolder,
' so Windows runs:   wscript.exe "...\openfolder.vbs" "%1"
' when a rendered link like openfolder:///C:/path/to/project is clicked in Chrome. %1 arrives
' here as WScript.Arguments(0) — the full URL, exactly as build_uri() in
' foundation/handler_uri.py constructed it. Decoding logic must stay in sync with that module.
'
' Opens the target folder in Windows Explorer.

Option Explicit

Const SCHEME_PREFIX = "openfolder:///"

Function UrlDecode(ByVal s)
    Dim i, ch, hex, result
    result = ""
    i = 1
    Do While i <= Len(s)
        ch = Mid(s, i, 1)
        If ch = "%" And i + 2 <= Len(s) Then
            hex = Mid(s, i + 1, 2)
            result = result & Chr(CLng("&H" & hex))
            i = i + 3
        Else
            result = result & ch
            i = i + 1
        End If
    Loop
    UrlDecode = result
End Function

Dim raw, encodedPath, decodedPath, winPath, shell

If WScript.Arguments.Count = 0 Then
    WScript.Quit 1
End If

raw = WScript.Arguments(0)

If Left(raw, Len(SCHEME_PREFIX)) = SCHEME_PREFIX Then
    encodedPath = Mid(raw, Len(SCHEME_PREFIX) + 1)
Else
    ' Unexpected shape — fall back to treating the whole argument as the path.
    encodedPath = raw
End If

decodedPath = UrlDecode(encodedPath)
winPath = Replace(decodedPath, "/", "\")

If Not CreateObject("Scripting.FileSystemObject").FolderExists(winPath) Then
    MsgBox "openfolder handler: folder does not exist:" & vbCrLf & winPath, _
        vbExclamation, "Backhaul openfolder handler"
    WScript.Quit 1
End If

Set shell = CreateObject("WScript.Shell")
shell.Run "explorer.exe """ & winPath & """", 1, False
