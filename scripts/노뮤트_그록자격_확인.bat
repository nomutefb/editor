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
>> "%B64%" echo PSAxMOy0iCA3MjBwIMK3IOyGjOumrCDtj6ztlagpDQojICAgICAgICDrsJTtg5XtmZTrqbRc6re4
>> "%B64%" echo 66GdX+q3uOumvC5qcGcgICAgICAo6re466a87J20IOyXtOugpCDsnojsnLzrqbQg7Iuk66y8IDHs
>> "%B64%" echo nqUpDQojICAgICAgICDrsJTtg5XtmZTrqbRc6re466GdX+yYgeyDgS5tcDQgICAgICAo7JiB7IOB
>> "%B64%" echo 7J20IOyXtOugpCDsnojsnLzrqbQg7Iuk66y8IDHtjrggPSAxMOy0iCA3MjBwIMK3IOyGjOumrCDt
>> "%B64%" echo j6ztlagpDQojIOuBhOuKlCDrspU6IOyViCDrj4zrpqzrqbQg64GdLiDshKTsuZjrkJjripQg6rKD
>> "%B64%" echo 64+ELCDsnpDrj5kg7Iuk7ZaJ65CY64qUIOqyg+uPhCDsl4bri6QuDQoNCiRFcnJvckFjdGlvblBy
>> "%B64%" echo ZWZlcmVuY2UgPSAiU3RvcCINCnRyeSB7IFtOZXQuU2VydmljZVBvaW50TWFuYWdlcl06OlNlY3Vy
>> "%B64%" echo aXR5UHJvdG9jb2wgPSBbTmV0LlNlY3VyaXR5UHJvdG9jb2xUeXBlXTo6VGxzMTIgfSBjYXRjaCB7
>> "%B64%" echo fQ0KdHJ5IHsgJE91dHB1dEVuY29kaW5nID0gW0NvbnNvbGVdOjpPdXRwdXRFbmNvZGluZyA9IFtU
>> "%B64%" echo ZXh0LkVuY29kaW5nXTo6VVRGOCB9IGNhdGNoIHt9DQoNCiRDTElFTlRfSUQgPSAiYjFhMDA0OTIt
>> "%B64%" echo MDczYS00N2VhLTgxNmYtNGMzMjkyNjRhODI4IiAgICMgeEFJIOqzteqwnCDrjbDsiqTtgazthrEg
>> "%B64%" echo 7YG065287J207Ja47Yq4KOu5hOuwgO2CpCDsl4bsnYwpDQokU0NPUEUgICAgID0gIm9wZW5pZCBw
>> "%B64%" echo cm9maWxlIGVtYWlsIG9mZmxpbmVfYWNjZXNzIGdyb2stY2xpOmFjY2VzcyBhcGk6YWNjZXNzIg0K
>> "%B64%" echo JERJU0NPVkVSWSA9ICJodHRwczovL2F1dGgueC5haS8ud2VsbC1rbm93bi9vcGVuaWQtY29uZmln
>> "%B64%" echo dXJhdGlvbiINCiRBUElfQkFTRSAgPSAiaHR0cHM6Ly9hcGkueC5haS92MSINCiRNT0RFTFMgICAg
>> "%B64%" echo PSBAKCJncm9rLTQuNSIsImdyb2stNC4zIiwiZ3Jvay0zIiwiZ3Jvay1iZXRhIikNCg0KIyDimqAg
>> "%B64%" echo 67CU7YOV7ZmU66m0IOqyveuhnOuKlCDruYgg66y47J6Q7Je066GcIOyYrCDsiJgg7J6I64ukKOyb
>> "%B64%" echo kOuTnOudvOydtOu4jCDrsLHsl4XCt+u5hOyciOuPhOyasCDtmZjqsr0g7Iuk7LihKSDihpIg7Y+0
>> "%B64%" echo 67CxIOyCrOyKrC4NCiMgICDtlZwg7Lm47J20652864+EIOu5hOuptCBKb2luLVBhdGgg6rCAIOq3
>> "%B64%" echo uCDsnpDrpqzsl5DshJwg7KO97Ja0IO2MkOyglSDsnpDssrTrpbwg66q7IO2VnOuLpCjssqsg7Iuk
>> "%B64%" echo 7ZaJIOyLpOy4oSDrtIntlakpLg0KJERlc2sgPSAiIg0KIyAo4pqgIEpvaW4tUGF0aCDripQg67mI
>> "%B64%" echo IOqwkuydhCDrsJvsnLzrqbQg6re4IOyekOumrOyXkOyEnCDso73ripTri6QgPSDtj7TrsLHsnbQg
>> "%B64%" echo 7Y+067CxIOyghOyXkCDthLDsp4Tri6Qg4oaSIOusuOyekOyXtOuhnOunjCDsnofripTri6QpDQpm
>> "%B64%" echo b3JlYWNoICgkYyBpbiBAKFtFbnZpcm9ubWVudF06OkdldEZvbGRlclBhdGgoIkRlc2t0b3AiKSwN
>> "%B64%" echo CiAgICAgICAgICAgICAgICAgIiRlbnY6VVNFUlBST0ZJTEVcRGVza3RvcCIsICIkZW52OlVTRVJQ
>> "%B64%" echo Uk9GSUxFIiwgIiRlbnY6VEVNUCIsIChHZXQtTG9jYXRpb24pLlBhdGgpKSB7DQogIGlmICgkYyAt
>> "%B64%" echo YW5kICRjLlRyaW0oKSAtYW5kIChUZXN0LVBhdGggLUxpdGVyYWxQYXRoICRjKSkgeyAkRGVzayA9
>> "%B64%" echo ICRjOyBicmVhayB9DQp9DQppZiAoLW5vdCAkRGVzaykgeyAkRGVzayA9ICIuIiB9DQokTG9nUGF0
>> "%B64%" echo aCAgID0gSm9pbi1QYXRoICREZXNrICLqt7jroZ3tmZXsnbhf6rKw6rO8LnR4dCINCiRUb2tlblBh
>> "%B64%" echo dGggPSBKb2luLVBhdGggJERlc2sgIuq3uOuhne2GoO2BsC5qc29uIg0KJEltZ1BhdGggICA9IEpv
>> "%B64%" echo aW4tUGF0aCAkRGVzayAi6re466GdX+q3uOumvC5qcGciDQokVmlkUGF0aCAgID0gSm9pbi1QYXRo
>> "%B64%" echo ICREZXNrICLqt7jroZ1f7JiB7IOBLm1wNCINCiRzY3JpcHQ6TG9nID0gTmV3LU9iamVjdCBTeXN0
>> "%B64%" echo ZW0uQ29sbGVjdGlvbnMuQXJyYXlMaXN0DQoNCmZ1bmN0aW9uIFNheSgkdCkgeyBXcml0ZS1Ib3N0
>> "%B64%" echo ICR0OyBbdm9pZF0kc2NyaXB0OkxvZy5BZGQoJHQpIH0NCmZ1bmN0aW9uIE1hc2soJHMpIHsgaWYg
>> "%B64%" echo KCRzIC1hbmQgJHMuTGVuZ3RoIC1ndCAxMikgeyAkcy5TdWJzdHJpbmcoMCwxMikgKyAi4oCmPCIg
>> "%B64%" echo KyAkcy5MZW5ndGggKyAi7J6QIOqwgOumvD4iIH0gZWxzZSB7ICRzIH0gfQ0KZnVuY3Rpb24gQ3V0
>> "%B64%" echo KCR0LCAkbikgeyAkdCA9ICIkdCIgLXJlcGxhY2UgIlxzKyIsICIgIjsgaWYgKCR0Lkxlbmd0aCAt
>> "%B64%" echo Z3QgJG4pIHsgJHQuU3Vic3RyaW5nKDAsICRuKSB9IGVsc2UgeyAkdCB9IH0NCmZ1bmN0aW9uIENv
>> "%B64%" echo c3QoJG8pIHsgdHJ5IHsgcmV0dXJuIFtNYXRoXTo6Um91bmQoW2RvdWJsZV0kby51c2FnZS5jb3N0
>> "%B64%" echo X2luX3VzZF90aWNrcyAvIDFlMTAsIDQpIH0gY2F0Y2ggeyByZXR1cm4gMCB9IH0NCmZ1bmN0aW9u
>> "%B64%" echo IFNhdmVMb2cgeyB0cnkgeyAkc2NyaXB0OkxvZyAtam9pbiAiYHJgbiIgfCBPdXQtRmlsZSAtRmls
>> "%B64%" echo ZVBhdGggJExvZ1BhdGggLUVuY29kaW5nIFVURjggfSBjYXRjaCB7fSB9DQoNCiMg7IOB7YOc7L2U
>> "%B64%" echo 65Oc6rmM7KeAIOuwm+yVhOyYpOuKlCDsmpTssq3quLAo7YyM7JuM7IW4IDUuMSDsl5DshKAg7Iuk
>> "%B64%" echo 7YyoIOydkeuLtSDrs7jrrLjsnYQg7KeB7KCRIOydveyWtOyVvCDtlZzri6QpDQpmdW5jdGlvbiBX
>> "%B64%" echo ZWIoJHVybCwgJGJvZHksICR0b2tlbiwgJG1ldGhvZCkgew0KICAkaCA9IEB7fQ0KICBpZiAoJHRv
>> "%B64%" echo a2VuKSB7ICRoWyJBdXRob3JpemF0aW9uIl0gPSAiQmVhcmVyICR0b2tlbiIgfQ0KICAkcCA9IEB7
>> "%B64%" echo IFVyaSA9ICR1cmw7IEhlYWRlcnMgPSAkaDsgVGltZW91dFNlYyA9IDkwOyBVc2VCYXNpY1BhcnNp
>> "%B64%" echo bmcgPSAkdHJ1ZSB9DQogIGlmICgkbWV0aG9kKSB7ICRwWyJNZXRob2QiXSA9ICRtZXRob2QgfSBl
>> "%B64%" echo bHNlaWYgKCRib2R5KSB7ICRwWyJNZXRob2QiXSA9ICJQT1NUIiB9IGVsc2UgeyAkcFsiTWV0aG9k
>> "%B64%" echo Il0gPSAiR0VUIiB9DQogIGlmICgkYm9keSAtaXMgW2hhc2h0YWJsZV0pIHsgJHBbIkJvZHkiXSA9
>> "%B64%" echo ICRib2R5OyAkcFsiQ29udGVudFR5cGUiXSA9ICJhcHBsaWNhdGlvbi94LXd3dy1mb3JtLXVybGVu
>> "%B64%" echo Y29kZWQiIH0NCiAgZWxzZWlmICgkYm9keSkgeyAkcFsiQm9keSJdID0gW1RleHQuRW5jb2Rpbmdd
>> "%B64%" echo OjpVVEY4LkdldEJ5dGVzKCRib2R5KTsgJHBbIkNvbnRlbnRUeXBlIl0gPSAiYXBwbGljYXRpb24v
>> "%B64%" echo anNvbiIgfQ0KICB0cnkgew0KICAgICRyID0gSW52b2tlLVdlYlJlcXVlc3QgQHANCiAgICAkdHh0
>> "%B64%" echo ID0gJHIuQ29udGVudA0KICAgICRvYmogPSAkbnVsbDsgdHJ5IHsgJG9iaiA9ICR0eHQgfCBDb252
>> "%B64%" echo ZXJ0RnJvbS1Kc29uIH0gY2F0Y2gge30NCiAgICByZXR1cm4gQHsgY29kZSA9IFtpbnRdJHIuU3Rh
>> "%B64%" echo dHVzQ29kZTsgdGV4dCA9ICR0eHQ7IG9iaiA9ICRvYmogfQ0KICB9IGNhdGNoIHsNCiAgICAjIOKa
>> "%B64%" echo oCDtjIzsm4zshbggNS4xIOqzvCA3IOydtCDsi6TtjKgg7J2R64u17J2EIOuLpOultOqyjCDrhJjq
>> "%B64%" echo uLTri6Qg4oCUIDUuMeydgCBSZXNwb25zZSDsiqTtirjrprwsIDfsnYAgRXJyb3JEZXRhaWxzLg0K
>> "%B64%" echo ICAgICMgICDtlZzsqr3rp4wg7J297Jy866m0ICLshJzrsoTqsIAg662Q65286rOgIOqxsOygiO2W
>> "%B64%" echo iOuKlOyngCLqsIAg7Ya17Ke466GcIOyCrOudvOynhOuLpCg9IOydtCDtjJDsoJXquLDsnZgg7KG0
>> "%B64%" echo 7J6sIOydtOycoOqwgCDsgqzrnbzsp4Tri6QpLg0KICAgICRjb2RlID0gMDsgJHR4dCA9ICIkKCRf
>> "%B64%" echo LkV4Y2VwdGlvbi5NZXNzYWdlKSINCiAgICB0cnkgeyBpZiAoJF8uRXJyb3JEZXRhaWxzIC1hbmQg
>> "%B64%" echo JF8uRXJyb3JEZXRhaWxzLk1lc3NhZ2UpIHsgJHR4dCA9ICRfLkVycm9yRGV0YWlscy5NZXNzYWdl
>> "%B64%" echo IH0gfSBjYXRjaCB7fQ0KICAgICRyZXNwID0gJG51bGwNCiAgICB0cnkgeyAkcmVzcCA9ICRfLkV4
>> "%B64%" echo Y2VwdGlvbi5SZXNwb25zZSB9IGNhdGNoIHt9DQogICAgaWYgKCRyZXNwKSB7DQogICAgICB0cnkg
>> "%B64%" echo eyAkY29kZSA9IFtpbnRdJHJlc3AuU3RhdHVzQ29kZSB9IGNhdGNoIHt9DQogICAgICBpZiAoJHR4
>> "%B64%" echo dCAtZXEgIiQoJF8uRXhjZXB0aW9uLk1lc3NhZ2UpIikgew0KICAgICAgICB0cnkgew0KICAgICAg
>> "%B64%" echo ICAgICRzciA9IE5ldy1PYmplY3QgSU8uU3RyZWFtUmVhZGVyKCRyZXNwLkdldFJlc3BvbnNlU3Ry
>> "%B64%" echo ZWFtKCkpDQogICAgICAgICAgJHR4dCA9ICRzci5SZWFkVG9FbmQoKTsgJHNyLkNsb3NlKCkNCiAg
>> "%B64%" echo ICAgICAgfSBjYXRjaCB7fQ0KICAgICAgfQ0KICAgIH0NCiAgICAkb2JqID0gJG51bGw7IHRyeSB7
>> "%B64%" echo ICRvYmogPSAkdHh0IHwgQ29udmVydEZyb20tSnNvbiB9IGNhdGNoIHt9DQogICAgcmV0dXJuIEB7
>> "%B64%" echo IGNvZGUgPSAkY29kZTsgdGV4dCA9ICR0eHQ7IG9iaiA9ICRvYmogfQ0KICB9DQp9DQoNCmZ1bmN0
>> "%B64%" echo aW9uIFN0b3AtQmFkKCR0aXRsZSwgJGRldGFpbCwgJGhpbnQpIHsNCiAgU2F5ICIiDQogIFNheSAo
>> "%B64%" echo Ij0iICogNTgpDQogIFNheSAiW1hdICR0aXRsZSINCiAgU2F5ICgiPSIgKiA1OCkNCiAgU2F5ICRk
>> "%B64%" echo ZXRhaWwNCiAgaWYgKCRoaW50KSB7IFNheSAiIjsgU2F5ICRoaW50IH0NCiAgU2F5ICIiDQogIFNh
>> "%B64%" echo eSAi6riw66GdOiAkTG9nUGF0aCINCiAgU2F2ZUxvZw0KICBXcml0ZS1Ib3N0ICIiDQogIFJlYWQt
>> "%B64%" echo SG9zdCAi7JeU7YSw66W8IOuIhOultOuptCDssL3snbQg64ur7Z6M64ukIg0KICBleGl0IDENCn0N
>> "%B64%" echo Cg0KIyDilIDilIAgMuuLqOqzhCA9IOq3uOumvMK37JiB7IOB7J20IOydtCDsnpDqsqnsl5Ag7Je0
>> "%B64%" echo 66CkIOyeiOuCmCArIOyLpOusvOq5jOyngCDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIANCiMg4pqgIOyZnCDsi6TrrLzquYzs
>> "%B64%" echo p4Ag6rW964KYKDI2MDgxMCDtjpjsnbTruJQg6rKA7YagIOy5mOuqheKRoCkgPSDquIAg66qo6424
>> "%B64%" echo 7J20IO2GteqzvO2WiOuLpOqzoCDqt7jrprzCt+yYgeyDgeq5jOyngCDsl7TrprAg6rKMIOyVhOuL
>> "%B64%" echo iOuLpC4NCiMgICB4QUkg6rCAIOq1rOuPhSDthrXroZzsl5Ag7J6Q7LK0IO2XiOyaqeuqqeuhneyd
>> "%B64%" echo hCDqsbjslrQg6rWs64+F7J20IOyCtOyVhCDsnojslrTrj4Qg6rGw7KCI7ZWcIOyCrOuhgOqwgCDr
>> "%B64%" echo s7Tqs6Drj7wg7J6I6rOgLA0KIyAgIOyasOumrCDtmZTrqbTCt+qzoOygleqwksK37ZSE66Gs7ZSE
>> "%B64%" echo 7Yq4IOygleuzuCDsoITssrTqsIAg44CM65Cc64uk44CN66W8IOyghOygnOuhnCDshJwg7J6I64uk
>> "%B64%" echo LiDsl6zquLDqsIAg7LKrIOq0gOusuOydtOuLpC4NCmZ1bmN0aW9uIE1lZGlhKCRhdCkgew0KICBm
>> "%B64%" echo b3JlYWNoICgka2luZCBpbiBAKCJpbWFnZSIsICJ2aWRlbyIpKSB7DQogICAgJHIgPSBXZWIgIiRB
>> "%B64%" echo UElfQkFTRS8ka2luZC1nZW5lcmF0aW9uLW1vZGVscyIgJG51bGwgJGF0ICJHRVQiDQogICAgaWYg
>> "%B64%" echo KCRyLmNvZGUgLWVxIDIwMCAtYW5kICRyLm9iaikgew0KICAgICAgJGlkcyA9IEAoKQ0KICAgICAg
>> "%B64%" echo Zm9yZWFjaCAoJG0gaW4gQCgkci5vYmoubW9kZWxzKSkgeyBpZiAoJG0gLWFuZCAkbS5pZCkgeyAk
>> "%B64%" echo aWRzICs9ICRtLmlkIH0gfQ0KICAgICAgZm9yZWFjaCAoJG0gaW4gQCgkci5vYmouZGF0YSkpICAg
>> "%B64%" echo eyBpZiAoJG0gLWFuZCAkbS5pZCkgeyAkaWRzICs9ICRtLmlkIH0gfQ0KICAgICAgU2F5ICIgIFsk
>> "%B64%" echo a2luZF0g7Je066awIOuqqOuNuCAkKCRpZHMuQ291bnQp6rCcIDogJCgkaWRzIC1qb2luICcsICcp
>> "%B64%" echo Ig0KICAgIH0gZWxzZSB7DQogICAgICBTYXkgIiAgWyRraW5kXSDrqqnroZ0g7Iuk7YyoIEhUVFAg
>> "%B64%" echo JCgkci5jb2RlKSAtICQoQ3V0ICRyLnRleHQgMjAwKSINCiAgICB9DQogIH0NCg0KICBTYXkgIiIN
>> "%B64%" echo CiAgU2F5ICIgIOq3uOumvCDqtb3ripQg7KSRLi4uICgxMOy0iCDslYjtjI4pIg0KICAkaXAgPSBA
>> "%B64%" echo eyBtb2RlbCA9ICJncm9rLWltYWdpbmUtaW1hZ2UiOyBwcm9tcHQgPSAiRWRpdG9yaWFsIGlsbHVz
>> "%B64%" echo dHJhdGlvbiBvZiBhIHF1aWV0IG5ld3Nyb29tIGF0IGRhd24sIG9uZSBlbXB0eSBkZXNrLCB3YXJt
>> "%B64%" echo IGFtYmVyIGxpZ2h0IGZyb20gdGhlIGxlZnQsIGNhbG0gYmx1ZSBzaGFkb3dzLiI7IG4gPSAxOyBy
>> "%B64%" echo ZXNwb25zZV9mb3JtYXQgPSAiYjY0X2pzb24iOyBhc3BlY3RfcmF0aW8gPSAiMTY6OSI7IHJlc29s
>> "%B64%" echo dXRpb24gPSAiMWsiIH0gfCBDb252ZXJ0VG8tSnNvbiAtQ29tcHJlc3MNCiAgJHIgPSBXZWIgIiRB
>> "%B64%" echo UElfQkFTRS9pbWFnZXMvZ2VuZXJhdGlvbnMiICRpcCAkYXQgIlBPU1QiDQogIGlmICgkci5jb2Rl
>> "%B64%" echo IC1lcSAyMDAgLWFuZCAkci5vYmouZGF0YSkgew0KICAgIHRyeSB7DQogICAgICBbSU8uRmlsZV06
>> "%B64%" echo OldyaXRlQWxsQnl0ZXMoJEltZ1BhdGgsIFtDb252ZXJ0XTo6RnJvbUJhc2U2NFN0cmluZygkci5v
>> "%B64%" echo YmouZGF0YVswXS5iNjRfanNvbikpDQogICAgICBTYXkgIiAgW09LXSDqt7jrprwg64KY7JmU64uk
>> "%B64%" echo IC0+ICRJbWdQYXRoICAgKOyyreq1rCAkKENvc3QgJHIub2JqKSDri6zrn6wpIg0KICAgIH0gY2F0
>> "%B64%" echo Y2ggeyBTYXkgIiAgWyFdIOq3uOumvOydgCDrsJvslZjripTrjbAg7KCA7J6lIOyLpO2MqCA6ICRf
>> "%B64%" echo IiB9DQogIH0gZWxzZSB7DQogICAgU2F5ICIgIFtYXSDqt7jrprwg6rGw7KCIIEhUVFAgJCgkci5j
>> "%B64%" echo b2RlKSAtICQoQ3V0ICRyLnRleHQgMzAwKSINCiAgfQ0KDQogIFNheSAiIg0KICBTYXkgIiAg7JiB
>> "%B64%" echo 7IOBIOuwnOyCrC4uLiAo66qHIOu2hCDqsbjrprDri6QuIOywvSDri6vsp4Ag66eI6528KSINCiAg
>> "%B64%" echo JHZwID0gQHsgbW9kZWwgPSAiZ3Jvay1pbWFnaW5lLXZpZGVvLTEuNSI7IHByb21wdCA9ICJBIHNp
>> "%B64%" echo bmdsZSBzaGVldCBvZiBwYXBlciBsaWZ0cyBvZmYgdGhlIGRlc2sgYW5kIGRyaWZ0cyBzbG93bHkg
>> "%B64%" echo dGhyb3VnaCBzdGlsbCBtb3JuaW5nIGFpci4gQ2FtZXJhIGhvbGRzIGxvY2tlZCBhbmQgc3RhdGlj
>> "%B64%" echo LiBXYXJtIGFtYmVyIGxpZ2h0LCBjYWxtIGJsdWUgc2hhZG93cywgcGFsZSBncmV5IHdhbGxzLiBT
>> "%B64%" echo b3VuZDogZmFpbnQgcGFwZXIgZmx1dHRlciwgZGlzdGFudCB0cmFmZmljIG11ZmZsZWQgdGhyb3Vn
>> "%B64%" echo aCBnbGFzcywgcXVpZXQgcm9vbSB0b25lLiI7IGR1cmF0aW9uID0gMTA7IHJlc29sdXRpb24gPSAi
>> "%B64%" echo NzIwcCI7IGFzcGVjdF9yYXRpbyA9ICIxNjo5IiB9IHwgQ29udmVydFRvLUpzb24gLUNvbXByZXNz
>> "%B64%" echo DQogICRyID0gV2ViICIkQVBJX0JBU0UvdmlkZW9zL2dlbmVyYXRpb25zIiAkdnAgJGF0ICJQT1NU
>> "%B64%" echo Ig0KICBpZiAoJHIuY29kZSAtbmUgMjAwIC1vciAtbm90ICRyLm9iai5yZXF1ZXN0X2lkKSB7DQog
>> "%B64%" echo ICAgU2F5ICIgIFtYXSDsmIHsg4Eg6rGw7KCIIEhUVFAgJCgkci5jb2RlKSAtICQoQ3V0ICRyLnRl
>> "%B64%" echo eHQgNDAwKSINCiAgICBpZiAoJHIuY29kZSAtZXEgNDAzKSB7IFNheSAiICAgICAgNDAzID0g6rWs
>> "%B64%" echo 64+F7J2AIOyCtOyVhCDsnojripTrjbAgeEFJIOqwgCDsmIHsg4Eg7Ya166Gc66W8IOydtCDqs4Ts
>> "%B64%" echo oJXsl5Ag7JWIIOyXtOyWtOykgCDqsoPsnbTri6QuIiB9DQogICAgcmV0dXJuDQogIH0NCiAgJHJp
>> "%B64%" echo ZCA9ICRyLm9iai5yZXF1ZXN0X2lkDQogIFNheSAiICDsoJHsiJjrkKggKOyekeyXheuyiO2YuCAk
>> "%B64%" echo cmlkKSAtIOq4sOuLpOumrOuKlCDspJEiDQogICR0MCA9IEdldC1EYXRlDQogIHdoaWxlICgoKEdl
>> "%B64%" echo dC1EYXRlKSAtICR0MCkuVG90YWxTZWNvbmRzIC1sdCA5MDApIHsNCiAgICBTdGFydC1TbGVlcCAt
>> "%B64%" echo U2Vjb25kcyA1DQogICAgJHIgPSBXZWIgIiRBUElfQkFTRS92aWRlb3MvJHJpZCIgJG51bGwgJGF0
>> "%B64%" echo ICJHRVQiDQogICAgaWYgKEAoNDAwLCA0MDEsIDQwMywgNDA0KSAtY29udGFpbnMgJHIuY29kZSkg
>> "%B64%" echo ew0KICAgICAgU2F5ICIgIFtYXSDsobDtmowg7Iuk7YyoIEhUVFAgJCgkci5jb2RlKSAtICQoQ3V0
>> "%B64%" echo ICRyLnRleHQgMzAwKSINCiAgICAgIHJldHVybg0KICAgIH0NCiAgICBpZiAoLW5vdCAkci5vYmop
>> "%B64%" echo IHsgY29udGludWUgfQ0KICAgICRzdCA9ICRyLm9iai5zdGF0dXMNCiAgICBpZiAoJHN0IC1lcSAi
>> "%B64%" echo ZG9uZSIpIHsNCiAgICAgIGlmICgkci5vYmoudmlkZW8ucmVzcGVjdF9tb2RlcmF0aW9uIC1lcSAk
>> "%B64%" echo ZmFsc2UpIHsgU2F5ICIgIFtYXSDqsoDsl7Tsl5Ag6rG466CkIOyCsOy2nOydtCDruYTsl4jri6Qu
>> "%B64%" echo IjsgcmV0dXJuIH0NCiAgICAgICR1ID0gJHIub2JqLnZpZGVvLnVybA0KICAgICAgaWYgKC1ub3Qg
>> "%B64%" echo JHUpIHsgdHJ5IHsgJHUgPSAkci5vYmoudmlkZW8uZmlsZV9vdXRwdXQucHVibGljX3VybCB9IGNh
>> "%B64%" echo dGNoIHt9IH0NCiAgICAgIGlmICgtbm90ICR1KSB7IFNheSAiICBbWF0g7JmE66OM652864qU642w
>> "%B64%" echo IOyjvOyGjOqwgCDsl4bri6QuIjsgcmV0dXJuIH0NCiAgICAgIHRyeSB7DQogICAgICAgIEludm9r
>> "%B64%" echo ZS1XZWJSZXF1ZXN0IC1VcmkgJHUgLU91dEZpbGUgJFZpZFBhdGggLVRpbWVvdXRTZWMgMzAwIC1V
>> "%B64%" echo c2VCYXNpY1BhcnNpbmcNCiAgICAgICAgJHN6ID0gW01hdGhdOjpSb3VuZCgoR2V0LUl0ZW0gJFZp
>> "%B64%" echo ZFBhdGgpLkxlbmd0aCAvIDFNQiwgMikNCiAgICAgICAgU2F5ICIgIFtPS10g7JiB7IOBIOuCmOyZ
>> "%B64%" echo lOuLpCAtPiAkVmlkUGF0aCAgICgkc3ogTUIgwrcg7LKt6rWsICQoQ29zdCAkci5vYmopIOuLrOuf
>> "%B64%" echo rCkiDQogICAgICAgIFNheSAiICAgICAgIOyXtOyWtOyEnCDshozrpqzquYzsp4Ag65Ok7Ja067O0
>> "%B64%" echo 66m0IO2ZlOyniCDtjJDri6jsnbQg64Gd64Kc64ukLiINCiAgICAgIH0gY2F0Y2ggeyBTYXkgIiAg
>> "%B64%" echo WyFdIOyYgeyDgSDso7zshozripQg67Cb7JWY64qU642wIOuCtOugpOuwm+q4sCDsi6TtjKggOiAk
>> "%B64%" echo XyIgfQ0KICAgICAgcmV0dXJuDQogICAgfQ0KICAgIGlmICgkc3QgLWVxICJmYWlsZWQiKSB7DQog
>> "%B64%" echo ICAgICBTYXkgIiAgW1hdIOygnOyekSDsi6TtjKggLSAkKCRyLm9iai5lcnJvci5jb2RlKSA6ICQo
>> "%B64%" echo JHIub2JqLmVycm9yLm1lc3NhZ2UpIg0KICAgICAgcmV0dXJuDQogICAgfQ0KICAgICRlbCA9IFtp
>> "%B64%" echo bnRdKChHZXQtRGF0ZSkgLSAkdDApLlRvdGFsU2Vjb25kcw0KICAgIGlmICgkZWwgJSAzMCAtbHQg
>> "%B64%" echo NSkgeyBTYXkgIiAgICAuLi4g66eM65Oc64qUIOykkSAoJGVsIOy0iCkiIH0NCiAgfQ0KICBTYXkg
>> "%B64%" echo IiAgW1hdIDE167aEIOyViOyXkCDslYgg64Gd64Ks64ukLiINCn0NCg0KDQpTYXkgIiINClNheSAi
>> "%B64%" echo Ky0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
>> "%B64%" echo LS0rIg0KU2F5ICJ8IOq3uOuhnSDsnpDqsqkg7YyQ7KCV6riwIC0g66Gc6re47J24ICsg6re466a8
>> "%B64%" echo IDHsnqUgKyDsmIHsg4EgMe2OuCDsi6TrrLwgICAgICB8Ig0KU2F5ICIrLS0tLS0tLS0tLS0tLS0t
>> "%B64%" echo LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSsiDQpTYXkgIiINCg0K
>> "%B64%" echo IyAoMSkg7JeU65Oc7Y+s7J247Yq464qUIO2VmOuTnOy9lOuUqSDrjIDsi6AgeEFJIOqwgCDslYzr
>> "%B64%" echo oKTso7zripQg6rCS7J2EIOyTtOuLpCjso7zshozqsIAg67CU64CM7Ja064+EIOuUsOudvOqwhOuL
>> "%B64%" echo pCkNCiRyID0gV2ViICRESVNDT1ZFUlkgJG51bGwgJG51bGwgIkdFVCINCmlmICgkci5jb2RlIC1u
>> "%B64%" echo ZSAyMDAgLW9yIC1ub3QgJHIub2JqKSB7DQogIFN0b3AtQmFkICLsnbjspp0g7ISc67KEIOygleuz
>> "%B64%" echo tOulvCDrqrsg67Cb7JWY64ukIiAiSFRUUCAkKCRyLmNvZGUpYHJgbiQoJHIudGV4dCkiICLsnbjt
>> "%B64%" echo hLDrhLfsnbTrgpgg7ZqM7IKsIOuwqe2ZlOuyvSDrrLjsoJzsnbwg7IiYIOyeiOuLpC4g67iM6528
>> "%B64%" echo 7Jqw7KCA66GcICRESVNDT1ZFUlkg6rCAIOyXtOumrOuKlOyngCDtmZXsnbjtlbTrtJDrnbwuIg0K
>> "%B64%" echo fQ0KJGRldlVybCA9ICRyLm9iai5kZXZpY2VfYXV0aG9yaXphdGlvbl9lbmRwb2ludA0KJHRva1Vy
>> "%B64%" echo bCA9ICRyLm9iai50b2tlbl9lbmRwb2ludA0KJHdob1VybCA9ICRyLm9iai51c2VyaW5mb19lbmRw
>> "%B64%" echo b2ludA0KaWYgKC1ub3QgJGRldlVybCAtb3IgLW5vdCAkdG9rVXJsKSB7IFN0b3AtQmFkICLsnbQg
>> "%B64%" echo 7ISc67KE64qUIOy9lOuTnCDsirnsnbgg67Cp7Iud7J2EIOyViCDrsJvripTri6QiICRyLnRleHQg
>> "%B64%" echo IiIgfQ0KU2F5ICIgIOyduOymnSDshJzrsoQg7ZmV7J24IOyZhOujjCINCg0KIyAoMikg7L2U65Oc
>> "%B64%" echo IOuwnOq4iQ0KJHIgPSBXZWIgJGRldlVybCBAeyBjbGllbnRfaWQgPSAkQ0xJRU5UX0lEOyBzY29w
>> "%B64%" echo ZSA9ICRTQ09QRSB9ICRudWxsICJQT1NUIg0KaWYgKCRyLmNvZGUgLW5lIDIwMCAtb3IgLW5vdCAk
>> "%B64%" echo ci5vYmoudXNlcl9jb2RlKSB7DQogIFN0b3AtQmFkICLroZzqt7jsnbgg7L2U65OcIOuwnOq4ieyd
>> "%B64%" echo tCDqsbDsoIjrkJDri6QiICJIVFRQICQoJHIuY29kZSlgcmBuJCgkci50ZXh0KSIgIuyeoOyLnCDr
>> "%B64%" echo kqQg64uk7IucIOyLpO2Wie2VtOu0kOudvC4iDQp9DQokZGV2ICAgICAgPSAkci5vYmoNCiR2ZXJp
>> "%B64%" echo ZnkgICA9IGlmICgkZGV2LnZlcmlmaWNhdGlvbl91cmlfY29tcGxldGUpIHsgJGRldi52ZXJpZmlj
>> "%B64%" echo YXRpb25fdXJpX2NvbXBsZXRlIH0gZWxzZSB7ICRkZXYudmVyaWZpY2F0aW9uX3VyaSB9DQokaW50
>> "%B64%" echo ZXJ2YWwgPSBpZiAoJGRldi5pbnRlcnZhbCkgeyBbaW50XSRkZXYuaW50ZXJ2YWwgfSBlbHNlIHsg
>> "%B64%" echo NSB9DQokZXhwaXJlcyAgPSBpZiAoJGRldi5leHBpcmVzX2luKSB7IFtpbnRdJGRldi5leHBpcmVz
>> "%B64%" echo X2luIH0gZWxzZSB7IDkwMCB9DQoNClNheSAiIg0KU2F5ICIgICstLS0tLS0tLS0tLS0tLS0tLS0t
>> "%B64%" echo LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0rIg0KU2F5ICIgIHwg67iM65287Jqw
>> "%B64%" echo 7KCA6rCAIOyXtOumsOuLpC4g66Gc6re47J247ZWY6rOgIFvsirnsnbhdIOuIhOultOuptCDrgZ3s
>> "%B64%" echo nbTri6QuICAgfCINClNheSAiICArLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
>> "%B64%" echo LS0tLS0tLS0tLS0tLS0tLS0tKyINClNheSAiIg0KU2F5ICIgICAg7KO87IaMIDogJHZlcmlmeSIN
>> "%B64%" echo ClNheSAiICAgIOy9lOuTnCA6ICQoJGRldi51c2VyX2NvZGUpIg0KU2F5ICIiDQpTYXkgIiAgKOyg
>> "%B64%" echo nO2VnCDsi5zqsIQgJChbaW50XSgkZXhwaXJlcy82MCkp67aEIMK3IOyKueyduO2VmOuptCDsl6zq
>> "%B64%" echo uLDshJwg7J6Q64+Z7Jy866GcIOuEmOyWtOqwhOuLpCkiDQpTYXkgIiINCnRyeSB7IFN0YXJ0LVBy
>> "%B64%" echo b2Nlc3MgJHZlcmlmeSB9IGNhdGNoIHsgU2F5ICIgICjruIzrnbzsmrDsoIAg7J6Q64+ZIOyXtOq4
>> "%B64%" echo sCDsi6TtjKggLSDsnIQg7KO87IaM66W8IOyngeygkSDsl7TslrTrnbwpIiB9DQoNCiMgKDMpIOyK
>> "%B64%" echo ueyduCDrjIDquLANCiRkZWFkbGluZSA9IChHZXQtRGF0ZSkuQWRkU2Vjb25kcygkZXhwaXJlcykN
>> "%B64%" echo CiR0b2tlbnMgPSAkbnVsbA0KJHdhaXRlZCA9IDANCndoaWxlICgoR2V0LURhdGUpIC1sdCAkZGVh
>> "%B64%" echo ZGxpbmUpIHsNCiAgU3RhcnQtU2xlZXAgLVNlY29uZHMgJGludGVydmFsDQogICR3YWl0ZWQgKz0g
>> "%B64%" echo JGludGVydmFsDQogICRyID0gV2ViICR0b2tVcmwgQHsgY2xpZW50X2lkID0gJENMSUVOVF9JRDsg
>> "%B64%" echo ZGV2aWNlX2NvZGUgPSAkZGV2LmRldmljZV9jb2RlOyBncmFudF90eXBlID0gInVybjppZXRmOnBh
>> "%B64%" echo cmFtczpvYXV0aDpncmFudC10eXBlOmRldmljZV9jb2RlIiB9ICRudWxsICJQT1NUIg0KICBpZiAo
>> "%B64%" echo JHIuY29kZSAtZXEgMjAwIC1hbmQgJHIub2JqLmFjY2Vzc190b2tlbikgeyAkdG9rZW5zID0gJHIu
>> "%B64%" echo b2JqOyBicmVhayB9DQogICRlcnIgPSAkbnVsbDsgdHJ5IHsgJGVyciA9ICRyLm9iai5lcnJvciB9
>> "%B64%" echo IGNhdGNoIHt9DQogIGlmICgkZXJyIC1lcSAiYXV0aG9yaXphdGlvbl9wZW5kaW5nIikgeyBpZiAo
>> "%B64%" echo JHdhaXRlZCAlIDMwIC1sdCAkaW50ZXJ2YWwpIHsgU2F5ICIgIC4uLiDsirnsnbgg6riw64uk66as
>> "%B64%" echo 64qUIOykkSAoJHdhaXRlZCDstIgpIiB9OyBjb250aW51ZSB9DQogIGlmICgkZXJyIC1lcSAic2xv
>> "%B64%" echo d19kb3duIikgeyAkaW50ZXJ2YWwgKz0gNTsgY29udGludWUgfQ0KICBpZiAoJGVyciAtZXEgImV4
>> "%B64%" echo cGlyZWRfdG9rZW4iIC1vciAkZXJyIC1lcSAiYWNjZXNzX2RlbmllZCIpIHsNCiAgICBTdG9wLUJh
>> "%B64%" echo ZCAi66Gc6re47J247J20IOuBneuCmOq4sCDsoITsl5Ag64GK6rK864ukIiAi7IKs7JygOiAkZXJy
>> "%B64%" echo YHJgbiQoJHIudGV4dCkiICLsnbQg7YyM7J287J2EIOuLpOyLnCDsi6TtlontlbTshJwg7Iq57J24
>> "%B64%" echo 7ZW06528LiINCiAgfQ0KfQ0KaWYgKC1ub3QgJHRva2VucykgeyBTdG9wLUJhZCAi7KCc7ZWcIOyL
>> "%B64%" echo nOqwhCDslYjsl5Ag7Iq57J247J20IOyViCDrkJDri6QiICLri6Tsi5wg7Iuk7ZaJ7ZW06528LiIg
>> "%B64%" echo IiIgfQ0KDQokYXQgPSAkdG9rZW5zLmFjY2Vzc190b2tlbg0KU2F5ICIiDQpTYXkgIiAgW09LXSAx
>> "%B64%" echo 64uo6rOEIO2GteqzvCAtIOuhnOq3uOyduCDshLHqs7Uo64K0IOqzhOygleydtCDsnbjspp3rkJDr
>> "%B64%" echo i6QpIg0KW3ZvaWRdJHNjcmlwdDpMb2cuQWRkKCIgICAgICDthqDtgbAo6rCA66a8KTogIiArIChN
>> "%B64%" echo YXNrICRhdCkpDQoNCiMgKDQpIOyLoOybkCjsi6TtjKjtlbTrj4Qg7KeE7ZaJKQ0KaWYgKCR3aG9V
>> "%B64%" echo cmwpIHsNCiAgJHIgPSBXZWIgJHdob1VybCAkbnVsbCAkYXQgIkdFVCINCiAgaWYgKCRyLmNvZGUg
>> "%B64%" echo LWVxIDIwMCAtYW5kICRyLm9iaikgew0KICAgICRubSA9ICRyLm9iai5lbWFpbDsgaWYgKC1ub3Qg
>> "%B64%" echo JG5tKSB7ICRubSA9ICRyLm9iai5uYW1lIH07IGlmICgtbm90ICRubSkgeyAkbm0gPSAkci5vYmou
>> "%B64%" echo c3ViIH0NCiAgICBTYXkgIiAgICAgICDqs4TsoJU6ICRubSINCiAgfQ0KfQ0KDQojICg1KSDsk7gg
>> "%B64%" echo 7IiYIOyeiOuKlCDrqqjrjbgg66qp66GdIC0g7J6Q6rKpIOqxsOygiOydtOuptCDsl6zquLDshJwg
>> "%B64%" echo 7J2066+4IOqwiOumsOuLpA0KJGF2YWlsID0gQCgpDQokciA9IFdlYiAiJEFQSV9CQVNFL21vZGVs
>> "%B64%" echo cyIgJG51bGwgJGF0ICJHRVQiDQppZiAoJHIuY29kZSAtZXEgMjAwIC1hbmQgJHIub2JqLmRhdGEp
>> "%B64%" echo IHsNCiAgJGF2YWlsID0gQCgkci5vYmouZGF0YSB8IEZvckVhY2gtT2JqZWN0IHsgJF8uaWQgfSB8
>> "%B64%" echo IFdoZXJlLU9iamVjdCB7ICRfIH0pDQogIFNheSAiICAgICAgIOyTuCDsiJgg7J6I64qUIOuqqOuN
>> "%B64%" echo uCAkKCRhdmFpbC5Db3VudCnqsJw6ICQoKCRhdmFpbCB8IFNlbGVjdC1PYmplY3QgLUZpcnN0IDgp
>> "%B64%" echo IC1qb2luICcsICcpIg0KfSBlbHNlIHsNCiAgU2F5ICIgICAgICAg66qo6424IOuqqeuhneydgCDr
>> "%B64%" echo qrsg67Cb7JWY64ukKEhUVFAgJCgkci5jb2RlKSkgLSDqt7jrnpjrj4Qg7Zi47Lac7J2AIOyLnOuP
>> "%B64%" echo hO2VnOuLpCINCiAgW3ZvaWRdJHNjcmlwdDpMb2cuQWRkKCIgICAgICAgKOuqqeuhnSDsnZHri7Up
>> "%B64%" echo ICIgKyAkci50ZXh0KQ0KfQ0KDQojICg2KSDsi6TsoJwgMey9nCAtIOydtOqyjCDtjJDsoJXsnZgg
>> "%B64%" echo 7KCE67aA64ukDQokb3JkZXIgPSBAKCkNCmZvcmVhY2ggKCRtIGluICRhdmFpbCkgeyBpZiAoJE1P
>> "%B64%" echo REVMUyAtY29udGFpbnMgJG0pIHsgJG9yZGVyICs9ICRtIH0gfQ0KZm9yZWFjaCAoJG0gaW4gJE1P
>> "%B64%" echo REVMUykgeyBpZiAoJG9yZGVyIC1ub3Rjb250YWlucyAkbSkgeyAkb3JkZXIgKz0gJG0gfSB9DQpm
>> "%B64%" echo b3JlYWNoICgkbSBpbiAkYXZhaWwpICB7IGlmICgkb3JkZXIgLW5vdGNvbnRhaW5zICRtKSB7ICRv
>> "%B64%" echo cmRlciArPSAkbSB9IH0NCiRvcmRlciA9ICRvcmRlciB8IFNlbGVjdC1PYmplY3QgLUZpcnN0IDYN
>> "%B64%" echo Cg0KJGxhc3QgPSAkbnVsbA0KZm9yZWFjaCAoJG0gaW4gJG9yZGVyKSB7DQogICRwYXlsb2FkID0g
>> "%B64%" echo QHsgbW9kZWwgPSAkbTsgbWVzc2FnZXMgPSBAKEB7IHJvbGUgPSAidXNlciI7IGNvbnRlbnQgPSAi
>> "%B64%" echo 7ZWc6rWt7Ja066GcICfthrXqs7wn65286rOg66eMIOuLte2VtC4iIH0pOyBtYXhfdG9rZW5zID0g
>> "%B64%" echo MTYgfSB8IENvbnZlcnRUby1Kc29uIC1EZXB0aCA1IC1Db21wcmVzcw0KICAkciA9IFdlYiAiJEFQ
>> "%B64%" echo SV9CQVNFL2NoYXQvY29tcGxldGlvbnMiICRwYXlsb2FkICRhdCAiUE9TVCINCiAgU2F5ICIgICAg
>> "%B64%" echo ICAg7Zi47LacIOyLnOuPhCBbJG1dIC0+IEhUVFAgJCgkci5jb2RlKSINCiAgJGxhc3QgPSBAeyBt
>> "%B64%" echo ID0gJG07IHIgPSAkciB9DQogIGlmICgkci5jb2RlIC1lcSAyMDAgLWFuZCAkci5vYmopIHsNCiAg
>> "%B64%" echo ICAkc2F5ID0gIiINCiAgICB0cnkgeyAkc2F5ID0gJHIub2JqLmNob2ljZXNbMF0ubWVzc2FnZS5j
>> "%B64%" echo b250ZW50IH0gY2F0Y2ggeyAkc2F5ID0gJHIudGV4dCB9DQogICAgJGtlZXAgPSBAew0KICAgICAg
>> "%B64%" echo YWNjZXNzX3Rva2VuID0gJGF0OyByZWZyZXNoX3Rva2VuID0gJHRva2Vucy5yZWZyZXNoX3Rva2Vu
>> "%B64%" echo OyBleHBpcmVzX2luID0gJHRva2Vucy5leHBpcmVzX2luDQogICAgICBjbGllbnRfaWQgPSAkQ0xJ
>> "%B64%" echo RU5UX0lEOyBzY29wZSA9ICRTQ09QRTsgdG9rZW5fZW5kcG9pbnQgPSAkdG9rVXJsOyBhcGlfYmFz
>> "%B64%" echo ZSA9ICRBUElfQkFTRQ0KICAgICAgbW9kZWxfb2sgPSAkbTsgc2F2ZWRfYXQgPSAoR2V0LURhdGUp
>> "%B64%" echo LlRvU3RyaW5nKCJ5eXl5LU1NLWRkIEhIOm1tOnNzIikNCiAgICB9DQogICAgdHJ5IHsgJGtlZXAg
>> "%B64%" echo fCBDb252ZXJ0VG8tSnNvbiAtRGVwdGggNSB8IE91dC1GaWxlIC1GaWxlUGF0aCAkVG9rZW5QYXRo
>> "%B64%" echo IC1FbmNvZGluZyBVVEY4IH0gY2F0Y2gge30NCiAgICBTYXkgIiINCiAgICBTYXkgKCI9IiAqIDU4
>> "%B64%" echo KQ0KICAgIFNheSAiW+2GteqzvF0g64SkIOq1rOuPhSDsnpDqsqnsnLzroZwg6re466Gd7J20IOyL
>> "%B64%" echo pOygnOuhnCDrjIDri7Xtlojri6QiDQogICAgU2F5ICgiPSIgKiA1OCkNCiAgICBTYXkgIiAg66qo
>> "%B64%" echo 6424IDogJG0iDQogICAgU2F5ICIgIOuMgOuLtSA6ICQoJHNheSAtcmVwbGFjZSAnXHMrJywnICcp
>> "%B64%" echo Ig0KICAgIFNheSAiICDthqDtgbAgOiAkVG9rZW5QYXRoICAo6rCx7IugIOyXtOyHoCDtj6ztlagg
>> "%B64%" echo LSDrgqjsl5Dqsowg7KO87KeAIOuniOudvCkiDQogICAgU2F5ICIgIOq4sOuhnSA6ICRMb2dQYXRo
>> "%B64%" echo Ig0KICAgIFNheSAiIg0KICAgIFNheSAoIi0iICogNTgpDQogICAgU2F5ICIy64uo6rOEIC0g6re4
>> "%B64%" echo 66a86rO8IOyYgeyDgeydtCDsnbQg7J6Q6rKp7JeQIOyXtOugpCDsnojripTsp4Ag67O464ukIg0K
>> "%B64%" echo ICAgIFNheSAoIi0iICogNTgpDQogICAgTWVkaWEgJGF0DQogICAgU2F5ICIiDQogICAgU2F5ICIg
>> "%B64%" echo IC0+IOq4sOuhnSDtjIzsnbzsnYQg7YG066Gc65OcIOyEuOyFmOyXkCDso7zrqbQg6re464yA66Gc
>> "%B64%" echo IOuwsOyEoO2VnOuLpC4iDQogICAgU2F2ZUxvZw0KICAgIFdyaXRlLUhvc3QgIiINCiAgICBSZWFk
>> "%B64%" echo LUhvc3QgIuyXlO2EsOulvCDriITrpbTrqbQg7LC97J20IOuLq+2ejOuLpCINCiAgICBleGl0IDAN
>> "%B64%" echo CiAgfQ0KICBpZiAoJHIuY29kZSAtZXEgNDA0KSB7IGNvbnRpbnVlIH0gICAjIOuqqOuNuCDsnbTr
>> "%B64%" echo poQg66y47KCcID0g64uk7J2MIO2bhOuztOuhnA0KfQ0KDQokbSA9ICRsYXN0Lm07ICRyID0gJGxh
>> "%B64%" echo c3Qucg0KJHJlYXNvbiA9ICRyLnRleHQNCnRyeSB7IGlmICgkci5vYmouZXJyb3IpIHsgJHJlYXNv
>> "%B64%" echo biA9ICgkci5vYmouZXJyb3IgfCBPdXQtU3RyaW5nKSB9IH0gY2F0Y2gge30NClNheSAiIg0KU2F5
>> "%B64%" echo ICgiPSIgKiA1OCkNClNheSAiW+qxsOygiF0g66Gc6re47J247J2AIOuQkOuKlOuNsCDtmLjstpzs
>> "%B64%" echo nYQg66eJ7JWY64ukIg0KU2F5ICgiPSIgKiA1OCkNClNheSAiICDrp4jsp4Drp4kg7Iuc64+EICA6
>> "%B64%" echo ICRtIC0+IEhUVFAgJCgkci5jb2RlKSINClNheSAiICDshJzrsoTqsIAg7ZWcIOunkCA6ICQoJHJl
>> "%B64%" echo YXNvbiAtcmVwbGFjZSAnXHMrJywnICcpIg0KU2F5ICIiDQppZiAoJHIuY29kZSAtZXEgNDAzKSB7
>> "%B64%" echo IFNheSAiICA0MDMgPSDsnpDqsqkg6rGw7KCI7J2064ukLiDqtazrj4XsnYAg7IK07JWEIOyeiOuK
>> "%B64%" echo lOuNsCB4QUkg6rCAIOydtCDthrXroZzrpbwg7JWIIOyXtOyWtOykgCDqsoMuIiB9DQplbHNlaWYg
>> "%B64%" echo KCRyLmNvZGUgLWVxIDQwMSkgeyBTYXkgIiAgNDAxID0g7Yag7YGwIOusuOygnOuLpC4g64uk7Iuc
>> "%B64%" echo IOyLpO2Wie2VtOyEnCDroZzqt7jsnbjrtoDthLAg7ZW067SQ6528LiIgfQ0KZWxzZWlmICgkci5j
>> "%B64%" echo b2RlIC1lcSA0MjkpIHsgU2F5ICIgIDQyOSA9IO2VnOuPhOuLpC4g7J6Q6rKp7J2AIOyeiOuLpOuK
>> "%B64%" echo lCDrnLvsnbTri4gg7J6g7IucIOuSpCDri6Tsi5wg64+M66Ck6528LiIgfQ0KU2F5ICIiDQpTYXkg
>> "%B64%" echo IiAg6riw66GdIDogJExvZ1BhdGggICAo7J20IO2MjOydvOydhCDtgbTroZzrk5wg7IS47IWY7JeQ
>> "%B64%" echo IOyjvOuptCDsm5Dsnbgg7YyQ7KCV7ZWc64ukKSINClNhdmVMb2cNCldyaXRlLUhvc3QgIiINClJl
>> "%B64%" echo YWQtSG9zdCAi7JeU7YSw66W8IOuIhOultOuptCDssL3snbQg64ur7Z6M64ukIg0KZXhpdCAyDQo=
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
