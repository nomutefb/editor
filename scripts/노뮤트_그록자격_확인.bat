@echo off
REM ===========================================================================
REM  nomute - Grok subscription entitlement probe : DOUBLE-CLICK, RUN ONCE
REM
REM  What it does: opens the xAI device-code login in your browser, then makes
REM  ONE real API call with your X Premium+ / SuperGrok entitlement and prints
REM  PASS or REFUSED with the server's own words.
REM
REM  Installs nothing. Registers nothing. Nothing is left running.
REM  Results are written to your Desktop.
REM
REM  GENERATED FILE - do not edit by hand.
REM  Source of truth: scripts/grok_probe.ps1
REM  Regenerate     : python3 scripts/build_grok_probe_bundle.py
REM ===========================================================================
setlocal
chcp 65001 >nul 2>&1
set "NM=%TEMP%\nomute_grok"
if not exist "%NM%" mkdir "%NM%"
set "B64=%NM%\_probe.b64"
if exist "%B64%" del "%B64%"

echo.
echo   Unpacking...
>> "%B64%" echo 77u/IyBncm9rX3Byb2JlLnBzMSDigJQgWCjsl5HsiqQpIOq1rOuPhSDsnpDqsqnsnLzroZwgR3Jv
>> "%B64%" echo ayBBUEkg66W8IOu2gOulvCDsiJgg7J6I64qU7KeAIOyLpO2YuOy2nOuhnCDtjJDsoJXtlZzri6Qu
>> "%B64%" echo DQojDQojIOuwsOqyvSgyNjA4MTAgwrcg7Jq07JiB7J6QICLsnbTrr7gg64K06rCAIOqwgOyngOqz
>> "%B64%" echo oCDsnojripQgeOqzhOygleyXkCDsho3tlZwg6re466GdIG9hdXRoIOulvCDrubzshJwg67Cw7ISg
>> "%B64%" echo 7Iuc7YKsIOyImCDsnojripQg67Cp67KV7J6I64KYPyIpOg0KIyAgIHhBSSDqsIAgMjAyNi0wNSDr
>> "%B64%" echo toDthLAg6rWs64+F7J6Q7JqpIE9BdXRoIOulvCDsl7Tsl4jri6Qg4oCUIEFQSSDtgqQo7KKF65+J
>> "%B64%" echo 7KCcKSDsl4bsnbQgU3VwZXJHcm9rIC8gWCBQcmVtaXVtKyDsnpDqsqnrp4zsnLzroZwNCiMgICBo
>> "%B64%" echo dHRwczovL2FwaS54LmFpL3YxIOulvCDrtoDrpbjri6QuIOuLpOunjCDrsLHsl5Trk5zqsIAg6re4
>> "%B64%" echo IO2GteuhnOyXkCDsnpDssrQg7ZeI7Jqp66qp66Gd7J2EIOqxuOqzoCDsnojri6TripQg7Iug6rOg
>> "%B64%" echo 6rCAIOuLpOyImCDsnojslrQNCiMgICAqKuyasOumrCDqs4TsoJXsnbQg65CY64qU7KeA64qUIOyL
>> "%B64%" echo pO2YuOy2nOuhnOunjCDslYwg7IiYIOyeiOuLpCoqIOKGkiDsnbQg7YyM7J287J2AIOq3uCDtlZwg
>> "%B64%" echo 6rCA7KeA66eMIO2VnOuLpC4NCiMNCiMg4pqgIO2MkOygleq4sOuLpC4g67Cw7ISgIOyVhOuLmCjr
>> "%B64%" echo oIjtj6wg65287J2067iMIOustOygkey0iSDCtyDsnpDrj5kg7Iuk7ZaJIDAgwrcg7JWIIOuPjOum
>> "%B64%" echo rOuptCDslYTrrLQg7J2864+EIOyViCDsnbzslrTrgpzri6QpLg0KIw0KIyDtjIzsnbTsjawg7YyQ
>> "%B64%" echo KHNoYXJlZC9ncm9rX29hdXRoX3Byb2JlLnB5KeqzvCDqsJnsnYAg7YyQ7KCV7J2EIO2VmOuQmCwg
>> "%B64%" echo 7Jq07JiB7J6QIFBDIOyXkOyEnCAqKuuNlOu4lO2BtOumrSAx7ZqMKirroZwg64Gd64KY6rKMDQoj
>> "%B64%" echo IO2MjOybjOyFuOuhnCDsmK7quLQg7IKs67O47J2064ukKDI2MDgxMCDsi6TsuKEgPSDsnIjrj4Ts
>> "%B64%" echo mrDsl5DshJwgcHl0aG9uMyDqsIAg7Zeb64+M6rOgIOyLpO2WiSDtj7TrjZTrj4Qg7Ja06riL64Ks
>> "%B64%" echo 64ukID0g7LKrIOyLpO2WiSDsnqXslaDrpbwNCiMg7L2U65Oc66GcIO2doeyImCDCtyBDTEFVREUg
>> "%B64%" echo WzktM10pLg0KIw0KIyDsgrDstpw6ICDrsJTtg5XtmZTrqbRc6re466Gd7ZmV7J24X+qysOqzvC50
>> "%B64%" echo eHQgKOq4sOuhnSDCtyDthqDtgbDsnYAg7JWeIDEy7J6Q66eMIOuCqOq4sOqzoCDqsIDrprDri6Qp
>> "%B64%" echo DQojICAgICAgICDrsJTtg5XtmZTrqbRc6re466Gd7Yag7YGwLmpzb24gICAgICjthrXqs7ztlojs
>> "%B64%" echo nYQg65WM66eMIMK3IOuwsOyEoCDsnqzro4wgwrcg64Ko7JeQ6rKMIOyjvOyngCDrp4jrnbwpDQoj
>> "%B64%" echo ICAgICAgICDrsJTtg5XtmZTrqbRc6re466GdX+q3uOumvC5qcGcgICAgICAo6re466a87J20IOyX
>> "%B64%" echo tOugpCDsnojsnLzrqbQg7Iuk66y8IDHsnqUpDQojICAgICAgICDrsJTtg5XtmZTrqbRc6re466Gd
>> "%B64%" echo X+yYgeyDgS5tcDQgICAgICAo7JiB7IOB7J20IOyXtOugpCDsnojsnLzrqbQg7Iuk66y8IDHtjrgg
>> "%B64%" echo PSAxMOy0iCA3MjBwIMK3IOyGjOumrCDtj6ztlagpDQojIOuBhOuKlCDrspU6IOyViCDrj4zrpqzr
>> "%B64%" echo qbQg64GdLiDshKTsuZjrkJjripQg6rKD64+ELCDsnpDrj5kg7Iuk7ZaJ65CY64qUIOqyg+uPhCDs
>> "%B64%" echo l4bri6QuDQoNCiRFcnJvckFjdGlvblByZWZlcmVuY2UgPSAiU3RvcCINCnRyeSB7IFtOZXQuU2Vy
>> "%B64%" echo dmljZVBvaW50TWFuYWdlcl06OlNlY3VyaXR5UHJvdG9jb2wgPSBbTmV0LlNlY3VyaXR5UHJvdG9j
>> "%B64%" echo b2xUeXBlXTo6VGxzMTIgfSBjYXRjaCB7fQ0KdHJ5IHsgJE91dHB1dEVuY29kaW5nID0gW0NvbnNv
>> "%B64%" echo bGVdOjpPdXRwdXRFbmNvZGluZyA9IFtUZXh0LkVuY29kaW5nXTo6VVRGOCB9IGNhdGNoIHt9DQoN
>> "%B64%" echo CiRDTElFTlRfSUQgPSAiYjFhMDA0OTItMDczYS00N2VhLTgxNmYtNGMzMjkyNjRhODI4IiAgICMg
>> "%B64%" echo eEFJIOqzteqwnCDrjbDsiqTtgazthrEg7YG065287J207Ja47Yq4KOu5hOuwgO2CpCDsl4bsnYwp
>> "%B64%" echo DQokU0NPUEUgICAgID0gIm9wZW5pZCBwcm9maWxlIGVtYWlsIG9mZmxpbmVfYWNjZXNzIGdyb2st
>> "%B64%" echo Y2xpOmFjY2VzcyBhcGk6YWNjZXNzIg0KJERJU0NPVkVSWSA9ICJodHRwczovL2F1dGgueC5haS8u
>> "%B64%" echo d2VsbC1rbm93bi9vcGVuaWQtY29uZmlndXJhdGlvbiINCiRBUElfQkFTRSAgPSAiaHR0cHM6Ly9h
>> "%B64%" echo cGkueC5haS92MSINCiRNT0RFTFMgICAgPSBAKCJncm9rLTQuNSIsImdyb2stNC4zIiwiZ3Jvay0z
>> "%B64%" echo IiwiZ3Jvay1iZXRhIikNCg0KIyDimqAg67CU7YOV7ZmU66m0IOqyveuhnOuKlCDruYgg66y47J6Q
>> "%B64%" echo 7Je066GcIOyYrCDsiJgg7J6I64ukKOybkOuTnOudvOydtOu4jCDrsLHsl4XCt+u5hOyciOuPhOya
>> "%B64%" echo sCDtmZjqsr0g7Iuk7LihKSDihpIg7Y+067CxIOyCrOyKrC4NCiMgICDtlZwg7Lm47J20652864+E
>> "%B64%" echo IOu5hOuptCBKb2luLVBhdGgg6rCAIOq3uCDsnpDrpqzsl5DshJwg7KO97Ja0IO2MkOyglSDsnpDs
>> "%B64%" echo srTrpbwg66q7IO2VnOuLpCjssqsg7Iuk7ZaJIOyLpOy4oSDrtIntlakpLg0KJERlc2sgPSAiIg0K
>> "%B64%" echo IyAo4pqgIEpvaW4tUGF0aCDripQg67mIIOqwkuydhCDrsJvsnLzrqbQg6re4IOyekOumrOyXkOyE
>> "%B64%" echo nCDso73ripTri6QgPSDtj7TrsLHsnbQg7Y+067CxIOyghOyXkCDthLDsp4Tri6Qg4oaSIOusuOye
>> "%B64%" echo kOyXtOuhnOunjCDsnofripTri6QpDQpmb3JlYWNoICgkYyBpbiBAKFtFbnZpcm9ubWVudF06Okdl
>> "%B64%" echo dEZvbGRlclBhdGgoIkRlc2t0b3AiKSwNCiAgICAgICAgICAgICAgICAgIiRlbnY6VVNFUlBST0ZJ
>> "%B64%" echo TEVcRGVza3RvcCIsICIkZW52OlVTRVJQUk9GSUxFIiwgIiRlbnY6VEVNUCIsIChHZXQtTG9jYXRp
>> "%B64%" echo b24pLlBhdGgpKSB7DQogIGlmICgkYyAtYW5kICRjLlRyaW0oKSAtYW5kIChUZXN0LVBhdGggLUxp
>> "%B64%" echo dGVyYWxQYXRoICRjKSkgeyAkRGVzayA9ICRjOyBicmVhayB9DQp9DQppZiAoLW5vdCAkRGVzaykg
>> "%B64%" echo eyAkRGVzayA9ICIuIiB9DQokTG9nUGF0aCAgID0gSm9pbi1QYXRoICREZXNrICLqt7jroZ3tmZXs
>> "%B64%" echo nbhf6rKw6rO8LnR4dCINCiRUb2tlblBhdGggPSBKb2luLVBhdGggJERlc2sgIuq3uOuhne2GoO2B
>> "%B64%" echo sC5qc29uIg0KJEltZ1BhdGggICA9IEpvaW4tUGF0aCAkRGVzayAi6re466GdX+q3uOumvC5qcGci
>> "%B64%" echo DQokVmlkUGF0aCAgID0gSm9pbi1QYXRoICREZXNrICLqt7jroZ1f7JiB7IOBLm1wNCINCiRzY3Jp
>> "%B64%" echo cHQ6TG9nID0gTmV3LU9iamVjdCBTeXN0ZW0uQ29sbGVjdGlvbnMuQXJyYXlMaXN0DQoNCmZ1bmN0
>> "%B64%" echo aW9uIFNheSgkdCkgeyBXcml0ZS1Ib3N0ICR0OyBbdm9pZF0kc2NyaXB0OkxvZy5BZGQoJHQpIH0N
>> "%B64%" echo CmZ1bmN0aW9uIE1hc2soJHMpIHsgaWYgKCRzIC1hbmQgJHMuTGVuZ3RoIC1ndCAxMikgeyAkcy5T
>> "%B64%" echo dWJzdHJpbmcoMCwxMikgKyAi4oCmPCIgKyAkcy5MZW5ndGggKyAi7J6QIOqwgOumvD4iIH0gZWxz
>> "%B64%" echo ZSB7ICRzIH0gfQ0KZnVuY3Rpb24gQ3V0KCR0LCAkbikgeyAkdCA9ICIkdCIgLXJlcGxhY2UgIlxz
>> "%B64%" echo KyIsICIgIjsgaWYgKCR0Lkxlbmd0aCAtZ3QgJG4pIHsgJHQuU3Vic3RyaW5nKDAsICRuKSB9IGVs
>> "%B64%" echo c2UgeyAkdCB9IH0NCmZ1bmN0aW9uIENvc3QoJG8pIHsgdHJ5IHsgcmV0dXJuIFtNYXRoXTo6Um91
>> "%B64%" echo bmQoW2RvdWJsZV0kby51c2FnZS5jb3N0X2luX3VzZF90aWNrcyAvIDFlMTAsIDQpIH0gY2F0Y2gg
>> "%B64%" echo eyByZXR1cm4gMCB9IH0NCmZ1bmN0aW9uIFNhdmVMb2cgeyB0cnkgeyAkc2NyaXB0OkxvZyAtam9p
>> "%B64%" echo biAiYHJgbiIgfCBPdXQtRmlsZSAtRmlsZVBhdGggJExvZ1BhdGggLUVuY29kaW5nIFVURjggfSBj
>> "%B64%" echo YXRjaCB7fSB9DQoNCiMg7IOB7YOc7L2U65Oc6rmM7KeAIOuwm+yVhOyYpOuKlCDsmpTssq3quLAo
>> "%B64%" echo 7YyM7JuM7IW4IDUuMSDsl5DshKAg7Iuk7YyoIOydkeuLtSDrs7jrrLjsnYQg7KeB7KCRIOydveyW
>> "%B64%" echo tOyVvCDtlZzri6QpDQpmdW5jdGlvbiBXZWIoJHVybCwgJGJvZHksICR0b2tlbiwgJG1ldGhvZCkg
>> "%B64%" echo ew0KICAkaCA9IEB7fQ0KICBpZiAoJHRva2VuKSB7ICRoWyJBdXRob3JpemF0aW9uIl0gPSAiQmVh
>> "%B64%" echo cmVyICR0b2tlbiIgfQ0KICAkcCA9IEB7IFVyaSA9ICR1cmw7IEhlYWRlcnMgPSAkaDsgVGltZW91
>> "%B64%" echo dFNlYyA9IDkwOyBVc2VCYXNpY1BhcnNpbmcgPSAkdHJ1ZSB9DQogIGlmICgkbWV0aG9kKSB7ICRw
>> "%B64%" echo WyJNZXRob2QiXSA9ICRtZXRob2QgfSBlbHNlaWYgKCRib2R5KSB7ICRwWyJNZXRob2QiXSA9ICJQ
>> "%B64%" echo T1NUIiB9IGVsc2UgeyAkcFsiTWV0aG9kIl0gPSAiR0VUIiB9DQogIGlmICgkYm9keSAtaXMgW2hh
>> "%B64%" echo c2h0YWJsZV0pIHsgJHBbIkJvZHkiXSA9ICRib2R5OyAkcFsiQ29udGVudFR5cGUiXSA9ICJhcHBs
>> "%B64%" echo aWNhdGlvbi94LXd3dy1mb3JtLXVybGVuY29kZWQiIH0NCiAgZWxzZWlmICgkYm9keSkgeyAkcFsi
>> "%B64%" echo Qm9keSJdID0gW1RleHQuRW5jb2RpbmddOjpVVEY4LkdldEJ5dGVzKCRib2R5KTsgJHBbIkNvbnRl
>> "%B64%" echo bnRUeXBlIl0gPSAiYXBwbGljYXRpb24vanNvbiIgfQ0KICB0cnkgew0KICAgICRyID0gSW52b2tl
>> "%B64%" echo LVdlYlJlcXVlc3QgQHANCiAgICAkdHh0ID0gJHIuQ29udGVudA0KICAgICRvYmogPSAkbnVsbDsg
>> "%B64%" echo dHJ5IHsgJG9iaiA9ICR0eHQgfCBDb252ZXJ0RnJvbS1Kc29uIH0gY2F0Y2gge30NCiAgICByZXR1
>> "%B64%" echo cm4gQHsgY29kZSA9IFtpbnRdJHIuU3RhdHVzQ29kZTsgdGV4dCA9ICR0eHQ7IG9iaiA9ICRvYmog
>> "%B64%" echo fQ0KICB9IGNhdGNoIHsNCiAgICAjIOKaoCDtjIzsm4zshbggNS4xIOqzvCA3IOydtCDsi6TtjKgg
>> "%B64%" echo 7J2R64u17J2EIOuLpOultOqyjCDrhJjquLTri6Qg4oCUIDUuMeydgCBSZXNwb25zZSDsiqTtirjr
>> "%B64%" echo prwsIDfsnYAgRXJyb3JEZXRhaWxzLg0KICAgICMgICDtlZzsqr3rp4wg7J297Jy866m0ICLshJzr
>> "%B64%" echo soTqsIAg662Q65286rOgIOqxsOygiO2WiOuKlOyngCLqsIAg7Ya17Ke466GcIOyCrOudvOynhOuL
>> "%B64%" echo pCg9IOydtCDtjJDsoJXquLDsnZgg7KG07J6sIOydtOycoOqwgCDsgqzrnbzsp4Tri6QpLg0KICAg
>> "%B64%" echo ICRjb2RlID0gMDsgJHR4dCA9ICIkKCRfLkV4Y2VwdGlvbi5NZXNzYWdlKSINCiAgICB0cnkgeyBp
>> "%B64%" echo ZiAoJF8uRXJyb3JEZXRhaWxzIC1hbmQgJF8uRXJyb3JEZXRhaWxzLk1lc3NhZ2UpIHsgJHR4dCA9
>> "%B64%" echo ICRfLkVycm9yRGV0YWlscy5NZXNzYWdlIH0gfSBjYXRjaCB7fQ0KICAgICRyZXNwID0gJG51bGwN
>> "%B64%" echo CiAgICB0cnkgeyAkcmVzcCA9ICRfLkV4Y2VwdGlvbi5SZXNwb25zZSB9IGNhdGNoIHt9DQogICAg
>> "%B64%" echo aWYgKCRyZXNwKSB7DQogICAgICB0cnkgeyAkY29kZSA9IFtpbnRdJHJlc3AuU3RhdHVzQ29kZSB9
>> "%B64%" echo IGNhdGNoIHt9DQogICAgICBpZiAoJHR4dCAtZXEgIiQoJF8uRXhjZXB0aW9uLk1lc3NhZ2UpIikg
>> "%B64%" echo ew0KICAgICAgICB0cnkgew0KICAgICAgICAgICRzciA9IE5ldy1PYmplY3QgSU8uU3RyZWFtUmVh
>> "%B64%" echo ZGVyKCRyZXNwLkdldFJlc3BvbnNlU3RyZWFtKCkpDQogICAgICAgICAgJHR4dCA9ICRzci5SZWFk
>> "%B64%" echo VG9FbmQoKTsgJHNyLkNsb3NlKCkNCiAgICAgICAgfSBjYXRjaCB7fQ0KICAgICAgfQ0KICAgIH0N
>> "%B64%" echo CiAgICAkb2JqID0gJG51bGw7IHRyeSB7ICRvYmogPSAkdHh0IHwgQ29udmVydEZyb20tSnNvbiB9
>> "%B64%" echo IGNhdGNoIHt9DQogICAgcmV0dXJuIEB7IGNvZGUgPSAkY29kZTsgdGV4dCA9ICR0eHQ7IG9iaiA9
>> "%B64%" echo ICRvYmogfQ0KICB9DQp9DQoNCmZ1bmN0aW9uIFN0b3AtQmFkKCR0aXRsZSwgJGRldGFpbCwgJGhp
>> "%B64%" echo bnQpIHsNCiAgU2F5ICIiDQogIFNheSAoIj0iICogNTgpDQogIFNheSAiW1hdICR0aXRsZSINCiAg
>> "%B64%" echo U2F5ICgiPSIgKiA1OCkNCiAgU2F5ICRkZXRhaWwNCiAgaWYgKCRoaW50KSB7IFNheSAiIjsgU2F5
>> "%B64%" echo ICRoaW50IH0NCiAgU2F5ICIiDQogIFNheSAi6riw66GdOiAkTG9nUGF0aCINCiAgU2F2ZUxvZw0K
>> "%B64%" echo ICBXcml0ZS1Ib3N0ICIiDQogIFJlYWQtSG9zdCAi7JeU7YSw66W8IOuIhOultOuptCDssL3snbQg
>> "%B64%" echo 64ur7Z6M64ukIg0KICBleGl0IDENCn0NCg0KIyDilIDilIAg7KCA7J6l65CcIOyXtOyHoOqwgCDs
>> "%B64%" echo nojsnLzrqbQg66Gc6re47J247J2EIOqxtOuEiOubtOuLpCDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIANCiMg4pqgIOyVoeyEuOyKpCDthqDtgbAoNuyLnOqwhCns
>> "%B64%" echo nYAg7KO97Ja064+EICoq6rCx7IugIOyXtOyHoOuKlCDsgrDri6QqKiDihpIg7ZWcIOuyiCDroZzq
>> "%B64%" echo t7jsnbjtlojsnLzrqbQg64uk7IucIOyLnO2CrCDsnbTsnKDqsIAg7JeG64ukLg0KIyAgIOq3uOuh
>> "%B64%" echo neydgCDqsLHsi6DtlaAg65WM66eI64ukIOyXtOyHoOulvCDsg4jqsoPsnLzroZwg67CU6r+U7KO8
>> "%B64%" echo 66+A66GcKO2ajOyghCkg67Cb7J2AIOyDiCDsl7Tsh6Drpbwg6re4IOyekOumrOyXkOyEnCDri6Ts
>> "%B64%" echo i5wg7KCA7J6l7ZWc64ukLg0KIyAgIOyggOyepeydhCDrubzrqLnsnLzrqbQg64uk7J2MIOyLpO2W
>> "%B64%" echo ieu2gO2EsCDsobDsmqntnogg64GK6ri064ukIOKAlCDqt7jrnpjshJwg6rCx7Iug6rO8IOyggOye
>> "%B64%" echo peydgCDtlZwg66q47J2064ukLg0KZnVuY3Rpb24gVHJ5U3RvcmVkKCR0b2tVcmwpIHsNCiAgaWYg
>> "%B64%" echo KC1ub3QgKFRlc3QtUGF0aCAtTGl0ZXJhbFBhdGggJFRva2VuUGF0aCkpIHsgcmV0dXJuICRudWxs
>> "%B64%" echo IH0NCiAgJGtlZXAgPSAkbnVsbA0KICB0cnkgeyAka2VlcCA9IEdldC1Db250ZW50IC1MaXRlcmFs
>> "%B64%" echo UGF0aCAkVG9rZW5QYXRoIC1SYXcgLUVuY29kaW5nIFVURjggfCBDb252ZXJ0RnJvbS1Kc29uIH0g
>> "%B64%" echo Y2F0Y2ggeyByZXR1cm4gJG51bGwgfQ0KICBpZiAoLW5vdCAka2VlcC5yZWZyZXNoX3Rva2VuKSB7
>> "%B64%" echo IHJldHVybiAkbnVsbCB9DQogIFNheSAiICDsoIDsnqXrkJwg7Je07Ieg66W8IOywvuyVmOuLpCAt
>> "%B64%" echo IOuhnOq3uOyduOydhCDqsbTrhIjrm7Tri6QiDQogICRyID0gV2ViICR0b2tVcmwgQHsgY2xpZW50
>> "%B64%" echo X2lkID0gJENMSUVOVF9JRDsgZ3JhbnRfdHlwZSA9ICJyZWZyZXNoX3Rva2VuIjsgcmVmcmVzaF90
>> "%B64%" echo b2tlbiA9ICRrZWVwLnJlZnJlc2hfdG9rZW4gfSAkbnVsbCAiUE9TVCINCiAgaWYgKCRyLmNvZGUg
>> "%B64%" echo LW5lIDIwMCAtb3IgLW5vdCAkci5vYmouYWNjZXNzX3Rva2VuKSB7DQogICAgU2F5ICIgICjsoIDs
>> "%B64%" echo nqXrkJwg7Je07Ieg6rCAIOyViCDrqLnripTri6QgSFRUUCAkKCRyLmNvZGUpIC0gJChDdXQgJHIu
>> "%B64%" echo dGV4dCAxNjApKSAtPiDroZzqt7jsnbjrtoDthLAg64uk7IucIO2VnOuLpCINCiAgICByZXR1cm4g
>> "%B64%" echo JG51bGwNCiAgfQ0KICAkbmV3UnQgPSAkci5vYmoucmVmcmVzaF90b2tlbg0KICBpZiAoJG5ld1J0
>> "%B64%" echo KSB7DQogICAgdHJ5IHsNCiAgICAgICRrZWVwIHwgQWRkLU1lbWJlciAtTm90ZVByb3BlcnR5TmFt
>> "%B64%" echo ZSByZWZyZXNoX3Rva2VuIC1Ob3RlUHJvcGVydHlWYWx1ZSAkbmV3UnQgLUZvcmNlDQogICAgICAk
>> "%B64%" echo a2VlcCB8IEFkZC1NZW1iZXIgLU5vdGVQcm9wZXJ0eU5hbWUgc2F2ZWRfYXQgLU5vdGVQcm9wZXJ0
>> "%B64%" echo eVZhbHVlIChHZXQtRGF0ZSkuVG9TdHJpbmcoInl5eXktTU0tZGQgSEg6bW06c3MiKSAtRm9yY2UN
>> "%B64%" echo CiAgICAgICRrZWVwIHwgQ29udmVydFRvLUpzb24gLURlcHRoIDUgfCBPdXQtRmlsZSAtRmlsZVBh
>> "%B64%" echo dGggJFRva2VuUGF0aCAtRW5jb2RpbmcgVVRGOA0KICAgIH0gY2F0Y2ggeyBTYXkgIiAgWyFdIOyD
>> "%B64%" echo iCDsl7Tsh6Ag7KCA7J6lIOyLpO2MqCAtIOuLpOydjCDsi6Ttlokg65WMIOuhnOq3uOyduOydtCDt
>> "%B64%" echo lYTsmpTtlaAg7IiYIOyeiOuLpCA6ICRfIiB9DQogIH0NCiAgU2F5ICIgIFtPS10g7J6Q6rKpIOuQ
>> "%B64%" echo mOyCtOuguOuLpCINCiAgcmV0dXJuICRyLm9iai5hY2Nlc3NfdG9rZW4NCn0NCg0KDQojIOKUgOKU
>> "%B64%" echo gCAy64uo6rOEID0g6re466a8wrfsmIHsg4HsnbQg7J20IOyekOqyqeyXkCDsl7TroKQg7J6I64KY
>> "%B64%" echo ICsg7Iuk66y86rmM7KeAIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgA0KIyDimqAg7JmcIOyLpOusvOq5jOyngCDqtb3rgpgo
>> "%B64%" echo MjYwODEwIO2OmOydtOu4lCDqsoDthqAg7LmY66qF4pGgKSA9IOq4gCDrqqjrjbjsnbQg7Ya16rO8
>> "%B64%" echo 7ZaI64uk6rOgIOq3uOumvMK37JiB7IOB6rmM7KeAIOyXtOumsCDqsowg7JWE64uI64ukLg0KIyAg
>> "%B64%" echo IHhBSSDqsIAg6rWs64+FIO2GteuhnOyXkCDsnpDssrQg7ZeI7Jqp66qp66Gd7J2EIOqxuOyWtCDq
>> "%B64%" echo tazrj4XsnbQg7IK07JWEIOyeiOyWtOuPhCDqsbDsoIjtlZwg7IKs66GA6rCAIOuztOqzoOuPvCDs
>> "%B64%" echo nojqs6AsDQojICAg7Jqw66asIO2ZlOuptMK36rOg7KCV6rCSwrftlITroaztlITtirgg7KCV67O4
>> "%B64%" echo IOyghOyytOqwgCDjgIzrkJzri6TjgI3rpbwg7KCE7KCc66GcIOyEnCDsnojri6QuIOyXrOq4sOqw
>> "%B64%" echo gCDssqsg6rSA66y47J2064ukLg0KZnVuY3Rpb24gTWVkaWEoJGF0KSB7DQogIGZvcmVhY2ggKCRr
>> "%B64%" echo aW5kIGluIEAoImltYWdlIiwgInZpZGVvIikpIHsNCiAgICAkciA9IFdlYiAiJEFQSV9CQVNFLyRr
>> "%B64%" echo aW5kLWdlbmVyYXRpb24tbW9kZWxzIiAkbnVsbCAkYXQgIkdFVCINCiAgICBpZiAoJHIuY29kZSAt
>> "%B64%" echo ZXEgMjAwIC1hbmQgJHIub2JqKSB7DQogICAgICAkaWRzID0gQCgpDQogICAgICBmb3JlYWNoICgk
>> "%B64%" echo bSBpbiBAKCRyLm9iai5tb2RlbHMpKSB7IGlmICgkbSAtYW5kICRtLmlkKSB7ICRpZHMgKz0gJG0u
>> "%B64%" echo aWQgfSB9DQogICAgICBmb3JlYWNoICgkbSBpbiBAKCRyLm9iai5kYXRhKSkgICB7IGlmICgkbSAt
>> "%B64%" echo YW5kICRtLmlkKSB7ICRpZHMgKz0gJG0uaWQgfSB9DQogICAgICBTYXkgIiAgWyRraW5kXSDsl7Tr
>> "%B64%" echo prAg66qo6424ICQoJGlkcy5Db3VudCnqsJwgOiAkKCRpZHMgLWpvaW4gJywgJykiDQogICAgfSBl
>> "%B64%" echo bHNlIHsNCiAgICAgIFNheSAiICBbJGtpbmRdIOuqqeuhnSDsi6TtjKggSFRUUCAkKCRyLmNvZGUp
>> "%B64%" echo IC0gJChDdXQgJHIudGV4dCAyMDApIg0KICAgIH0NCiAgfQ0KDQogIFNheSAiIg0KICBTYXkgIiAg
>> "%B64%" echo 6re466a8IOq1veuKlCDspJEuLi4gKDEw7LSIIOyViO2MjikiDQogICRpcCA9IEB7IG1vZGVsID0g
>> "%B64%" echo Imdyb2staW1hZ2luZS1pbWFnZSI7IHByb21wdCA9ICJFZGl0b3JpYWwgaWxsdXN0cmF0aW9uIG9m
>> "%B64%" echo IGEgcXVpZXQgbmV3c3Jvb20gYXQgZGF3biwgb25lIGVtcHR5IGRlc2ssIHdhcm0gYW1iZXIgbGln
>> "%B64%" echo aHQgZnJvbSB0aGUgbGVmdCwgY2FsbSBibHVlIHNoYWRvd3MuIjsgbiA9IDE7IHJlc3BvbnNlX2Zv
>> "%B64%" echo cm1hdCA9ICJiNjRfanNvbiI7IGFzcGVjdF9yYXRpbyA9ICIxNjo5IjsgcmVzb2x1dGlvbiA9ICIx
>> "%B64%" echo ayIgfSB8IENvbnZlcnRUby1Kc29uIC1Db21wcmVzcw0KICAkciA9IFdlYiAiJEFQSV9CQVNFL2lt
>> "%B64%" echo YWdlcy9nZW5lcmF0aW9ucyIgJGlwICRhdCAiUE9TVCINCiAgaWYgKCRyLmNvZGUgLWVxIDIwMCAt
>> "%B64%" echo YW5kICRyLm9iai5kYXRhKSB7DQogICAgdHJ5IHsNCiAgICAgIFtJTy5GaWxlXTo6V3JpdGVBbGxC
>> "%B64%" echo eXRlcygkSW1nUGF0aCwgW0NvbnZlcnRdOjpGcm9tQmFzZTY0U3RyaW5nKCRyLm9iai5kYXRhWzBd
>> "%B64%" echo LmI2NF9qc29uKSkNCiAgICAgIFNheSAiICBbT0tdIOq3uOumvCDrgpjsmZTri6QgLT4gJEltZ1Bh
>> "%B64%" echo dGggICAo7LKt6rWsICQoQ29zdCAkci5vYmopIOuLrOufrCkiDQogICAgfSBjYXRjaCB7IFNheSAi
>> "%B64%" echo ICBbIV0g6re466a87J2AIOuwm+yVmOuKlOuNsCDsoIDsnqUg7Iuk7YyoIDogJF8iIH0NCiAgfSBl
>> "%B64%" echo bHNlIHsNCiAgICBTYXkgIiAgW1hdIOq3uOumvCDqsbDsoIggSFRUUCAkKCRyLmNvZGUpIC0gJChD
>> "%B64%" echo dXQgJHIudGV4dCAzMDApIg0KICB9DQoNCiAgU2F5ICIiDQogIFNheSAiICDsmIHsg4Eg67Cc7IKs
>> "%B64%" echo Li4uICjrqocg67aEIOqxuOumsOuLpC4g7LC9IOuLq+yngCDrp4jrnbwpIg0KICAkdnAgPSBAeyBt
>> "%B64%" echo b2RlbCA9ICJncm9rLWltYWdpbmUtdmlkZW8tMS41IjsgcHJvbXB0ID0gIkEgc2luZ2xlIHNoZWV0
>> "%B64%" echo IG9mIHBhcGVyIGxpZnRzIG9mZiB0aGUgZGVzayBhbmQgZHJpZnRzIHNsb3dseSB0aHJvdWdoIHN0
>> "%B64%" echo aWxsIG1vcm5pbmcgYWlyLiBDYW1lcmEgaG9sZHMgbG9ja2VkIGFuZCBzdGF0aWMuIFdhcm0gYW1i
>> "%B64%" echo ZXIgbGlnaHQsIGNhbG0gYmx1ZSBzaGFkb3dzLCBwYWxlIGdyZXkgd2FsbHMuIFNvdW5kOiBmYWlu
>> "%B64%" echo dCBwYXBlciBmbHV0dGVyLCBkaXN0YW50IHRyYWZmaWMgbXVmZmxlZCB0aHJvdWdoIGdsYXNzLCBx
>> "%B64%" echo dWlldCByb29tIHRvbmUuIjsgZHVyYXRpb24gPSAxMDsgcmVzb2x1dGlvbiA9ICI3MjBwIjsgYXNw
>> "%B64%" echo ZWN0X3JhdGlvID0gIjE2OjkiIH0gfCBDb252ZXJ0VG8tSnNvbiAtQ29tcHJlc3MNCiAgJHIgPSBX
>> "%B64%" echo ZWIgIiRBUElfQkFTRS92aWRlb3MvZ2VuZXJhdGlvbnMiICR2cCAkYXQgIlBPU1QiDQogIGlmICgk
>> "%B64%" echo ci5jb2RlIC1uZSAyMDAgLW9yIC1ub3QgJHIub2JqLnJlcXVlc3RfaWQpIHsNCiAgICBTYXkgIiAg
>> "%B64%" echo W1hdIOyYgeyDgSDqsbDsoIggSFRUUCAkKCRyLmNvZGUpIC0gJChDdXQgJHIudGV4dCA0MDApIg0K
>> "%B64%" echo ICAgIGlmICgkci5jb2RlIC1lcSA0MDMpIHsgU2F5ICIgICAgICA0MDMgPSDqtazrj4XsnYAg7IK0
>> "%B64%" echo 7JWEIOyeiOuKlOuNsCB4QUkg6rCAIOyYgeyDgSDthrXroZzrpbwg7J20IOqzhOygleyXkCDslYgg
>> "%B64%" echo 7Je07Ja07KSAIOqyg+ydtOuLpC4iIH0NCiAgICByZXR1cm4NCiAgfQ0KICAkcmlkID0gJHIub2Jq
>> "%B64%" echo LnJlcXVlc3RfaWQNCiAgU2F5ICIgIOygkeyImOuQqCAo7J6R7JeF67KI7Zi4ICRyaWQpIC0g6riw
>> "%B64%" echo 64uk66as64qUIOykkSINCiAgJHQwID0gR2V0LURhdGUNCiAgd2hpbGUgKCgoR2V0LURhdGUpIC0g
>> "%B64%" echo JHQwKS5Ub3RhbFNlY29uZHMgLWx0IDkwMCkgew0KICAgIFN0YXJ0LVNsZWVwIC1TZWNvbmRzIDUN
>> "%B64%" echo CiAgICAkciA9IFdlYiAiJEFQSV9CQVNFL3ZpZGVvcy8kcmlkIiAkbnVsbCAkYXQgIkdFVCINCiAg
>> "%B64%" echo ICBpZiAoQCg0MDAsIDQwMSwgNDAzLCA0MDQpIC1jb250YWlucyAkci5jb2RlKSB7DQogICAgICBT
>> "%B64%" echo YXkgIiAgW1hdIOyhsO2ajCDsi6TtjKggSFRUUCAkKCRyLmNvZGUpIC0gJChDdXQgJHIudGV4dCAz
>> "%B64%" echo MDApIg0KICAgICAgcmV0dXJuDQogICAgfQ0KICAgIGlmICgtbm90ICRyLm9iaikgeyBjb250aW51
>> "%B64%" echo ZSB9DQogICAgJHN0ID0gJHIub2JqLnN0YXR1cw0KICAgIGlmICgkc3QgLWVxICJkb25lIikgew0K
>> "%B64%" echo ICAgICAgaWYgKCRyLm9iai52aWRlby5yZXNwZWN0X21vZGVyYXRpb24gLWVxICRmYWxzZSkgeyBT
>> "%B64%" echo YXkgIiAgW1hdIOqygOyXtOyXkCDqsbjroKQg7IKw7Lac7J20IOu5hOyXiOuLpC4iOyByZXR1cm4g
>> "%B64%" echo fQ0KICAgICAgJHUgPSAkci5vYmoudmlkZW8udXJsDQogICAgICBpZiAoLW5vdCAkdSkgeyB0cnkg
>> "%B64%" echo eyAkdSA9ICRyLm9iai52aWRlby5maWxlX291dHB1dC5wdWJsaWNfdXJsIH0gY2F0Y2gge30gfQ0K
>> "%B64%" echo ICAgICAgaWYgKC1ub3QgJHUpIHsgU2F5ICIgIFtYXSDsmYTro4zrnbzripTrjbAg7KO87IaM6rCA
>> "%B64%" echo IOyXhuuLpC4iOyByZXR1cm4gfQ0KICAgICAgdHJ5IHsNCiAgICAgICAgSW52b2tlLVdlYlJlcXVl
>> "%B64%" echo c3QgLVVyaSAkdSAtT3V0RmlsZSAkVmlkUGF0aCAtVGltZW91dFNlYyAzMDAgLVVzZUJhc2ljUGFy
>> "%B64%" echo c2luZw0KICAgICAgICAkc3ogPSBbTWF0aF06OlJvdW5kKChHZXQtSXRlbSAkVmlkUGF0aCkuTGVu
>> "%B64%" echo Z3RoIC8gMU1CLCAyKQ0KICAgICAgICBTYXkgIiAgW09LXSDsmIHsg4Eg64KY7JmU64ukIC0+ICRW
>> "%B64%" echo aWRQYXRoICAgKCRzeiBNQiDCtyDssq3qtawgJChDb3N0ICRyLm9iaikg64us65+sKSINCiAgICAg
>> "%B64%" echo ICAgU2F5ICIgICAgICAg7Je07Ja07IScIOyGjOumrOq5jOyngCDrk6TslrTrs7TrqbQg7ZmU7KeI
>> "%B64%" echo IO2MkOuLqOydtCDrgZ3rgpzri6QuIg0KICAgICAgfSBjYXRjaCB7IFNheSAiICBbIV0g7JiB7IOB
>> "%B64%" echo IOyjvOyGjOuKlCDrsJvslZjripTrjbAg64K066Ck67Cb6riwIOyLpO2MqCA6ICRfIiB9DQogICAg
>> "%B64%" echo ICByZXR1cm4NCiAgICB9DQogICAgaWYgKCRzdCAtZXEgImZhaWxlZCIpIHsNCiAgICAgIFNheSAi
>> "%B64%" echo ICBbWF0g7KCc7J6RIOyLpO2MqCAtICQoJHIub2JqLmVycm9yLmNvZGUpIDogJCgkci5vYmouZXJy
>> "%B64%" echo b3IubWVzc2FnZSkiDQogICAgICByZXR1cm4NCiAgICB9DQogICAgJGVsID0gW2ludF0oKEdldC1E
>> "%B64%" echo YXRlKSAtICR0MCkuVG90YWxTZWNvbmRzDQogICAgaWYgKCRlbCAlIDMwIC1sdCA1KSB7IFNheSAi
>> "%B64%" echo ICAgIC4uLiDrp4zrk5zripQg7KSRICgkZWwg7LSIKSIgfQ0KICB9DQogIFNheSAiICBbWF0gMTXr
>> "%B64%" echo toQg7JWI7JeQIOyViCDrgZ3rgqzri6QuIg0KfQ0KDQoNClNheSAiIg0KU2F5ICIrLS0tLS0tLS0t
>> "%B64%" echo LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSsiDQpTYXkg
>> "%B64%" echo Inwg6re466GdIOyekOqyqSDtjJDsoJXquLAgLSDroZzqt7jsnbggKyDqt7jrprwgMeyepSArIOyY
>> "%B64%" echo geyDgSAx7Y64IOyLpOusvCAgICAgIHwiDQpTYXkgIistLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
>> "%B64%" echo LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tKyINClNheSAiIg0KDQojICgxKSDsl5Tr
>> "%B64%" echo k5ztj6zsnbjtirjripQg7ZWY65Oc7L2U65SpIOuMgOyLoCB4QUkg6rCAIOyVjOugpOyjvOuKlCDq
>> "%B64%" echo sJLsnYQg7JO064ukKOyjvOyGjOqwgCDrsJTrgIzslrTrj4Qg65Sw65286rCE64ukKQ0KJHIgPSBX
>> "%B64%" echo ZWIgJERJU0NPVkVSWSAkbnVsbCAkbnVsbCAiR0VUIg0KaWYgKCRyLmNvZGUgLW5lIDIwMCAtb3Ig
>> "%B64%" echo LW5vdCAkci5vYmopIHsNCiAgU3RvcC1CYWQgIuyduOymnSDshJzrsoQg7KCV67O066W8IOuquyDr
>> "%B64%" echo sJvslZjri6QiICJIVFRQICQoJHIuY29kZSlgcmBuJCgkci50ZXh0KSIgIuyduO2EsOuEt+ydtOuC
>> "%B64%" echo mCDtmozsgqwg67Cp7ZmU67K9IOusuOygnOydvCDsiJgg7J6I64ukLiDruIzrnbzsmrDsoIDroZwg
>> "%B64%" echo JERJU0NPVkVSWSDqsIAg7Je066as64qU7KeAIO2ZleyduO2VtOu0kOudvC4iDQp9DQokZGV2VXJs
>> "%B64%" echo ID0gJHIub2JqLmRldmljZV9hdXRob3JpemF0aW9uX2VuZHBvaW50DQokdG9rVXJsID0gJHIub2Jq
>> "%B64%" echo LnRva2VuX2VuZHBvaW50DQokd2hvVXJsID0gJHIub2JqLnVzZXJpbmZvX2VuZHBvaW50DQppZiAo
>> "%B64%" echo LW5vdCAkZGV2VXJsIC1vciAtbm90ICR0b2tVcmwpIHsgU3RvcC1CYWQgIuydtCDshJzrsoTripQg
>> "%B64%" echo 7L2U65OcIOyKueyduCDrsKnsi53snYQg7JWIIOuwm+uKlOuLpCIgJHIudGV4dCAiIiB9DQpTYXkg
>> "%B64%" echo IiAg7J247KadIOyEnOuyhCDtmZXsnbgg7JmE66OMIg0KDQojICgyKSDsoIDsnqXrkJwg7Je07Ieg
>> "%B64%" echo IOuovOyggCDihpIg7JeG6rGw64KYIOyjveyXiOydhCDrlYzrp4wg66Gc6re47J24DQokYXQgPSBU
>> "%B64%" echo cnlTdG9yZWQgJHRva1VybA0KaWYgKCRhdCkgew0KICBTYXkgIiINCiAgU2F5ICgiLSIgKiA1OCkN
>> "%B64%" echo CiAgU2F5ICLqt7jrprzqs7wg7JiB7IOB7J20IOydtCDsnpDqsqnsl5Ag7Je066CkIOyeiOuKlOyn
>> "%B64%" echo gCDrs7jri6QiDQogIFNheSAoIi0iICogNTgpDQogIE1lZGlhICRhdA0KICBTYXkgIiINCiAgU2F5
>> "%B64%" echo ICIgIC0+IOq4sOuhnSDtjIzsnbzsnYQg7YG066Gc65OcIOyEuOyFmOyXkCDso7zrqbQg6re464yA
>> "%B64%" echo 66GcIOuwsOyEoO2VnOuLpC4iDQogIFNheSAiICDquLDroZ0gOiAkTG9nUGF0aCINCiAgU2F2ZUxv
>> "%B64%" echo Zw0KICBXcml0ZS1Ib3N0ICIiDQogIFJlYWQtSG9zdCAi7JeU7YSw66W8IOuIhOultOuptCDssL3s
>> "%B64%" echo nbQg64ur7Z6M64ukIg0KICBleGl0IDANCn0NCg0KIyAoMykg7L2U65OcIOuwnOq4iSjsoIDsnqXr
>> "%B64%" echo kJwg7Je07Ieg6rCAIOyXhuydhCDrlYzrp4wpDQokciA9IFdlYiAkZGV2VXJsIEB7IGNsaWVudF9p
>> "%B64%" echo ZCA9ICRDTElFTlRfSUQ7IHNjb3BlID0gJFNDT1BFIH0gJG51bGwgIlBPU1QiDQppZiAoJHIuY29k
>> "%B64%" echo ZSAtbmUgMjAwIC1vciAtbm90ICRyLm9iai51c2VyX2NvZGUpIHsNCiAgU3RvcC1CYWQgIuuhnOq3
>> "%B64%" echo uOyduCDsvZTrk5wg67Cc6riJ7J20IOqxsOygiOuQkOuLpCIgIkhUVFAgJCgkci5jb2RlKWByYG4k
>> "%B64%" echo KCRyLnRleHQpIiAi7J6g7IucIOuSpCDri6Tsi5wg7Iuk7ZaJ7ZW067SQ6528LiINCn0NCiRkZXYg
>> "%B64%" echo ICAgICA9ICRyLm9iag0KJHZlcmlmeSAgID0gaWYgKCRkZXYudmVyaWZpY2F0aW9uX3VyaV9jb21w
>> "%B64%" echo bGV0ZSkgeyAkZGV2LnZlcmlmaWNhdGlvbl91cmlfY29tcGxldGUgfSBlbHNlIHsgJGRldi52ZXJp
>> "%B64%" echo ZmljYXRpb25fdXJpIH0NCiRpbnRlcnZhbCA9IGlmICgkZGV2LmludGVydmFsKSB7IFtpbnRdJGRl
>> "%B64%" echo di5pbnRlcnZhbCB9IGVsc2UgeyA1IH0NCiRleHBpcmVzICA9IGlmICgkZGV2LmV4cGlyZXNfaW4p
>> "%B64%" echo IHsgW2ludF0kZGV2LmV4cGlyZXNfaW4gfSBlbHNlIHsgOTAwIH0NCg0KU2F5ICIiDQpTYXkgIiAg
>> "%B64%" echo Ky0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSsi
>> "%B64%" echo DQpTYXkgIiAgfCDruIzrnbzsmrDsoIDqsIAg7Je066aw64ukLiDroZzqt7jsnbjtlZjqs6AgW+yK
>> "%B64%" echo ueyduF0g64iE66W066m0IOuBneydtOuLpC4gICB8Ig0KU2F5ICIgICstLS0tLS0tLS0tLS0tLS0t
>> "%B64%" echo LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0rIg0KU2F5ICIiDQpTYXkgIiAg
>> "%B64%" echo ICDso7zshowgOiAkdmVyaWZ5Ig0KU2F5ICIgICAg7L2U65OcIDogJCgkZGV2LnVzZXJfY29kZSki
>> "%B64%" echo DQpTYXkgIiINClNheSAiICAo7KCc7ZWcIOyLnOqwhCAkKFtpbnRdKCRleHBpcmVzLzYwKSnrtoQg
>> "%B64%" echo wrcg7Iq57J247ZWY66m0IOyXrOq4sOyEnCDsnpDrj5nsnLzroZwg64SY7Ja06rCE64ukKSINClNh
>> "%B64%" echo eSAiIg0KdHJ5IHsgU3RhcnQtUHJvY2VzcyAkdmVyaWZ5IH0gY2F0Y2ggeyBTYXkgIiAgKOu4jOud
>> "%B64%" echo vOyasOyggCDsnpDrj5kg7Je06riwIOyLpO2MqCAtIOychCDso7zshozrpbwg7KeB7KCRIOyXtOyW
>> "%B64%" echo tOudvCkiIH0NCg0KIyAoMykg7Iq57J24IOuMgOq4sA0KJGRlYWRsaW5lID0gKEdldC1EYXRlKS5B
>> "%B64%" echo ZGRTZWNvbmRzKCRleHBpcmVzKQ0KJHRva2VucyA9ICRudWxsDQokd2FpdGVkID0gMA0Kd2hpbGUg
>> "%B64%" echo KChHZXQtRGF0ZSkgLWx0ICRkZWFkbGluZSkgew0KICBTdGFydC1TbGVlcCAtU2Vjb25kcyAkaW50
>> "%B64%" echo ZXJ2YWwNCiAgJHdhaXRlZCArPSAkaW50ZXJ2YWwNCiAgJHIgPSBXZWIgJHRva1VybCBAeyBjbGll
>> "%B64%" echo bnRfaWQgPSAkQ0xJRU5UX0lEOyBkZXZpY2VfY29kZSA9ICRkZXYuZGV2aWNlX2NvZGU7IGdyYW50
>> "%B64%" echo X3R5cGUgPSAidXJuOmlldGY6cGFyYW1zOm9hdXRoOmdyYW50LXR5cGU6ZGV2aWNlX2NvZGUiIH0g
>> "%B64%" echo JG51bGwgIlBPU1QiDQogIGlmICgkci5jb2RlIC1lcSAyMDAgLWFuZCAkci5vYmouYWNjZXNzX3Rv
>> "%B64%" echo a2VuKSB7ICR0b2tlbnMgPSAkci5vYmo7IGJyZWFrIH0NCiAgJGVyciA9ICRudWxsOyB0cnkgeyAk
>> "%B64%" echo ZXJyID0gJHIub2JqLmVycm9yIH0gY2F0Y2gge30NCiAgaWYgKCRlcnIgLWVxICJhdXRob3JpemF0
>> "%B64%" echo aW9uX3BlbmRpbmciKSB7IGlmICgkd2FpdGVkICUgMzAgLWx0ICRpbnRlcnZhbCkgeyBTYXkgIiAg
>> "%B64%" echo Li4uIOyKueyduCDquLDri6TrpqzripQg7KSRICgkd2FpdGVkIOy0iCkiIH07IGNvbnRpbnVlIH0N
>> "%B64%" echo CiAgaWYgKCRlcnIgLWVxICJzbG93X2Rvd24iKSB7ICRpbnRlcnZhbCArPSA1OyBjb250aW51ZSB9
>> "%B64%" echo DQogIGlmICgkZXJyIC1lcSAiZXhwaXJlZF90b2tlbiIgLW9yICRlcnIgLWVxICJhY2Nlc3NfZGVu
>> "%B64%" echo aWVkIikgew0KICAgIFN0b3AtQmFkICLroZzqt7jsnbjsnbQg64Gd64KY6riwIOyghOyXkCDrgYrq
>> "%B64%" echo srzri6QiICLsgqzsnKA6ICRlcnJgcmBuJCgkci50ZXh0KSIgIuydtCDtjIzsnbzsnYQg64uk7Iuc
>> "%B64%" echo IOyLpO2Wie2VtOyEnCDsirnsnbjtlbTrnbwuIg0KICB9DQp9DQppZiAoLW5vdCAkdG9rZW5zKSB7
>> "%B64%" echo IFN0b3AtQmFkICLsoJztlZwg7Iuc6rCEIOyViOyXkCDsirnsnbjsnbQg7JWIIOuQkOuLpCIgIuuL
>> "%B64%" echo pOyLnCDsi6TtlontlbTrnbwuIiAiIiB9DQoNCiRhdCA9ICR0b2tlbnMuYWNjZXNzX3Rva2VuDQpT
>> "%B64%" echo YXkgIiINClNheSAiICBbT0tdIDHri6jqs4Qg7Ya16rO8IC0g66Gc6re47J24IOyEseqztSjrgrQg
>> "%B64%" echo 6rOE7KCV7J20IOyduOymneuQkOuLpCkiDQpbdm9pZF0kc2NyaXB0OkxvZy5BZGQoIiAgICAgIO2G
>> "%B64%" echo oO2BsCjqsIDrprwpOiAiICsgKE1hc2sgJGF0KSkNCg0KIyAoNCkg7Iug7JuQKOyLpO2MqO2VtOuP
>> "%B64%" echo hCDsp4TtlokpDQppZiAoJHdob1VybCkgew0KICAkciA9IFdlYiAkd2hvVXJsICRudWxsICRhdCAi
>> "%B64%" echo R0VUIg0KICBpZiAoJHIuY29kZSAtZXEgMjAwIC1hbmQgJHIub2JqKSB7DQogICAgJG5tID0gJHIu
>> "%B64%" echo b2JqLmVtYWlsOyBpZiAoLW5vdCAkbm0pIHsgJG5tID0gJHIub2JqLm5hbWUgfTsgaWYgKC1ub3Qg
>> "%B64%" echo JG5tKSB7ICRubSA9ICRyLm9iai5zdWIgfQ0KICAgIFNheSAiICAgICAgIOqzhOyglTogJG5tIg0K
>> "%B64%" echo ICB9DQp9DQoNCiMgKDUpIOyTuCDsiJgg7J6I64qUIOuqqOuNuCDrqqnroZ0gLSDsnpDqsqkg6rGw
>> "%B64%" echo 7KCI7J2066m0IOyXrOq4sOyEnCDsnbTrr7gg6rCI66aw64ukDQokYXZhaWwgPSBAKCkNCiRyID0g
>> "%B64%" echo V2ViICIkQVBJX0JBU0UvbW9kZWxzIiAkbnVsbCAkYXQgIkdFVCINCmlmICgkci5jb2RlIC1lcSAy
>> "%B64%" echo MDAgLWFuZCAkci5vYmouZGF0YSkgew0KICAkYXZhaWwgPSBAKCRyLm9iai5kYXRhIHwgRm9yRWFj
>> "%B64%" echo aC1PYmplY3QgeyAkXy5pZCB9IHwgV2hlcmUtT2JqZWN0IHsgJF8gfSkNCiAgU2F5ICIgICAgICAg
>> "%B64%" echo 7JO4IOyImCDsnojripQg66qo6424ICQoJGF2YWlsLkNvdW50KeqwnDogJCgoJGF2YWlsIHwgU2Vs
>> "%B64%" echo ZWN0LU9iamVjdCAtRmlyc3QgOCkgLWpvaW4gJywgJykiDQp9IGVsc2Ugew0KICBTYXkgIiAgICAg
>> "%B64%" echo ICDrqqjrjbgg66qp66Gd7J2AIOuquyDrsJvslZjri6QoSFRUUCAkKCRyLmNvZGUpKSAtIOq3uOue
>> "%B64%" echo mOuPhCDtmLjstpzsnYAg7Iuc64+E7ZWc64ukIg0KICBbdm9pZF0kc2NyaXB0OkxvZy5BZGQoIiAg
>> "%B64%" echo ICAgICAo66qp66GdIOydkeuLtSkgIiArICRyLnRleHQpDQp9DQoNCiMgKDYpIOyLpOygnCAx7L2c
>> "%B64%" echo IC0g7J206rKMIO2MkOygleydmCDsoITrtoDri6QNCiRvcmRlciA9IEAoKQ0KZm9yZWFjaCAoJG0g
>> "%B64%" echo aW4gJGF2YWlsKSB7IGlmICgkTU9ERUxTIC1jb250YWlucyAkbSkgeyAkb3JkZXIgKz0gJG0gfSB9
>> "%B64%" echo DQpmb3JlYWNoICgkbSBpbiAkTU9ERUxTKSB7IGlmICgkb3JkZXIgLW5vdGNvbnRhaW5zICRtKSB7
>> "%B64%" echo ICRvcmRlciArPSAkbSB9IH0NCmZvcmVhY2ggKCRtIGluICRhdmFpbCkgIHsgaWYgKCRvcmRlciAt
>> "%B64%" echo bm90Y29udGFpbnMgJG0pIHsgJG9yZGVyICs9ICRtIH0gfQ0KJG9yZGVyID0gJG9yZGVyIHwgU2Vs
>> "%B64%" echo ZWN0LU9iamVjdCAtRmlyc3QgNg0KDQokbGFzdCA9ICRudWxsDQpmb3JlYWNoICgkbSBpbiAkb3Jk
>> "%B64%" echo ZXIpIHsNCiAgJHBheWxvYWQgPSBAeyBtb2RlbCA9ICRtOyBtZXNzYWdlcyA9IEAoQHsgcm9sZSA9
>> "%B64%" echo ICJ1c2VyIjsgY29udGVudCA9ICLtlZzqta3slrTroZwgJ+2GteqzvCfrnbzqs6Drp4wg64u17ZW0
>> "%B64%" echo LiIgfSk7IG1heF90b2tlbnMgPSAxNiB9IHwgQ29udmVydFRvLUpzb24gLURlcHRoIDUgLUNvbXBy
>> "%B64%" echo ZXNzDQogICRyID0gV2ViICIkQVBJX0JBU0UvY2hhdC9jb21wbGV0aW9ucyIgJHBheWxvYWQgJGF0
>> "%B64%" echo ICJQT1NUIg0KICBTYXkgIiAgICAgICDtmLjstpwg7Iuc64+EIFskbV0gLT4gSFRUUCAkKCRyLmNv
>> "%B64%" echo ZGUpIg0KICAkbGFzdCA9IEB7IG0gPSAkbTsgciA9ICRyIH0NCiAgaWYgKCRyLmNvZGUgLWVxIDIw
>> "%B64%" echo MCAtYW5kICRyLm9iaikgew0KICAgICRzYXkgPSAiIg0KICAgIHRyeSB7ICRzYXkgPSAkci5vYmou
>> "%B64%" echo Y2hvaWNlc1swXS5tZXNzYWdlLmNvbnRlbnQgfSBjYXRjaCB7ICRzYXkgPSAkci50ZXh0IH0NCiAg
>> "%B64%" echo ICAka2VlcCA9IEB7DQogICAgICBhY2Nlc3NfdG9rZW4gPSAkYXQ7IHJlZnJlc2hfdG9rZW4gPSAk
>> "%B64%" echo dG9rZW5zLnJlZnJlc2hfdG9rZW47IGV4cGlyZXNfaW4gPSAkdG9rZW5zLmV4cGlyZXNfaW4NCiAg
>> "%B64%" echo ICAgIGNsaWVudF9pZCA9ICRDTElFTlRfSUQ7IHNjb3BlID0gJFNDT1BFOyB0b2tlbl9lbmRwb2lu
>> "%B64%" echo dCA9ICR0b2tVcmw7IGFwaV9iYXNlID0gJEFQSV9CQVNFDQogICAgICBtb2RlbF9vayA9ICRtOyBz
>> "%B64%" echo YXZlZF9hdCA9IChHZXQtRGF0ZSkuVG9TdHJpbmcoInl5eXktTU0tZGQgSEg6bW06c3MiKQ0KICAg
>> "%B64%" echo IH0NCiAgICB0cnkgeyAka2VlcCB8IENvbnZlcnRUby1Kc29uIC1EZXB0aCA1IHwgT3V0LUZpbGUg
>> "%B64%" echo LUZpbGVQYXRoICRUb2tlblBhdGggLUVuY29kaW5nIFVURjggfSBjYXRjaCB7fQ0KICAgIFNheSAi
>> "%B64%" echo Ig0KICAgIFNheSAoIj0iICogNTgpDQogICAgU2F5ICJb7Ya16rO8XSDrhKQg6rWs64+FIOyekOqy
>> "%B64%" echo qeycvOuhnCDqt7jroZ3snbQg7Iuk7KCc66GcIOuMgOuLte2WiOuLpCINCiAgICBTYXkgKCI9IiAq
>> "%B64%" echo IDU4KQ0KICAgIFNheSAiICDrqqjrjbggOiAkbSINCiAgICBTYXkgIiAg64yA64u1IDogJCgkc2F5
>> "%B64%" echo IC1yZXBsYWNlICdccysnLCcgJykiDQogICAgU2F5ICIgIO2GoO2BsCA6ICRUb2tlblBhdGggICjq
>> "%B64%" echo sLHsi6Ag7Je07IegIO2PrO2VqCAtIOuCqOyXkOqyjCDso7zsp4Ag66eI6528KSINCiAgICBTYXkg
>> "%B64%" echo IiAg6riw66GdIDogJExvZ1BhdGgiDQogICAgU2F5ICIiDQogICAgU2F5ICgiLSIgKiA1OCkNCiAg
>> "%B64%" echo ICBTYXkgIjLri6jqs4QgLSDqt7jrprzqs7wg7JiB7IOB7J20IOydtCDsnpDqsqnsl5Ag7Je066Ck
>> "%B64%" echo IOyeiOuKlOyngCDrs7jri6QiDQogICAgU2F5ICgiLSIgKiA1OCkNCiAgICBNZWRpYSAkYXQNCiAg
>> "%B64%" echo ICBTYXkgIiINCiAgICBTYXkgIiAgLT4g6riw66GdIO2MjOydvOydhCDtgbTroZzrk5wg7IS47IWY
>> "%B64%" echo 7JeQIOyjvOuptCDqt7jrjIDroZwg67Cw7ISg7ZWc64ukLiINCiAgICBTYXZlTG9nDQogICAgV3Jp
>> "%B64%" echo dGUtSG9zdCAiIg0KICAgIFJlYWQtSG9zdCAi7JeU7YSw66W8IOuIhOultOuptCDssL3snbQg64ur
>> "%B64%" echo 7Z6M64ukIg0KICAgIGV4aXQgMA0KICB9DQogIGlmICgkci5jb2RlIC1lcSA0MDQpIHsgY29udGlu
>> "%B64%" echo dWUgfSAgICMg66qo6424IOydtOumhCDrrLjsoJwgPSDri6TsnYwg7ZuE67O066GcDQp9DQoNCiRt
>> "%B64%" echo ID0gJGxhc3QubTsgJHIgPSAkbGFzdC5yDQokcmVhc29uID0gJHIudGV4dA0KdHJ5IHsgaWYgKCRy
>> "%B64%" echo Lm9iai5lcnJvcikgeyAkcmVhc29uID0gKCRyLm9iai5lcnJvciB8IE91dC1TdHJpbmcpIH0gfSBj
>> "%B64%" echo YXRjaCB7fQ0KU2F5ICIiDQpTYXkgKCI9IiAqIDU4KQ0KU2F5ICJb6rGw7KCIXSDroZzqt7jsnbjs
>> "%B64%" echo nYAg65CQ64qU642wIO2YuOy2nOydhCDrp4nslZjri6QiDQpTYXkgKCI9IiAqIDU4KQ0KU2F5ICIg
>> "%B64%" echo IOuniOyngOuniSDsi5zrj4QgIDogJG0gLT4gSFRUUCAkKCRyLmNvZGUpIg0KU2F5ICIgIOyEnOuy
>> "%B64%" echo hOqwgCDtlZwg66eQIDogJCgkcmVhc29uIC1yZXBsYWNlICdccysnLCcgJykiDQpTYXkgIiINCmlm
>> "%B64%" echo ICgkci5jb2RlIC1lcSA0MDMpIHsgU2F5ICIgIDQwMyA9IOyekOqyqSDqsbDsoIjsnbTri6QuIOq1
>> "%B64%" echo rOuPheydgCDsgrTslYQg7J6I64qU642wIHhBSSDqsIAg7J20IO2GteuhnOulvCDslYgg7Je07Ja0
>> "%B64%" echo 7KSAIOqygy4iIH0NCmVsc2VpZiAoJHIuY29kZSAtZXEgNDAxKSB7IFNheSAiICA0MDEgPSDthqDt
>> "%B64%" echo gbAg66y47KCc64ukLiDri6Tsi5wg7Iuk7ZaJ7ZW07IScIOuhnOq3uOyduOu2gO2EsCDtlbTrtJDr
>> "%B64%" echo nbwuIiB9DQplbHNlaWYgKCRyLmNvZGUgLWVxIDQyOSkgeyBTYXkgIiAgNDI5ID0g7ZWc64+E64uk
>> "%B64%" echo LiDsnpDqsqnsnYAg7J6I64uk64qUIOucu+ydtOuLiCDsnqDsi5wg65KkIOuLpOyLnCDrj4zroKTr
>> "%B64%" echo nbwuIiB9DQpTYXkgIiINClNheSAiICDquLDroZ0gOiAkTG9nUGF0aCAgICjsnbQg7YyM7J287J2E
>> "%B64%" echo IO2BtOuhnOuTnCDshLjshZjsl5Ag7KO866m0IOybkOyduCDtjJDsoJXtlZzri6QpIg0KU2F2ZUxv
>> "%B64%" echo Zw0KV3JpdGUtSG9zdCAiIg0KUmVhZC1Ib3N0ICLsl5TthLDrpbwg64iE66W066m0IOywveydtCDr
>> "%B64%" echo i6vtnozri6QiDQpleGl0IDINCg==
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$t=[IO.File]::ReadAllText($env:B64); [IO.File]::WriteAllBytes((Join-Path $env:NM 'grok_probe.ps1'), [Convert]::FromBase64String(($t -replace '\s','')))"
if errorlevel 1 goto :fail
del "%B64%" >nul 2>&1

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%NM%\grok_probe.ps1"
set "RC=%ERRORLEVEL%"

del "%NM%\grok_probe.ps1" >nul 2>&1
rmdir "%NM%" >nul 2>&1
exit /b %RC%

:fail
echo.
echo   UNPACK FAILED - please send the lines above.
echo.
pause
exit /b 1
