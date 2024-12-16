Dim NextUpdate As Date
Dim autoUpdateEnabled As Boolean
' Δημιουργούμε μια Dictionary για την κατάσταση κάθε κρυπτονομίσματος
Dim emailStatus As Object
' Δημιουργούμε μια καθολική μεταβλητή για την κατάσταση της αυτόματης πώλησης
Dim AutoSellEnabled As Boolean
Sub ToggleAutoUpdate()
    ' Εναλλαγή της κατάστασης αυτόματης ενημέρωσης
    autoUpdateEnabled = Not autoUpdateEnabled

    ' Αναφορά στο κύριο Shape για την ενημέρωση
    Dim autoUpdateShape As Shape
    Dim stopIcon2 As Shape
    Set autoUpdateShape = ActiveSheet.Shapes("Rounded Rectangle 1") ' Κύριο κουμπί για το Auto Update
    Set stopIcon2 = ActiveSheet.Shapes("StopIcon2") ' Εικονίδιο Stop

    ' Αλλαγή κειμένου και χρώματος στο κύριο Shape
    If autoUpdateEnabled Then
        StartAutoUpdate autoUpdateShape
        stopIcon2.Visible = msoFalse ' Απόκρυψη εικονιδίου Stop
        'MsgBox "Auto update has been enabled."
    Else
        StopAutoUpdate autoUpdateShape
        stopIcon2.Visible = msoTrue ' Απόκρυψη εικονιδίου Stop
        'MsgBox "Auto update has been disabled."
    End If
End Sub
Sub StartAutoUpdate(autoUpdateShape As Shape)
    ' Ενεργοποίηση του Auto Update και προγραμματισμός της επόμενης εκτέλεσης
    autoUpdateEnabled = True
    NextUpdate = Now + TimeValue("00:04:00") ' Ρύθμιση χρόνου εκτέλεσης
    Application.OnTime NextUpdate, "UpdateCryptoData"

    ' Ενημέρωση του κειμένου και του χρώματος στο Shape
    autoUpdateShape.TextFrame.Characters.Text = "Απενεργοποίηση Αυτόματης Ενημέρωσης"
    autoUpdateShape.Fill.ForeColor.RGB = RGB(0, 128, 0) ' Πράσινο χρώμα
End Sub
Sub StopAutoUpdate(autoUpdateShape As Shape)
    On Error Resume Next
    ' Ακύρωση της προγραμματισμένης ενημέρωσης UpdateCryptoData
    Application.OnTime EarliestTime:=NextUpdate, Procedure:="UpdateCryptoData", Schedule:=False
    autoUpdateEnabled = False

    ' Ενημέρωση του κειμένου και του χρώματος στο Shape
    autoUpdateShape.TextFrame.Characters.Text = "Ενεργοποίηση Αυτόματης Ενημέρωσης"
    autoUpdateShape.Fill.ForeColor.RGB = RGB(255, 0, 0) ' Κόκκινο χρώμα
    On Error GoTo 0
End Sub
Sub ToggleAutoSell()
    ' Εναλλαγή της κατάστασης αυτόματης πώλησης
    AutoSellEnabled = Not AutoSellEnabled

    ' Αναφορά στο κύριο Shape και στο εικονίδιο "Stop"
    Dim autoSellShape As Shape
    Dim stopIcon As Shape
    Set autoSellShape = ActiveSheet.Shapes("Rounded Rectangle 4") ' Κύριο κουμπί
    Set stopIcon = ActiveSheet.Shapes("StopIcon") ' Εικονίδιο Stop

    ' Αλλαγή κειμένου και χρώματος στο κύριο Shape
    If AutoSellEnabled Then
        autoSellShape.TextFrame.Characters.Text = "Απενεργοποίηση Αυτόματης Πώλησης"
        autoSellShape.Fill.ForeColor.RGB = RGB(0, 128, 0) ' Πράσινο χρώμα
        stopIcon.Visible = msoFalse ' Απόκρυψη εικονιδίου Stop
    Else
        autoSellShape.TextFrame.Characters.Text = "Ενεργοποίηση Αυτόματης Πώλησης"
        autoSellShape.Fill.ForeColor.RGB = RGB(255, 0, 0) ' Κόκκινο χρώμα
        stopIcon.Visible = msoTrue ' Εμφάνιση εικονιδίου Stop

        ' Κλήση του macro για ακύρωση όλων των σημάτων πώλησης
        CancelAllSellSignals
    End If
End Sub
Sub CancelAllSellSignals()
    Dim http As Object
    Dim JSON As Object
    Dim CancelHttp As Object
    Dim apiURL As String
    Dim JsonData As String
    Dim botName As String
    Dim Timestamp As String
    
    ' Δημιουργία timestamp για να αποφύγουμε το caching
    Timestamp = "?timestamp=" & CStr(Now)
    
    ' URL του API που δίνει τη λίστα με τα bots
    apiURL = "http://192.168.2.251:5015/api/crypto-info" & Timestamp
    
    ' Δημιουργία του αντικειμένου HTTP για να λάβουμε τα ονόματα των bots
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "GET", apiURL, False
    http.Send
    
    ' Έλεγχος αν το αίτημα ήταν επιτυχές
    If http.Status = 200 Then
        ' Ανάλυση του JSON με τη λίστα των bots
        Set JSON = JsonConverter.ParseJson(http.responseText)
        
        ' Επανάληψη για κάθε bot στη λίστα
        For Each CoinData In JSON
            botName = CoinData("name")
            
            ' Δημιουργία του JSON request body με το όνομα του bot
            JsonData = "{""name"":""" & botName & """}"
            
            ' Διεύθυνση του endpoint για ακύρωση του σήματος πώλησης
            Dim CancelURL As String
            CancelURL = "http://192.168.2.251:5015/api/cancel_sell_signal"
            
            ' Δημιουργία νέου αντικειμένου HTTP για την ακύρωση του σήματος
            Set CancelHttp = CreateObject("MSXML2.XMLHTTP")
            CancelHttp.Open "POST", CancelURL, False
            CancelHttp.setRequestHeader "Content-Type", "application/json"
            CancelHttp.Send JsonData
            
            ' Έλεγχος αν το αίτημα ακύρωσης ήταν επιτυχές
            If CancelHttp.Status = 200 Then
                Debug.Print "Επιτυχής ακύρωση σήματος πώλησης για το bot: " & botName
            Else
                MsgBox "Σφάλμα στην ακύρωση σήματος πώλησης για το bot: " & botName & ". Κωδικός σφάλματος: " & CancelHttp.Status
            End If
        Next CoinData
        
        Debug.Print "Όλα τα σήματα πώλησης ακυρώθηκαν επιτυχώς."
    Else
        Debug.Print "Σφάλμα σύνδεσης στο API για τη λίστα των bots."
    End If
End Sub
Private Sub Worksheet_SelectionChange(ByVal Target As Range)
    ' Αποθηκεύει την τρέχουσα τιμή του H14 για παρακολούθηση αλλαγών
    If Target.Address = "$H$14" Then
        PreviousValue = Target.Value
    End If
End Sub
Sub InitializeEmailStatus()
    ' Αρχικοποίηση της Dictionary μόνο μία φορά στην αρχή της ημέρας ή σε reset
    Set emailStatus = CreateObject("Scripting.Dictionary")
End Sub

Sub SendEmail(ByVal name As String, ByVal cryptoPrice As Double)
    Dim http As Object
    Dim ApiKey As String
    Dim Url As String
    Dim JSON As String
    Dim ToEmail As String
    Dim FromEmail As String

    ApiKey = "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" ' Βάλε το SendGrid API key σου εδώ
    Url = "https://api.sendgrid.com/v3/mail/send"
    ToEmail = "info@f2d.gr" ' Βάλε τη διεύθυνση παραλήπτη
    FromEmail = "info@f2d.gr" ' Βάλε τη διεύθυνση αποστολέα

    ' Διαμόρφωση του θέματος και του σώματος του email
    Subject = "Notification: " & name & " Price Alert!"
    Body = "Το " & name & " μόλις ξεπέρασε το καθορισμένο όριο. Αυτη τη στιγμή το κέρδος είναι: " & cryptoPrice

    JSON = "{""personalizations"":[{""to"":[{""email"":""" & ToEmail & """}]}],""from"":{""email"":""" & FromEmail & """},""subject"":""" & Subject & """,""content"":[{""type"":""text/plain"",""value"":""" & Body & """}]}"

    Set http = CreateObject("MSXML2.XMLHTTP.6.0")
    http.Open "POST", Url, False
    http.setRequestHeader "Authorization", "Bearer " & ApiKey
    http.setRequestHeader "Content-Type", "application/json"
    http.Send JSON

    If http.Status <> 202 Then
        MsgBox "Failed to send email. Error: " & http.responseText
    End If
End Sub
Sub UpdateCryptoData()
    Dim apiURL As String
    Dim JSON As Object
    Dim http As Object
    Dim CoinData As Object
    Dim RowIndex As Integer
    Dim PairAPIURL As String
    Dim PairJson As Object
    Dim PairHttp As Object
    Dim Timestamp As String
    Dim staticVarsURL As String
    Dim staticVarsJson As Object
    Dim variableNames As Variant
    Dim i As Integer
    Dim cryptoWorkbook As Workbook
    Set cryptoWorkbook = Workbooks("cryptobots_update.xlsm")
    
    ' Έλεγχος αν η Dictionary έχει αρχικοποιηθεί
    If emailStatus Is Nothing Then
        InitializeEmailStatus
    End If
    
    ' Ορισμός μεταβλητών
    variableNames = Array("SCALP_TARGET", "BUY_THRESHOLD", "RSI_THRESHOLD", "ENABLE_STOP_LOSS", "STOP_LOSS", "ENABLE_TRAILING_PROFIT", "STATIC_TRAILING_PROFIT_THRESHOLD", "MINIMUM_PROFIT_THRESHOLD", "SELL_ON_TRAILING", "DAILY_PROFIT_TARGET")
    
    ' Δημιουργία timestamp
    Timestamp = "?timestamp=" & CStr(Now)
    
    ' URL για το API
    apiURL = "http://192.168.2.251:5015/api/crypto-info" & Timestamp
    
    ' Δημιουργία HTTP request
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "GET", apiURL, False
    http.Send
    
    If http.Status = 200 Then
        Set JSON = JsonConverter.ParseJson(http.responseText)
        
        RowIndex = 2 ' Ξεκινάμε από τη 2η γραμμή
        
        For Each CoinData In JSON
            ' Ενημέρωση δεδομένων για κάθε νόμισμα
            With cryptoWorkbook.Sheets("Sheet1")
                .Cells(RowIndex, 1).Value = CoinData("name")
                
                If Not IsNull(CoinData("active_trade")) Then
                    .Cells(RowIndex, 2).Value = CoinData("active_trade")
                Else
                    .Cells(RowIndex, 2).Value = 0
                End If
                
                If Not IsNull(CoinData("trade_amount")) Then
                    .Cells(RowIndex, 3).Value = CoinData("trade_amount")
                Else
                    .Cells(RowIndex, 3).Value = 0
                End If
                
                ' Ενημέρωση τιμής από το Coinbase API
                If CoinData("euro_pair") <> "" Then
                    PairAPIURL = "https://api.exchange.coinbase.com/products/" & CoinData("euro_pair") & "/ticker"
                    Set PairHttp = CreateObject("MSXML2.XMLHTTP")
                    PairHttp.Open "GET", PairAPIURL, False
                    PairHttp.Send
                    
                    If PairHttp.Status = 200 Then
                        Set PairJson = JsonConverter.ParseJson(PairHttp.responseText)
                        .Cells(RowIndex, 6).Value = PairJson("price")
                    Else
                        MsgBox "API error for pair: " & CoinData("euro_pair")
                    End If
                End If
                
                
                ' Ενημέρωση δεδομένων DCA 2
                With cryptoWorkbook.Sheets("Sheet1")
                    If Not IsNull(CoinData("second_trade_price")) Then
                        .Cells(RowIndex, 9).Value = CoinData("second_trade_price") ' DCA 2 Price
                    Else
                        .Cells(RowIndex, 9).Value = "N/A"
                    End If
                    
                    If Not IsNull(CoinData("second_trade_amount")) Then
                        .Cells(RowIndex, 10).Value = CoinData("second_trade_amount") ' DCA 2 Amount
                    Else
                        .Cells(RowIndex, 10).Value = "N/A"
                    End If
                End With
                
                
                
                
                ' Ενημέρωση της κατάστασης του bot
                If IsNull(CoinData("start_bot")) Then
                    .Cells(RowIndex, 14).Value = "Not Available"
                ElseIf CoinData("start_bot") = True Then
                    .Cells(RowIndex, 14).Value = "Started"
                Else
                    .Cells(RowIndex, 14).Value = "Stopped"
                End If
                
                ' Call API to read static variables and update columns M-S
                staticVarsURL = "http://192.168.2.251:5015/api/get_static_variables?name=" & CoinData("name") & "&" & Timestamp
                http.Open "GET", staticVarsURL, False
                http.Send
                
                
                If http.Status = 200 Then
                    Set staticVarsJson = JsonConverter.ParseJson(http.responseText)
                    
                    ' Update cells in columns M to S with static variable values
                    For i = 0 To UBound(variableNames)
                        If Not IsNull(staticVarsJson(variableNames(i))) Then
                            .Cells(RowIndex, 15 + i).Value = staticVarsJson(variableNames(i))
                        Else
                            .Cells(RowIndex, 15 + i).Value = "N/A"
                        End If
                    Next i
                Else
                    MsgBox "Failed to retrieve static variables for bot: " & CoinData("name")
                End If
                               

                ' Color the cells from A to L based on trade amount
                If .Cells(RowIndex, 3).Value > 0 Then
                    .Range(.Cells(RowIndex, 1), .Cells(RowIndex, 14)).Interior.Color = RGB(198, 239, 206) ' Green color
                Else
                    .Range(.Cells(RowIndex, 1), .Cells(RowIndex, 14)).Interior.Color = RGB(255, 199, 206) ' Red color
                End If
                
                
                ' color cells
                If .Cells(RowIndex, 8).Value <> 0 Then
                    Dim cryptoPrice As Double
                    Dim name As String
                    cryptoPrice = CDbl(.Cells(RowIndex, 8).Value)
                    name = .Cells(RowIndex, 1).Value
                
                
                    ' ¸ëåã÷ïò ôéìÞò êáé áëëáãÞ ÷ñþìáôïò
                    If .Cells(RowIndex, 8).Value > .Cells(RowIndex, 22).Value Then
                        .Cells(RowIndex, 8).Interior.Color = RGB(0, 100, 0) ' Dark green
                    Else
                        .Cells(RowIndex, 8).Interior.Color = RGB(255, 0, 0) ' Red
                    End If
                End If
            End With
            
            RowIndex = RowIndex + 1
        Next CoinData
    Else
        MsgBox "Error connecting to the local API."
    End If
    
    ' Αν το Auto Update είναι ενεργοποιημένο, προγραμματίζεται ξανά
    If autoUpdateEnabled Then
        Dim autoUpdateShape As Shape
        Set autoUpdateShape = ActiveSheet.Shapes("Rounded Rectangle 1")
        StartAutoUpdate autoUpdateShape
    End If

    ' Trigger AutoSellExecution after auto update scheduling
    AutoSellExecution
End Sub
Sub AutoSellExecution()
    Dim RowIndex As Integer
    Dim cryptoWorkbook As Workbook
    Dim name As String
    
    Set cryptoWorkbook = Workbooks("cryptobots_update.xlsm")
    
    ' Εκτέλεση πώλησης μετά την ενημέρωση δεδομένων
    With cryptoWorkbook.Sheets("Sheet1")
        RowIndex = 2
        Do While Not IsEmpty(.Cells(RowIndex, 1).Value)
            ' Έλεγχος αν η αυτόματη πώληση είναι ενεργοποιημένη
            If AutoSellEnabled Then
                ' Έλεγχος συνθήκης
                If .Cells(RowIndex, 8).Value > .Cells(RowIndex, 22).Value Then
                    name = .Cells(RowIndex, 1).Value
                    
                    ' Εκτέλεση πώλησης
                    On Error Resume Next
                    Application.Run "SellBot" & name
                    On Error GoTo 0
                End If
            End If
            RowIndex = RowIndex + 1
        Loop
    End With
End Sub

