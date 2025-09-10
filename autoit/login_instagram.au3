#include <Array.au3> ; Para exibir resultados
#include <MsgBoxConstants.au3> ; Para mensagens de erro

Local $aResult
Local $instagram = "https://www.instagram.com/" ; Altere aqui para outro site, se quiser
Local $id_tarefa
Local $link_tarefa
Local $sTempFolder = @ScriptDir & "\temp"
Local $sFilePath = $sTempFolder & "\perfil.txt"
Local $sClipboard
Local $cor_preto
Local $cor_branco = 16777215
Local $cor_azul = 4873721
Local $cor_valida1
Local $cor_valida2
Local $sNomeRobo = @UserName
Local $sStatus
Local $sId_robo
Local $sId_usuario
Local $sLogin
Local $sSenha
Local $sSegunda
Local $sId_conta
Local $sQuery
Local $cCont1 = 1
Local $cCont2 = 1
Local $cCont3 = 1
Local $sSegundo_fator
Local $cor_azulclaro = 8424955
Local $cor_azulbebe = 38390
Local $a = 1
Local $b = 1
Local $c = 1
Local $sStatusRobo


; ###############################################
	Global $oErrorHandler = ObjEvent("AutoIt.Error", "_ErrFunc")
	Func _ErrFunc($oError)
	    ConsoleWrite("COM Error: " & $oError.description & @CRLF)
	EndFunc
	; Criar objeto de conexão ADO
	Global $oConnection = ObjCreate("ADODB.Connection")
	If @error Then
	    MsgBox($MB_ICONERROR, "Erro", "Falha ao criar objeto ADODB.Connection")
	    Exit
	EndIf
	; String de conexão para MySQL (ajuste com suas credenciais)
	Local $sConnectionString = "Provider=MSDASQL;Driver={MySQL ODBC 8.0 Unicode Driver};Server=162.241.203.70;Database=feli1439_bot;Uid=feli1439_masterbot;Pwd=Adorigram190120!;"
	$oConnection.Open($sConnectionString)
	If @error Then
	    ;MsgBox($MB_ICONERROR, "Erro", "Falha ao conectar: " & @error)
	    Exit
	EndIf
	;MsgBox($MB_ICONINFORMATION, "Sucesso", "Conexão estabelecida!")
	Global $oRecordset = ObjCreate("ADODB.Recordset")
	If @error Then
	    MsgBox($MB_ICONERROR, "Erro", "Falha ao criar objeto ADODB.Recordset")
	    Exit
	EndIf
; ###############################################

; >>>>>>>>>>>>>>>> Buscar dados

While $c < 2
	$oRecordset.Open("SELECT * FROM robo WHERE nome_acc = '"& $sNomeRobo &"'" , $oConnection)
	If @error Then
		MsgBox($MB_ICONERROR, "Erro", "Falha na query SELECT: " & @error)
		Exit
	EndIf
	If Not $oRecordset.EOF Then
		$aResult = $oRecordset.GetRows()
		;_ArrayDisplay($aResult, "Dados da tabela teste")
	Else
		MsgBox($MB_ICONINFORMATION, "Info", "Erro au extrair status do robo")
	EndIf
	$sId_robo = $aResult[0][0]	
	$sStatusRobo = $aResult[0][2]
	$sId_usuario = $aResult[0][3]
	$oRecordset.Close
	If $sStatusRobo == 'Livre' Then
	ElseIf $sStatus == 'Erro' Then
		Exit
	Else
		$c = $c + 2
	EndIf
	Sleep(5000)
WEnd

$c = 1

;===== acima trouxe o status do robo, assim que muda de livre, segue adiante

While $c < 2
$oRecordset.Open("SELECT * FROM autentica_instagram WHERE id_robo = '"& $sId_robo &"'" , $oConnection)
If @error Then
    MsgBox($MB_ICONERROR, "Erro", "Falha na query SELECT: " & @error)
    Exit
EndIf

; Exibir resultados

If Not $oRecordset.EOF Then
    $aResult = $oRecordset.GetRows()
    ;_ArrayDisplay($aResult, "Dados da tabela teste")
Else
    MsgBox($MB_ICONINFORMATION, "Info", "2 Nenhum dado encontrado")
EndIf


$sId_conta = $aResult[0][0]
$sLogin = $aResult[0][2]
$sSenha = $aResult[0][3]
$sSegunda = $aResult[0][4]
$sSegundo_fator = $aResult[0][6]
$oRecordset.Close

If $sSegundo_fator == 8 Then
ElseIf $sSegundo_fator == 5 Then
	$c = $c + 2
	Sleep(5000)
Else
	$c = $c + 2
EndIf


WEnd
$c =1

; --------------------Abre o Google Chrome com o URL especificado

Run("C:\Program Files\Google\Chrome\Application\chrome.exe " & $instagram)
Sleep(600)
; Aguarda a janela do Chrome ficar ativa e maximiza
WinWaitActive("[CLASS:Chrome_WidgetWin_1]")
WinSetState("[CLASS:Chrome_WidgetWin_1]", "", @SW_MAXIMIZE)
Sleep(600)
;------------------- Fim abrir instagram ---------------------------------


$cor_valida1 =  PixelGetColor(1358, 524)
$cor_valida2 =  PixelGetColor(1130, 524)
	Sleep(3000)
		If $cor_valida1 <> $cor_preto Or $cor_valida2 == $cor_branco Then
		Sleep(600)
		MouseClick("Left", 1370, 430, 2)
		Sleep(300)
		Send("{Del}")
		Sleep(300)
		ClipPut($sLogin)
		Sleep(300)
		Send("^v")
		Sleep(300)
		Send("{Tab}")
		Sleep(300)
		Send("{Del}")
		ClipPut("")
		ClipPut($sSenha)
		Sleep(300)
		Send("^v")
		Sleep(300)
		Send("{Enter}") ; LOGAR
		Sleep(10000)
		MouseMove(1890, 145) 
		$cor_valida1 =  PixelGetColor(1315, 507)
		If $cor_valida1 == $cor_azul Or $cor_valida1 == $cor_azulclaro Or $cor_valida1 == $cor_azulbebe Then
			; SENHA ERRADA
			$sQuery = "UPDATE autentica_instagram SET segundo_fator = 3 WHERE id = '"& $sId_conta &"' "
			$oConnection.Execute($sQuery)
			While $cCont1 <= 2			
				$oRecordset.Open("SELECT * FROM autentica_instagram WHERE id_robo = '"& $sId_robo &"'" , $oConnection)
				If @error Then
					MsgBox($MB_ICONERROR, "Erro", "Falha na query SELECT: " & @error)
					Exit
				EndIf
				; Exibir resultados
				If Not $oRecordset.EOF Then
					$aResult = $oRecordset.GetRows()
					;_ArrayDisplay($aResult, "Dados da tabela teste")
				Else
					MsgBox($MB_ICONINFORMATION, "Info", "4 Nenhum dado encontrado")
				EndIf
				$sSegunda = $aResult[0][4]
				$sLogin = $aResult[0][2]
				$sSenha = $aResult[0][3]
				$sSegundo_fator = $aResult[0][6]
				$oRecordset.Close
				If $sSegundo_fator == 3 Then
					Sleep(30000)
					$cor_valida1 =  PixelGetColor(1315, 507)
					If $cor_valida1 == $cor_azul Or $cor_valida1 == $cor_azulclaro Or $cor_valida1 == $cor_azulbebe Then
					Else
						$sQuery = "UPDATE autentica_instagram SET segundo_fator = 5 WHERE id = '"& $sId_conta &"' "
						$oConnection.Execute($sQuery)
						$cCont1 = $cCont1 + 10
					EndIf
				ElseIf $sSegundo_fator == 1 Then					
					$cor_valida1 =  PixelGetColor(1371, 507)
					If $cor_valida1 == $cor_azul Or $cor_valida1 == $cor_azulclaro Or $cor_valida1 == $cor_azulbebe Then
						Sleep(600)
						MouseClick("Left", 1345, 415, 1)
						Sleep(300)
						MouseClick("Left", 1345, 415, 1)
						Sleep(300)
						MouseClick("Left", 1345, 415, 1)
						Sleep(300)
						Send("{Del}")
						Sleep(300)
						ClipPut($sLogin)
						Sleep(300)
						Send("^v")
						Sleep(300)
						Send("{Tab}")
						Sleep(300)
						Send("{Del}")
						ClipPut("")
						ClipPut($sSenha)
						Sleep(300)
						Send("^v")
						Sleep(300)
						Send("{Enter}")
						Sleep(10000)
						$sQuery = "UPDATE autentica_instagram SET segundo_fator = 3 WHERE id = '"& $sId_conta &"' "
						$oConnection.Execute($sQuery)
						$a = $a + 1
					ElseIf $a == 4 Then
						$sQuery = "UPDATE autentica_instagram SET segundo_fator = 7 WHERE id = '"& $sId_conta &"' "
						$oConnection.Execute($sQuery)
						MouseClick("Left", 1896, 17, 1)
						Exit	
					Else
						$sQuery = "UPDATE autentica_instagram SET segundo_fator = 5 WHERE id = '"& $sId_conta &"' "
						$oConnection.Execute($sQuery)
						$cCont1 = $cCont1 + 10					
					EndIf
				EndIf
			WEnd
				$a = 1
				$cCont1 = 1
				
			Else				
				$cor_valida1 =  PixelGetColor(1063, 448)
				$cor_valida2 =  PixelGetColor(860, 448)
				If ($cor_azul == $cor_valida1 And $cor_azul == $cor_valida2) Or ($cor_azulclaro == $cor_valida1 And $cor_azulclaro == $cor_valida2) Or ($cor_azulbebe == $cor_valida1 And $cor_azulbebe == $cor_valida2) Then
					$sQuery = "UPDATE autentica_instagram SET segundo_fator = 2 WHERE id = '"& $sId_conta &"' "
					$oConnection.Execute($sQuery)
					MouseClick("Left", 1063, 448, 1)
					Sleep(1000)
					While $cCont2 <= 2
						$oRecordset.Open("SELECT segundo_fator, segunda_etapa FROM autentica_instagram WHERE id_robo = '"& $sId_robo &"'" , $oConnection)
						If @error Then
							MsgBox($MB_ICONERROR, "Erro", "Falha na query SELECT: " & @error)
							Exit
						EndIf
						; Exibir resultados
						If Not $oRecordset.EOF Then
							$aResult = $oRecordset.GetRows()
							;_ArrayDisplay($aResult, "Dados da tabela teste")
						Else
							MsgBox($MB_ICONINFORMATION, "Info", "3 Nenhum dado encontrado")
						EndIf
						$sSegundo_fator = $aResult[0][0]
						$sSegunda = $aResult[0][1]
						$oRecordset.Close
						
						If $sSegundo_fator == 2 Then
							Sleep(10000)
							
							$cor_valida1 =  PixelGetColor(1029, 417)
							$cor_valida2 =  PixelGetColor(855, 424)
							If $cor_valida1 == $cor_azul Or $cor_valida1 == $cor_azulclaro Or $cor_valida2 == $cor_azul Or $cor_valida2 == $cor_azulclaro Or $cor_valida1 == $cor_azulbebe Or $cor_valida2 == $cor_azulbebe Then
							Else
								$sQuery = "UPDATE autentica_instagram SET segundo_fator = 5 WHERE id = '"& $sId_conta &"' "
								$oConnection.Execute($sQuery)
								$cCont2 = $cCont2 + 10
							EndIf					

						ElseIf $sSegundo_fator == 4 Then
							MouseClick("Left", 1055, 377, 2)
							Sleep(1000)
							Send("{Del}")
							ClipPut("")
							ClipPut($sSegunda)
							Send("^v")
							Sleep(600)
							Send("{Enter}")						
							$sQuery = "UPDATE autentica_instagram SET segundo_fator = 2 WHERE id = '"& $sId_conta &"' "
							$oConnection.Execute($sQuery)
							Sleep(30000)
							$a = $a + 1
						ElseIf $a == 4 Then
							$sQuery = "UPDATE autentica_instagram SET segundo_fator = 6 WHERE id = '"& $sId_conta &"' "
							$oConnection.Execute($sQuery)
							MouseClick("Left", 1896, 17, 1)
							Exit					
						EndIf
					WEnd
				Else
					$sQuery = "UPDATE autentica_instagram SET segundo_fator = 5 WHERE id = '"& $sId_conta &"' "
					$oConnection.Execute($sQuery)
					Sleep(10000)
					
				EndIf
			
			EndIf
		Else	
			Sleep(10000)	
			ConsoleWrite("instagram logado")
		EndIf
	MouseClick("Left", 1896, 17, 1)
Sleep(10000)	


#ce


#cs

; Executar query SELECT
$oRecordset.Open("SELECT status FROM robo WHERE nome_acc = 'insta-01' ", $oConnection)
If @error Then
    MsgBox($MB_ICONERROR, "Erro", "Falha na query SELECT: " & @error)
    Exit
EndIf

; Exibir resultados
Local $aResult
If Not $oRecordset.EOF Then
    $aResult = $oRecordset.GetRows()
    ;_ArrayDisplay($aResult, "Dados da tabela teste")
Else
    MsgBox($MB_ICONINFORMATION, "Info", "Nenhum dado encontrado")
EndIf
Local $a = $aResult[0][0]



;MsgBox(0, "Teste", $aResult[0][0])
; Fechar Recordset

if $a <> 'Livre' Then
	;MsgBox(0, "Teste", $aResult[0][0])
	$oRecordset.Close
	Local $sQuery = "UPDATE robo SET status = 'Ocupado' WHERE nome_acc = 'insta-01'"
	$oConnection.Execute($sQuery)
	Sleep(600)
	; Executar query SELECT
	$oRecordset.Open("SELECT * FROM tarefas WHERE status_tarefa = 'Aguardando' LIMIT 1 ", $oConnection)
	If @error Then
		MsgBox($MB_ICONERROR, "Erro", "Falha na query SELECT: " & @error)
		Exit
	EndIf
	; Exibir resultados
	Local $atarefas
	If Not $oRecordset.EOF Then
		$aTarefas = $oRecordset.GetRows()
		;_ArrayDisplay($aResult, "Dados da tabela teste")
	Else
		MsgBox($MB_ICONINFORMATION, "Info", "Nenhum dado encontrado")
	EndIf
		MsgBox(0, "Teste", $aTarefas[0][0])
		Local $sQuery = "UPDATE tarefas SET status_tarefa = 'Executando' WHERE id = $id_tarefa"
		$oConnection.Execute($sQuery)
		$id_tarefa = $aTarefas[0][0]
		$link_tarefa = $aTarefas[0][6]
		
		
;---------- tarefa informações perfil -----------
		Sleep(600)
		MouseClick("Left", 1361, 23, 1)
		Sleep(300)
		Send("{Del}")
		Sleep(300)	
		ClipPut($link_tarefa)
		Send("^v")
		Sleep(600)
		Send("{Enter}")
		Sleep(1000)
		Send("{F12}")
		Sleep(300)
		MouseClick("Right", 1402, 244, 1)
		Sleep(600)
		MouseClick("Left", 1488, 296, 1)
		Sleep(600)
		Send("^a")
		Sleep(300)
		Send("^c")
		Sleep(300)
		$sClipboard = ClipGet()
		Sleep(300)
		FileWrite($sFilePath, $sClipboard)
		Send("{F12}")
;--------------tarefa lista de seguidores---------
	
		
		
		
		
		
		
	
	
	
	
	
	
Else
	MsgBox(0, "Teste", "Erro")
EndIf


#ce


















