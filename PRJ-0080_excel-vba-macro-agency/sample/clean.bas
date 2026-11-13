Option Explicit
' Shell Kill CreateObject 는 주석이라 무시
Public Sub Total()
    Dim s As String
    s = "나는 ' 따옴표가 있는 글자"
    Range("A1").Value = Application.WorksheetFunction.Sum(Range("B1:B9"))
End Sub
