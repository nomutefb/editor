@echo off
REM ===========================================================================
REM  nomute - Higgsfield entitlement probe : DOUBLE-CLICK, RUN ONCE
REM
REM  What it does: opens the Higgsfield sign-in page in your browser, exchanges
REM  your approval for a refresh token the CI runner can use, and then proves
REM  that token really unlocks Seedance before asking you to paste it anywhere.
REM  Spends NO credits (balance + cost preflight only, no job is submitted).
REM
REM  Installs nothing. Registers nothing. Nothing is left running.
REM  Results are written to your Desktop.
REM
REM  GENERATED FILE - do not edit by hand.
REM  Source of truth: scripts/hf_probe.ps1
REM  Regenerate     : python3 scripts/build_hf_probe_bundle.py
REM ===========================================================================
setlocal
chcp 65001 >nul 2>&1
set "NM=%TEMP%\nomute_hf"
if not exist "%NM%" mkdir "%NM%"
set "B64=%NM%\_probe.b64"
if exist "%B64%" del "%B64%"

echo.
echo   Unpacking...
>> "%B64%" echo 77u/IyDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi
>> "%B64%" echo lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi
>> "%B64%" echo lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi
>> "%B64%" echo lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi
>> "%B64%" echo lZDilZDilZDilZDilZANCiMgaGZfcHJvYmUucHMxICgy7YyQKSDigJQg7Z6J7Iqk7ZWE65OcIOye
>> "%B64%" echo kOqyqeydhCDrn6zrhIjqsIAg7JO4IOyImCDsnojripQgKirsl7Tsh6Ag7ZWcIOykhCoq66GcIOuw
>> "%B64%" echo lOq+vOuLpA0KIw0KIyDimqAgMe2MkCjquLDquLAg7L2U65OcIOuwqeyLnSnsnYAgKirrqqjrjbjs
>> "%B64%" echo nbQg7JWIIOyXtOuguOuLpCoqKDI2MDgxMiDsi6TsuKEgwrcg65+wIDMxNjI0NTY0MDAyKS4NCiMg
>> "%B64%" echo ICDsnpDqsqnrj4Qg7J6U7JWh64+EIO2GteqzvO2WiOuKlOuNsCgzLDA2MCDtgazroIjrlKcgwrcg
>> "%B64%" echo dWx0cmEpIOufrOuEiOqwgCDrs7TripQg66qo6424IOuqqeuhneydtCA27KKF67+Q7J206rOgDQoj
>> "%B64%" echo ICAg6re4IOyViOyXkCDsi5zrjITsiqTqsIAg7JeG7JeI64ukLiDqsJnsnYAg6rOE7KCV7J24642w
>> "%B64%" echo IOyCrOuejOydtCDrtpnsnbgg7Jew6rKw7JeQ7ISc64qUIOyLnOuMhOyKpOqwgCDqt7jrjIDroZwg
>> "%B64%" echo 66i57ZiU64ukDQojICAg4oaSIOywqOydtOuKlCAqKuyWtOuKkCDroZzqt7jsnbgg67Cp7Iud7Jy8
>> "%B64%" echo 66GcIOuwm+ydgCDsnpDqsqnsnbTrg5AqKuyYgOuLpC4g7LC96rWs6rCAIOqzteqwnO2VnCDslYjr
>> "%B64%" echo grTsl5Drj4Qg6riw6riwIOy9lOuTnCDrsKnsi53snYANCiMgICDri6Trpbgg7ZSE66Gc6re4656o
>> "%B64%" echo 7Jqp7Jy866GcIOygge2YgCDsnojri6QuIOKGkiAy7YyQ7J2AICoq67iM65287Jqw7KCAIOuwqeyL
>> "%B64%" echo nSoqKOyCrOuejOydtCDrtpnsnbgg7Jew6rKw6rO8IOqwmeydgCDquLgp7Jy866GcIOqwhOuLpC4N
>> "%B64%" echo CiMNCiMg7Z2Q66aEKOyLpOy4oSDqt5zqsqkgwrcgMjYwODEyKSA9DQojICAg4pGgIFBPU1QgL29h
>> "%B64%" echo dXRoMi9yZWdpc3RlciAg4oaSIOyasOumrCDtlITroZzqt7jrnqgg67KI7Zi4KOuTseuhneyXkCDs
>> "%B64%" echo irnsnbgg67aI7JqUIMK3IOymieyLnCDrsJzquIkpDQojICAg4pGhIOu4jOudvOyasOyggOuhnCAv
>> "%B64%" echo b2F1dGgyL2F1dGhvcml6ZSAoUEtDRSkg4oaSIOuhnOq3uOyduMK37ZeI7JqpDQojICAg4pGiIOuC
>> "%B64%" echo tCBQQyDqsIAg7J6g6rmQIOyXsCDssL3qtazroZwg7Iq57J24IOy9lOuTnOqwgCDrj4zslYTsmKjr
>> "%B64%" echo i6QoMTI3LjAuMC4xKQ0KIyAgIOKRoyBQT1NUIC9vYXV0aDIvdG9rZW4g4oaSIOygkeyGjSDsl7Ts
>> "%B64%" echo h6AgKyAqKuqwseyLoCDsl7Tsh6AqKg0KIw0KIyDsgrDstpw6ICDrsJTtg5XtmZTrqbRc7Z6J7Iqk
>> "%B64%" echo 7ZWE65Oc7ZmV7J24X+qysOqzvC50eHQgICAo6riw66GdIMK3IOyXtOyHoOuKlCDslZ4gMTLsnpDr
>> "%B64%" echo p4wg64Ko6riw6rOgIOqwgOumsOuLpCkNCiMgICAgICAgIOuwlO2Dle2ZlOuptFztnonsiqTtlYTr
>> "%B64%" echo k5zsl7Tsh6Bf67aZ7Jes64Sj6riwLnR4dCAo67aZ7Jes64Sj7J2EIOqwkiAqKu2VnCDspIQqKiA9
>> "%B64%" echo IO2UhOuhnOq3uOueqOuyiO2YuDrqsLHsi6Dsl7Tsh6ApDQojIOuBhOuKlCDrspU6IOyViCDrj4zr
>> "%B64%" echo pqzrqbQg64GdLiDshKTsuZjrkJjripQg6rKD64+ELCDsnpDrj5kg7Iuk7ZaJ65CY64qUIOqyg+uP
>> "%B64%" echo hCDsl4bri6QuIO2BrOugiOuUpyAwLg0KIyDsg53shLEg7KCV67O4OiBzY3JpcHRzL2hmX3Byb2Jl
>> "%B64%" echo LnBzMSDCtyDrsojrk6Qg7J6s7IOd7ISxID0gcHl0aG9uMyBzY3JpcHRzL2J1aWxkX2hmX3Byb2Jl
>> "%B64%" echo X2J1bmRsZS5weQ0KIyDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi
>> "%B64%" echo lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi
>> "%B64%" echo lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi
>> "%B64%" echo lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi
>> "%B64%" echo lZDilZDilZDilZDilZDilZDilZDilZANCiRFcnJvckFjdGlvblByZWZlcmVuY2UgPSAiU3RvcCIN
>> "%B64%" echo CnRyeSB7IFtOZXQuU2VydmljZVBvaW50TWFuYWdlcl06OlNlY3VyaXR5UHJvdG9jb2wgPSBbTmV0
>> "%B64%" echo LlNlY3VyaXR5UHJvdG9jb2xUeXBlXTo6VGxzMTIgfSBjYXRjaCB7fQ0KdHJ5IHsgJE91dHB1dEVu
>> "%B64%" echo Y29kaW5nID0gW0NvbnNvbGVdOjpPdXRwdXRFbmNvZGluZyA9IFtUZXh0LkVuY29kaW5nXTo6VVRG
>> "%B64%" echo OCB9IGNhdGNoIHt9DQoNCiRCQVNFID0gImh0dHBzOi8vbWNwLmhpZ2dzZmllbGQuYWkiDQokUE9S
>> "%B64%" echo VCA9IDg3NjUNCiRSRURJUiA9ICJodHRwOi8vMTI3LjAuMC4xOiRQT1JUL2NhbGxiYWNrIg0KJFND
>> "%B64%" echo T1BFID0gIm9wZW5pZCBlbWFpbCBvZmZsaW5lX2FjY2VzcyINCiRTRUNSRVRfTkFNRSA9ICJISUdH
>> "%B64%" echo U0ZJRUxEX1JFRlJFU0hfVE9LRU4iDQojIOKaoCDssL3qtawg7JWe64uo7J20IO2MjOydtOyNrMK3
>> "%B64%" echo 6riw67O4IOyEnOuqheydhCDrp4nripTri6QoMTAxMCkg4oaSIOu4jOudvOyasOyggCDshJzrqoXs
>> "%B64%" echo nYQg64uo64ukKDI2MDgxMiDsi6TsuKEpLg0KJFVBID0gIk1vemlsbGEvNS4wIChXaW5kb3dzIE5U
>> "%B64%" echo IDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28p
>> "%B64%" echo IENocm9tZS8xNDEuMC4wLjAgU2FmYXJpLzUzNy4zNiINCg0KIyDimqAg67CU7YOV7ZmU66m0IOqy
>> "%B64%" echo veuhnOuKlCDruYgg66y47J6Q7Je066GcIOyYrCDsiJgg7J6I64ukKOybkOuTnOudvOydtOu4jCDr
>> "%B64%" echo sLHsl4Ug7Iuk7LihKSDihpIg7Y+067CxIOyCrOyKrC4NCiREZXNrID0gIiINCmZvcmVhY2ggKCRj
>> "%B64%" echo IGluIEAoW0Vudmlyb25tZW50XTo6R2V0Rm9sZGVyUGF0aChbRW52aXJvbm1lbnQrU3BlY2lhbEZv
>> "%B64%" echo bGRlcl06OkRlc2t0b3BEaXJlY3RvcnkpLA0KICAgICAgICAgICAgICAgICBbRW52aXJvbm1lbnRd
>> "%B64%" echo OjpHZXRGb2xkZXJQYXRoKFtFbnZpcm9ubWVudCtTcGVjaWFsRm9sZGVyXTo6RGVza3RvcCksDQog
>> "%B64%" echo ICAgICAgICAgICAgICAgIChKb2luLVBhdGggJGVudjpVU0VSUFJPRklMRSAiRGVza3RvcCIpLA0K
>> "%B64%" echo ICAgICAgICAgICAgICAgICAoSm9pbi1QYXRoICRlbnY6VVNFUlBST0ZJTEUgIuuwlO2DlSDtmZTr
>> "%B64%" echo qbQiKSwNCiAgICAgICAgICAgICAgICAgJGVudjpVU0VSUFJPRklMRSwgJGVudjpURU1QKSkgew0K
>> "%B64%" echo ICBpZiAoJGMgLWFuZCAoVGVzdC1QYXRoICRjKSkgeyAkRGVzayA9ICRjOyBicmVhayB9DQp9DQpp
>> "%B64%" echo ZiAoLW5vdCAkRGVzaykgeyAkRGVzayA9ICIuIiB9DQokTG9nUGF0aCA9IEpvaW4tUGF0aCAkRGVz
>> "%B64%" echo ayAi7Z6J7Iqk7ZWE65Oc7ZmV7J24X+qysOqzvC50eHQiDQokS2V5UGF0aCA9IEpvaW4tUGF0aCAk
>> "%B64%" echo RGVzayAi7Z6J7Iqk7ZWE65Oc7Je07IegX+u2meyXrOuEo+q4sC50eHQiDQokTGluZXMgPSBOZXct
>> "%B64%" echo T2JqZWN0IFN5c3RlbS5Db2xsZWN0aW9ucy5BcnJheUxpc3QNCg0KZnVuY3Rpb24gU2F5KFtzdHJp
>> "%B64%" echo bmddJG0sIFtzdHJpbmddJGNvbG9yID0gIkdyYXkiKSB7IFdyaXRlLUhvc3QgJG0gLUZvcmVncm91
>> "%B64%" echo bmRDb2xvciAkY29sb3I7IFt2b2lkXSRMaW5lcy5BZGQoJG0pIH0NCmZ1bmN0aW9uIE1hc2soW3N0
>> "%B64%" echo cmluZ10kdikgeyBpZiAoLW5vdCAkdikgeyByZXR1cm4gIijsl4bsnYwpIiB9IDsgaWYgKCR2Lkxl
>> "%B64%" echo bmd0aCAtbGUgMTIpIHsgcmV0dXJuICIqKioiIH0gOyByZXR1cm4gJHYuU3Vic3RyaW5nKDAsMTIp
>> "%B64%" echo ICsgIuKApigiICsgJHYuTGVuZ3RoICsgIuyekCkiIH0NCmZ1bmN0aW9uIERvbmUoW2ludF0kcmMp
>> "%B64%" echo IHsNCiAgIyDimqAg6riw66GdIOyggOyepSDsnpDssrTrpbwg6rCQ7Iu864ukIOKAlCDrsLHsi6DC
>> "%B64%" echo t+2BtOudvOyasOuTnCDrj5nquLDtmZTqsIAg67CU7YOV7ZmU66m0IOyTsOq4sOulvCDrp4nsnLzr
>> "%B64%" echo qbQsIOyLpO2MqCDsgqzsnKDrpbwNCiAgIyAgIOyVjOumrOugpOuNmCDsnbQg7ZWo7IiY6rCAIOyC
>> "%B64%" echo rOycoOulvCDrp5DtlZjquLDrj4Qg7KCE7JeQIOyjveqzoCDssL3snbQg6re464OlIOuLq+2ejOuL
>> "%B64%" echo pCjsoJXrs7ggU2F2ZUxvZyDqs4Tslb0g6rOE7Iq5KS4NCiAgdHJ5IHsgJExpbmVzIC1qb2luICJg
>> "%B64%" echo cmBuIiB8IFNldC1Db250ZW50IC1QYXRoICRMb2dQYXRoIC1FbmNvZGluZyBVVEY4IH0gY2F0Y2gg
>> "%B64%" echo ew0KICAgIFdyaXRlLUhvc3QgKCLquLDroZ0g7YyM7J287J2EIOyggOyepe2VmOyngCDrqrvtlojs
>> "%B64%" echo irXri4jri6Q6ICIgKyAkXy5FeGNlcHRpb24uTWVzc2FnZSkgLUZvcmVncm91bmRDb2xvciBZZWxs
>> "%B64%" echo b3cNCiAgfQ0KICBXcml0ZS1Ib3N0ICIiOyBXcml0ZS1Ib3N0ICgi6riw66GdOiAiICsgJExvZ1Bh
>> "%B64%" echo dGgpIC1Gb3JlZ3JvdW5kQ29sb3IgRGFya0dyYXkNCiAgUmVhZC1Ib3N0ICLsl5TthLDrpbwg64iE
>> "%B64%" echo 66W066m0IOuLq+2emeuLiOuLpCIgfCBPdXQtTnVsbA0KICBleGl0ICRyYw0KfQ0KZnVuY3Rpb24g
>> "%B64%" echo QjY0VXJsKFtieXRlW11dJGIpIHsgW0NvbnZlcnRdOjpUb0Jhc2U2NFN0cmluZygkYikuVHJpbUVu
>> "%B64%" echo ZCgnPScpLlJlcGxhY2UoJysnLCctJykuUmVwbGFjZSgnLycsJ18nKSB9DQoNCiMg4pqgICoq7ISc
>> "%B64%" echo 67KE6rCAIOutkOudvOqzoCDqsbDsoIjtlojripTsp4AqKuulvCDsnb3ripTri6Qo7KCV67O4ID0g
>> "%B64%" echo Z3Jva19wcm9iZS5wczEgV2ViKCkpLiDtjIzsm4zshbggNS4xIOqzvCA3IOydtCDsi6TtjKgNCiMg
>> "%B64%" echo ICDsnZHri7XsnYQg64uk66W06rKMIOuEmOqyqOyEnCwg7ZWc7Kq966eMIOydveycvOuptCDrgqjr
>> "%B64%" echo ipQg6rG0ICIoNDAwKSDsnpjrqrvrkJwg7JqU7LKtIiDqsJnsnYAg6ruN642w6riw67+Q7J206rOg
>> "%B64%" echo IOyEnOuyhOqwgA0KIyAgIOuztOuCuCDsgqzsnKAoaW52YWxpZF9ncmFudCDCtyDssKjri6gg67O4
>> "%B64%" echo 66y4KeqwgCDthrXsp7jroZwg7IKs65287KeE64ukID0g7J20IO2MkOygleq4sOydmCDsobTsnqwg
>> "%B64%" echo 7J207Jyg6rCAIOyCrOudvOynhOuLpC4NCmZ1bmN0aW9uIEVyclRleHQoJGUpIHsNCiAgJHQgPSAi
>> "%B64%" echo JCgkZS5FeGNlcHRpb24uTWVzc2FnZSkiDQogIHRyeSB7IGlmICgkZS5FcnJvckRldGFpbHMgLWFu
>> "%B64%" echo ZCAkZS5FcnJvckRldGFpbHMuTWVzc2FnZSkgeyByZXR1cm4gW3N0cmluZ10kZS5FcnJvckRldGFp
>> "%B64%" echo bHMuTWVzc2FnZSB9IH0gY2F0Y2gge30NCiAgJHJlc3AgPSAkbnVsbA0KICB0cnkgeyAkcmVzcCA9
>> "%B64%" echo ICRlLkV4Y2VwdGlvbi5SZXNwb25zZSB9IGNhdGNoIHt9DQogIGlmICgkcmVzcCkgew0KICAgIHRy
>> "%B64%" echo eSB7DQogICAgICAkc3IgPSBOZXctT2JqZWN0IElPLlN0cmVhbVJlYWRlcigkcmVzcC5HZXRSZXNw
>> "%B64%" echo b25zZVN0cmVhbSgpKQ0KICAgICAgJGIgPSAkc3IuUmVhZFRvRW5kKCk7ICRzci5DbG9zZSgpDQog
>> "%B64%" echo ICAgICBpZiAoJGIpIHsgcmV0dXJuICgiSFRUUCAiICsgW2ludF0kcmVzcC5TdGF0dXNDb2RlICsg
>> "%B64%" echo IiDCtyAiICsgJGIpIH0NCiAgICB9IGNhdGNoIHt9DQogICAgdHJ5IHsgcmV0dXJuICgiSFRUUCAi
>> "%B64%" echo ICsgW2ludF0kcmVzcC5TdGF0dXNDb2RlICsgIiDCtyAiICsgJHQpIH0gY2F0Y2gge30NCiAgfQ0K
>> "%B64%" echo ICByZXR1cm4gJHQNCn0NCg0KU2F5ICIiDQpTYXkgIiAg4pSM4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSQIiAiQ3lhbiINClNheSAiICDilIIgIOuFuOuupO2KuCDigJQg
>> "%B64%" echo 7Z6J7Iqk7ZWE65OcIOyekOqyqSDtmZXsnbggKDLtjJApICAgICAgICAg4pSCIiAiQ3lhbiINClNh
>> "%B64%" echo eSAiICDilIIgIOu4jOudvOyasOyggOuhnCDtlZwg67KIIO2XiOyaqe2VmOuptCDrgZ3rgqnri4jr
>> "%B64%" echo i6QgICAgICDilIIiICJDeWFuIg0KU2F5ICIgIOKUgiAg7YGs66CI65Sn7J2AIOyTsOyngCDslYrs
>> "%B64%" echo irXri4jri6QgICAgICAgICAgICAgICAg4pSCIiAiQ3lhbiINClNheSAiICDilJTilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilJgiICJDeWFuIg0KU2F5ICIiDQpTYXkgKCLs
>> "%B64%" echo i6Ttlokg7Iuc6rCBIDogIiArIChHZXQtRGF0ZSAtRm9ybWF0ICJ5eXl5LU1NLWRkIEhIOm1tOnNz
>> "%B64%" echo IikpDQpTYXkgIiINCg0KIyDilIDilIAg4pGgIO2UhOuhnOq3uOueqCDrk7HroZ0g4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSADQp0cnkgew0KICAkcmVnID0g
>> "%B64%" echo SW52b2tlLVJlc3RNZXRob2QgLVVyaSAiJEJBU0Uvb2F1dGgyL3JlZ2lzdGVyIiAtTWV0aG9kIFBv
>> "%B64%" echo c3QgLVRpbWVvdXRTZWMgNDAgYA0KICAgIC1IZWFkZXJzIEB7ICJVc2VyLUFnZW50IiA9ICRVQSB9
>> "%B64%" echo IC1Db250ZW50VHlwZSAiYXBwbGljYXRpb24vanNvbiIgLUJvZHkgKEB7DQogICAgICBjbGllbnRf
>> "%B64%" echo bmFtZSA9ICJub211dGUtZWRpdG9yIjsgcmVkaXJlY3RfdXJpcyA9IEAoJFJFRElSKQ0KICAgICAg
>> "%B64%" echo Z3JhbnRfdHlwZXMgPSBAKCJhdXRob3JpemF0aW9uX2NvZGUiLCJyZWZyZXNoX3Rva2VuIik7IHJl
>> "%B64%" echo c3BvbnNlX3R5cGVzID0gQCgiY29kZSIpDQogICAgICB0b2tlbl9lbmRwb2ludF9hdXRoX21ldGhv
>> "%B64%" echo ZCA9ICJub25lIjsgc2NvcGUgPSAkU0NPUEUgfSB8IENvbnZlcnRUby1Kc29uIC1Db21wcmVzcykN
>> "%B64%" echo Cn0gY2F0Y2ggew0KICBTYXkgIuKdjCDtlITroZzqt7jrnqgg65Ox66GdIOyLpO2MqC4iICJSZWQi
>> "%B64%" echo OyBTYXkgKCIgICDsgqzsnKA6ICIgKyAoRXJyVGV4dCAkXykpICJSZWQiOyBEb25lIDENCn0NCiRj
>> "%B64%" echo bGllbnRJZCA9IFtzdHJpbmddJHJlZy5jbGllbnRfaWQNClNheSAoIuKRoCDtlITroZzqt7jrnqgg
>> "%B64%" echo 65Ox66GdIOKckyAg67KI7Zi4ICIgKyAkY2xpZW50SWQpDQoNCiMg4pSA4pSAIOKRoSDsirnsnbgg
>> "%B64%" echo 7LC9IOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgA0KJHJuZyA9
>> "%B64%" echo IFtTZWN1cml0eS5DcnlwdG9ncmFwaHkuUmFuZG9tTnVtYmVyR2VuZXJhdG9yXTo6Q3JlYXRlKCkN
>> "%B64%" echo CiR2YiA9IE5ldy1PYmplY3QgYnl0ZVtdIDY0OyAkcm5nLkdldEJ5dGVzKCR2Yik7ICR2ZXJpZmll
>> "%B64%" echo ciA9IEI2NFVybCAkdmINCiRzaGEgPSBbU2VjdXJpdHkuQ3J5cHRvZ3JhcGh5LlNIQTI1Nl06OkNy
>> "%B64%" echo ZWF0ZSgpDQokY2hhbGxlbmdlID0gQjY0VXJsICRzaGEuQ29tcHV0ZUhhc2goW1RleHQuRW5jb2Rp
>> "%B64%" echo bmddOjpBU0NJSS5HZXRCeXRlcygkdmVyaWZpZXIpKQ0KJHNiID0gTmV3LU9iamVjdCBieXRlW10g
>> "%B64%" echo MTY7ICRybmcuR2V0Qnl0ZXMoJHNiKTsgJHN0YXRlID0gQjY0VXJsICRzYg0KDQokYXV0aFVybCA9
>> "%B64%" echo ICIkQkFTRS9vYXV0aDIvYXV0aG9yaXplP3Jlc3BvbnNlX3R5cGU9Y29kZSZjbGllbnRfaWQ9JGNs
>> "%B64%" echo aWVudElkIiArDQogICAgICAgICAgICImcmVkaXJlY3RfdXJpPSIgKyBbVXJpXTo6RXNjYXBlRGF0
>> "%B64%" echo YVN0cmluZygkUkVESVIpICsNCiAgICAgICAgICAgIiZzY29wZT0iICsgW1VyaV06OkVzY2FwZURh
>> "%B64%" echo dGFTdHJpbmcoJFNDT1BFKSArDQogICAgICAgICAgICImc3RhdGU9JHN0YXRlJmNvZGVfY2hhbGxl
>> "%B64%" echo bmdlPSRjaGFsbGVuZ2UmY29kZV9jaGFsbGVuZ2VfbWV0aG9kPVMyNTYiDQoNCiRsaXN0ZW5lciA9
>> "%B64%" echo IE5ldy1PYmplY3QgU3lzdGVtLk5ldC5Tb2NrZXRzLlRjcExpc3RlbmVyKFtOZXQuSVBBZGRyZXNz
>> "%B64%" echo XTo6TG9vcGJhY2ssICRQT1JUKQ0KdHJ5IHsgJGxpc3RlbmVyLlN0YXJ0KCkgfSBjYXRjaCB7DQog
>> "%B64%" echo IFNheSAoIuKdjCDrgrQgUEMg7LC96rWsKCIgKyAkUE9SVCArICLrsogp66W8IOuquyDsl7Tsl4js
>> "%B64%" echo irXri4jri6Q6ICIgKyAkXy5FeGNlcHRpb24uTWVzc2FnZSkgIlJlZCINCiAgU2F5ICIgICDri6Tr
>> "%B64%" echo pbgg7ZSE66Gc6re4656o7J20IOq3uCDrsojtmLjrpbwg7JOw6rOgIOyeiOydhCDsiJgg7J6I7Iq1
>> "%B64%" echo 64uI64ukLiDsnqDsi5wg65KkIOuLpOyLnCDsi6TtlontlbQg7KO87IS47JqULiINCiAgRG9uZSAx
>> "%B64%" echo DQp9DQoNClNheSAiIg0KU2F5ICLikaEg7Iq57J24IOywveydhCDsl73ri4jri6QuIOu4jOudvOya
>> "%B64%" echo sOyggOyXkOyEnCDtl4jsmqnsnYQg64iE66W07IS47JqULiINClNheSAiIg0KU2F5ICgiICAgIiAr
>> "%B64%" echo ICRhdXRoVXJsKSAiRGFya0dyYXkiDQpTYXkgIiINCnRyeSB7IFN0YXJ0LVByb2Nlc3MgJGF1dGhV
>> "%B64%" echo cmwgfCBPdXQtTnVsbCB9IGNhdGNoIHsgU2F5ICIgICAo67iM65287Jqw7KCA6rCAIOyViCDsl7Tr
>> "%B64%" echo pqzrqbQg7JyEIOyjvOyGjOulvCDsp4HsoJEg67aZ7Jes64Sj7Jy87IS47JqUKSIgIlllbGxvdyIg
>> "%B64%" echo fQ0KDQokY29kZSA9ICRudWxsOyAkZGVhZGxpbmUgPSAoR2V0LURhdGUpLkFkZE1pbnV0ZXMoMTAp
>> "%B64%" echo DQojIOKaoCDsnbQg66Oo7ZSEIOyViOydgCAqKuu4jOudvOyasOyggOqwgCDrp4jsnYzrjIDroZwg
>> "%B64%" echo 64GK7J2EIOyImCDsnojripQg6rWs6rCEKirsnbTri6Qo66+466asIOyXtOyWtOuztOuKlCDsl7Dq
>> "%B64%" echo srDCt+uovOyggCDri6vquLApLg0KIyAgIOqwkOyLuOyngCDslYrsnLzrqbQg7KCV7ZmV7Z6IIOyK
>> "%B64%" echo ueyduO2VmOuKlCDqt7gg7Iic6rCE7JeQIOywveydtCDsgqzsnKAg7JeG7J20IOuLq+2eiOqzoCDq
>> "%B64%" echo uLDroZ3rj4Qg7JWIIOuCqOuKlOuLpC4NCiMgICDimqAg64yA6riwIDEw67aEIOKAlCAy64uo6rOE
>> "%B64%" echo IOyduOymncK366Gc6re47J247J20IOuBvOuptCA167aE7J2AIOu5oOuTr+2VmOuLpC4NCndoaWxl
>> "%B64%" echo ICgoR2V0LURhdGUpIC1sdCAkZGVhZGxpbmUgLWFuZCAtbm90ICRjb2RlKSB7DQogdHJ5IHsNCiAg
>> "%B64%" echo aWYgKC1ub3QgJGxpc3RlbmVyLlBlbmRpbmcoKSkgeyBTdGFydC1TbGVlcCAtTWlsbGlzZWNvbmRz
>> "%B64%" echo IDMwMDsgY29udGludWUgfQ0KICAkY2wgPSAkbGlzdGVuZXIuQWNjZXB0VGNwQ2xpZW50KCk7ICRz
>> "%B64%" echo dCA9ICRjbC5HZXRTdHJlYW0oKQ0KICAkYnVmID0gTmV3LU9iamVjdCBieXRlW10gODE5MjsgJG4g
>> "%B64%" echo PSAkc3QuUmVhZCgkYnVmLCAwLCAkYnVmLkxlbmd0aCkNCiAgJHJlcSA9IFtUZXh0LkVuY29kaW5n
>> "%B64%" echo XTo6QVNDSUkuR2V0U3RyaW5nKCRidWYsIDAsICRuKQ0KICAkZmlyc3QgPSAoJHJlcSAtc3BsaXQg
>> "%B64%" echo ImByYG4iKVswXQ0KICBpZiAoJGZpcnN0IC1tYXRjaCAnR0VUXHMrKFxTKyknKSB7DQogICAgJHEg
>> "%B64%" echo PSAkTWF0Y2hlc1sxXQ0KICAgIGlmICgkcSAtbWF0Y2ggJ1s/Jl1jb2RlPShbXiZcc10rKScpIHsg
>> "%B64%" echo JGNvZGUgPSBbVXJpXTo6VW5lc2NhcGVEYXRhU3RyaW5nKCRNYXRjaGVzWzFdKSB9DQogICAgaWYg
>> "%B64%" echo KCRxIC1tYXRjaCAnWz8mXWVycm9yPShbXiZcc10rKScpIHsNCiAgICAgIFNheSAoIuKdjCDsirns
>> "%B64%" echo nbjsnbQg6rGw67aA65CQ7Iq164uI64ukOiAiICsgW1VyaV06OlVuZXNjYXBlRGF0YVN0cmluZygk
>> "%B64%" echo TWF0Y2hlc1sxXSkpICJSZWQiDQogICAgICBTYXkgIiAgIOqwmeydgCDqs4TsoJXsnLzroZwg64uk
>> "%B64%" echo 7IucIOyLpO2Wie2VmOqxsOuCmCwg67iM65287Jqw7KCA7JeQ7IScIO2eieyKpO2VhOuTnOyXkCDr
>> "%B64%" echo oZzqt7jsnbjtlZwg65KkIOuLpOyLnCDtlbQg67O07IS47JqULiINCiAgICB9DQogICAgaWYgKCRx
>> "%B64%" echo IC1tYXRjaCAnWz8mXXN0YXRlPShbXiZcc10rKScpIHsNCiAgICAgIGlmIChbVXJpXTo6VW5lc2Nh
>> "%B64%" echo cGVEYXRhU3RyaW5nKCRNYXRjaGVzWzFdKSAtbmUgJHN0YXRlKSB7DQogICAgICAgIFNheSAi4p2M
>> "%B64%" echo IOydkeuLteydmCDtkZzsi53snbQg7JWIIOunnuyKteuLiOuLpCjspJHqsITsl5DshJwg6rCA66Gc
>> "%B64%" echo 7LGE7JiA7J2EIOyImCDsnojsirXri4jri6QpLiIgIlJlZCI7ICRjb2RlID0gJG51bGwNCiAgICAg
>> "%B64%" echo IH0NCiAgICB9DQogIH0NCiAgJGh0bWwgPSAiPGh0bWw+PGhlYWQ+PG1ldGEgY2hhcnNldD0ndXRm
>> "%B64%" echo LTgnPjwvaGVhZD48Ym9keSBzdHlsZT0nZm9udC1mYW1pbHk6c2Fucy1zZXJpZjtiYWNrZ3JvdW5k
>> "%B64%" echo OiMxMTE7Y29sb3I6I2VlZTtwYWRkaW5nOjQwcHgnPjxoMj4iICsNCiAgICAgICAgICAkKGlmICgk
>> "%B64%" echo Y29kZSkgeyAi7Iq57J24IOyZhOujjCIgfSBlbHNlIHsgIuyKueyduCDsi6TtjKgiIH0pICsNCiAg
>> "%B64%" echo ICAgICAgICAiPC9oMj48cD7snbQg7LC97J2EIOuLq+qzoCDqsoDsnYAg7LC97Jy866GcIOuPjOyV
>> "%B64%" echo hOqwgOyEuOyalC48L3A+PC9ib2R5PjwvaHRtbD4iDQogICRib2R5ID0gW1RleHQuRW5jb2Rpbmdd
>> "%B64%" echo OjpVVEY4LkdldEJ5dGVzKCRodG1sKQ0KICAkaGVhZCA9IFtUZXh0LkVuY29kaW5nXTo6QVNDSUku
>> "%B64%" echo R2V0Qnl0ZXMoIkhUVFAvMS4xIDIwMCBPS2ByYG5Db250ZW50LVR5cGU6IHRleHQvaHRtbDsgY2hh
>> "%B64%" echo cnNldD11dGYtOGByYG5Db250ZW50LUxlbmd0aDogJCgkYm9keS5MZW5ndGgpYHJgbkNvbm5lY3Rp
>> "%B64%" echo b246IGNsb3NlYHJgbmByYG4iKQ0KICAkc3QuV3JpdGUoJGhlYWQsIDAsICRoZWFkLkxlbmd0aCk7
>> "%B64%" echo ICRzdC5Xcml0ZSgkYm9keSwgMCwgJGJvZHkuTGVuZ3RoKTsgJHN0LkZsdXNoKCkNCiAgJGNsLkNs
>> "%B64%" echo b3NlKCkNCiB9IGNhdGNoIHsgU3RhcnQtU2xlZXAgLU1pbGxpc2Vjb25kcyAyMDAgfSAgICMg64GK
>> "%B64%" echo 6ri0IOyXsOqysCDtlZjrgpjroZwg7YyQ7KCV6riw66W8IOyjveydtOyngCDslYrripTri6Qo64uk
>> "%B64%" echo 7J2MIOyXsOqysOydhCDquLDri6TrprDri6QpDQp9DQp0cnkgeyAkbGlzdGVuZXIuU3RvcCgpIH0g
>> "%B64%" echo Y2F0Y2gge30NCg0KaWYgKC1ub3QgJGNvZGUpIHsgU2F5ICIiOyBTYXkgIuKdjCDsi5zqsIQg7JWI
>> "%B64%" echo 7JeQIOyKueyduOydtCDslYgg65CQ7Iq164uI64ukLiDri6Tsi5wg7Iuk7ZaJ7ZW0IOyjvOyEuOya
>> "%B64%" echo lC4iICJSZWQiOyBEb25lIDEgfQ0KU2F5ICIiDQpTYXkgIiAgIOKchSDsirnsnbgg7JmE66OMIiAi
>> "%B64%" echo R3JlZW4iDQoNCiMg4pSA4pSAIOKRoiDsl7Tsh6Ag6rWQ7ZmYIOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgA0KJGZvcm0gPSAiZ3JhbnRfdHlwZT1hdXRob3JpemF0aW9uX2NvZGUmY29kZT0iICsg
>> "%B64%" echo W1VyaV06OkVzY2FwZURhdGFTdHJpbmcoJGNvZGUpICsNCiAgICAgICAgIiZyZWRpcmVjdF91cmk9
>> "%B64%" echo IiArIFtVcmldOjpFc2NhcGVEYXRhU3RyaW5nKCRSRURJUikgKw0KICAgICAgICAiJmNsaWVudF9p
>> "%B64%" echo ZD0iICsgW1VyaV06OkVzY2FwZURhdGFTdHJpbmcoJGNsaWVudElkKSArDQogICAgICAgICImY29k
>> "%B64%" echo ZV92ZXJpZmllcj0iICsgW1VyaV06OkVzY2FwZURhdGFTdHJpbmcoJHZlcmlmaWVyKQ0KdHJ5IHsN
>> "%B64%" echo CiAgJHRvayA9IEludm9rZS1SZXN0TWV0aG9kIC1VcmkgIiRCQVNFL29hdXRoMi90b2tlbiIgLU1l
>> "%B64%" echo dGhvZCBQb3N0IC1UaW1lb3V0U2VjIDQwIGANCiAgICAtSGVhZGVycyBAeyAiVXNlci1BZ2VudCIg
>> "%B64%" echo PSAkVUEgfSAtQ29udGVudFR5cGUgImFwcGxpY2F0aW9uL3gtd3d3LWZvcm0tdXJsZW5jb2RlZCIg
>> "%B64%" echo LUJvZHkgJGZvcm0NCn0gY2F0Y2ggew0KICBTYXkgIuKdjCDsl7Tsh6Ag6rWQ7ZmYIOyLpO2MqC4i
>> "%B64%" echo ICJSZWQiOyBTYXkgKCIgICDsgqzsnKA6ICIgKyAoRXJyVGV4dCAkXykpICJSZWQiOyBEb25lIDEN
>> "%B64%" echo Cn0NCiRhY2Nlc3MgPSBbc3RyaW5nXSR0b2suYWNjZXNzX3Rva2VuDQokcmVmcmVzaCA9IFtzdHJp
>> "%B64%" echo bmddJHRvay5yZWZyZXNoX3Rva2VuDQpTYXkgIiINClNheSAi4pGiIOyXtOyHoCDrsJvsnYwg4pyT
>> "%B64%" echo Ig0KU2F5ICgiICAg7KCR7IaNIOyXtOyHoCA6ICIgKyAoTWFzayAkYWNjZXNzKSkNClNheSAoIiAg
>> "%B64%" echo IOqwseyLoCDsl7Tsh6AgOiAiICsgKE1hc2sgJHJlZnJlc2gpKQ0KaWYgKCR0b2suZXhwaXJlc19p
>> "%B64%" echo bikgeyBTYXkgKCIgICDsoJHsho0g7Je07IegIOyImOuqhSA6ICIgKyAkdG9rLmV4cGlyZXNfaW4g
>> "%B64%" echo KyAi7LSIIikgfQ0KDQppZiAoLW5vdCAkcmVmcmVzaCkgew0KICBTYXkgIiINCiAgU2F5ICLinYwg
>> "%B64%" echo 6rCx7IugIOyXtOyHoOqwgCDsnZHri7Xsl5Ag7JeG7Iq164uI64ukIOKAlCDsnbQg7KSE7J2EIOq3
>> "%B64%" echo uOuMgOuhnCDslYzroKQg7KO87IS47JqULiIgIlJlZCI7IERvbmUgMQ0KfQ0KDQoNCiMg4pSA4pSA
>> "%B64%" echo IOKRoyAqKuu2meyXrOuEo+q4sCDsoITsl5Ag7Jes6riw7IScIOymneuqhe2VnOuLpCoqIOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgA0KIyDimqAg7JmcIOydtCDri6jqs4TqsIAg7J6I64KYKDI2MDgxMiDsi6Tsgqzqs6ApID0g
>> "%B64%" echo Me2MkOycvOuhnCDrsJvsnYAg7Je07Ieg64qUIOyekOqyqcK37J6U7JWh7J20IOuLpCDthrXqs7zt
>> "%B64%" echo lZjripTrjbANCiMgICAqKuuqqOuNuCDrqqnroZ3sl5Ag7Iuc64yE7Iqk6rCAIOyXhuyXiOuLpC4q
>> "%B64%" echo KiDqt7jqsbgg6rmD7ZeI67iM7JeQIOuEo+qzoCDrn6zrhIjrpbwg64+M66awIOuSpOyXkOyVvCDs
>> "%B64%" echo lYzslZjri6QgPQ0KIyAgIOyatOyYgeyekOqwgCDtl5vsiJjqs6Drpbwg7ZaI64ukLiDqt7jrnpjs
>> "%B64%" echo hJwgMu2MkOydgCAqKuyXtOyHoOulvCDso7zquLAg7KCE7JeQKiog7LC96rWs7JeQIOyngeygkSDr
>> "%B64%" echo rLzslrTrs7jri6QuDQpTYXkgIiINClNheSAi4pGjIOydtCDsl7Tsh6DroZwg7Iuc64yE7Iqk6rCA
>> "%B64%" echo IOyXtOumrOuKlOyngCDsp4DquIgg7ZmV7J247ZWp64uI64ukLiINCg0KJGhkciA9IEB7ICJBdXRo
>> "%B64%" echo b3JpemF0aW9uIiA9ICJCZWFyZXIgJGFjY2VzcyI7ICJVc2VyLUFnZW50IiA9ICRVQQ0KICAgICAg
>> "%B64%" echo ICAgICJBY2NlcHQiID0gImFwcGxpY2F0aW9uL2pzb24sIHRleHQvZXZlbnQtc3RyZWFtIjsgIk1D
>> "%B64%" echo UC1Qcm90b2NvbC1WZXJzaW9uIiA9ICIyMDI1LTA2LTE4IiB9DQokc2NyaXB0OnNpZCA9ICRudWxs
>> "%B64%" echo DQpmdW5jdGlvbiBScGMoW3N0cmluZ10kbWV0aG9kLCAkcHJtKSB7DQogICRib2R5ID0gKEB7IGpz
>> "%B64%" echo b25ycGMgPSAiMi4wIjsgaWQgPSAoR2V0LVJhbmRvbSAtTWF4aW11bSA5OTk5OSk7IG1ldGhvZCA9
>> "%B64%" echo ICRtZXRob2Q7IHBhcmFtcyA9ICRwcm0gfSB8IENvbnZlcnRUby1Kc29uIC1EZXB0aCAxMiAtQ29t
>> "%B64%" echo cHJlc3MpDQogICRoID0gJGhkci5DbG9uZSgpOyBpZiAoJHNjcmlwdDpzaWQpIHsgJGhbIk1jcC1T
>> "%B64%" echo ZXNzaW9uLUlkIl0gPSAkc2NyaXB0OnNpZCB9DQogICRyID0gSW52b2tlLVdlYlJlcXVlc3QgLVVy
>> "%B64%" echo aSAiJEJBU0UvbWNwIiAtTWV0aG9kIFBvc3QgLUhlYWRlcnMgJGggLUNvbnRlbnRUeXBlICJhcHBs
>> "%B64%" echo aWNhdGlvbi9qc29uIiAtQm9keSAkYm9keSAtVGltZW91dFNlYyA2MCAtVXNlQmFzaWNQYXJzaW5n
>> "%B64%" echo DQogIGlmICgkci5IZWFkZXJzWyJNY3AtU2Vzc2lvbi1JZCJdKSB7ICRzY3JpcHQ6c2lkID0gW3N0
>> "%B64%" echo cmluZ10kci5IZWFkZXJzWyJNY3AtU2Vzc2lvbi1JZCJdIH0NCiAgJHQgPSBbc3RyaW5nXSRyLkNv
>> "%B64%" echo bnRlbnQNCiAgaWYgKCR0IC1tYXRjaCAnKD9tKV5kYXRhOlxzKihcey4qKSQnKSB7ICR0ID0gJE1h
>> "%B64%" echo dGNoZXNbMV0gfSAgICMg7J2067Kk7Yq4IOyKpO2KuOumvOydtOuptCDslYzrp7nsnbTrp4wNCiAg
>> "%B64%" echo cmV0dXJuICgkdCB8IENvbnZlcnRGcm9tLUpzb24pDQp9DQpmdW5jdGlvbiBUb29sKFtzdHJpbmdd
>> "%B64%" echo JG5hbWUsICRhcmdzMikgew0KICAkcmVzID0gUnBjICJ0b29scy9jYWxsIiBAeyBuYW1lID0gJG5h
>> "%B64%" echo bWU7IGFyZ3VtZW50cyA9ICRhcmdzMiB9DQogIGlmICgkcmVzLmVycm9yKSB7IHJldHVybiAiRVJS
>> "%B64%" echo ICIgKyAoJHJlcy5lcnJvciB8IENvbnZlcnRUby1Kc29uIC1Db21wcmVzcykgfQ0KICBmb3JlYWNo
>> "%B64%" echo ICgkYyBpbiAkcmVzLnJlc3VsdC5jb250ZW50KSB7IGlmICgkYy50eXBlIC1lcSAidGV4dCIpIHsg
>> "%B64%" echo cmV0dXJuIFtzdHJpbmddJGMudGV4dCB9IH0NCiAgcmV0dXJuICgkcmVzLnJlc3VsdCB8IENvbnZl
>> "%B64%" echo cnRUby1Kc29uIC1EZXB0aCA4IC1Db21wcmVzcykNCn0NCg0KJG9rID0gJGZhbHNlDQp0cnkgew0K
>> "%B64%" echo ICBScGMgImluaXRpYWxpemUiIEB7IHByb3RvY29sVmVyc2lvbiA9ICIyMDI1LTA2LTE4IjsgY2Fw
>> "%B64%" echo YWJpbGl0aWVzID0gQHt9DQogICAgICAgICAgICAgICAgICAgICAgY2xpZW50SW5mbyA9IEB7IG5h
>> "%B64%" echo bWUgPSAibm9tdXRlLXByb2JlIjsgdmVyc2lvbiA9ICIyLjAiIH0gfSB8IE91dC1OdWxsDQogIHRy
>> "%B64%" echo eSB7IFJwYyAibm90aWZpY2F0aW9ucy9pbml0aWFsaXplZCIgQHt9IHwgT3V0LU51bGwgfSBjYXRj
>> "%B64%" echo aCB7fQ0KICAkYmFsID0gVG9vbCAiYmFsYW5jZSIgQHt9DQogIFNheSAoIiAgIOyelOyVoSA6ICIg
>> "%B64%" echo KyAkYmFsKQ0KICAkY29zdCA9IFRvb2wgImdlbmVyYXRlX3ZpZGVvIiBAeyBwYXJhbXMgPSBAeyBt
>> "%B64%" echo b2RlbCA9ICJzZWVkYW5jZV8yXzUiOyBwcm9tcHQgPSAiY29zdCBjaGVjayINCiAgICAgIGR1cmF0
>> "%B64%" echo aW9uID0gMzA7IHJlc29sdXRpb24gPSAiNzIwcCI7IG1vZGUgPSAib21uaV9yZWZlcmVuY2UiOyBh
>> "%B64%" echo c3BlY3RfcmF0aW8gPSAiOToxNiINCiAgICAgIGdlbmVyYXRlX2F1ZGlvID0gJHRydWU7IHVzZV91
>> "%B64%" echo bmxpbSA9ICRmYWxzZTsgZ2V0X2Nvc3QgPSAkdHJ1ZSB9IH0NCiAgU2F5ICgiICAg7Iuc64yE7Iqk
>> "%B64%" echo IOqyrOyggSA6ICIgKyAkY29zdCkNCiAgaWYgKCRjb3N0IC1tYXRjaCAnImNyZWRpdHMiJyAtb3Ig
>> "%B64%" echo JGNvc3QgLW1hdGNoICdcZCtccypjcmVkaXQnKSB7ICRvayA9ICR0cnVlIH0NCn0gY2F0Y2ggew0K
>> "%B64%" echo ICBTYXkgKCIgICDimqAg7ZmV7J24IO2YuOy2nOydtCDsi6TtjKjtlojsirXri4jri6Q6ICIgKyAo
>> "%B64%" echo RXJyVGV4dCAkXykpICJZZWxsb3ciDQp9DQoNCmlmICgtbm90ICRvaykgew0KICBTYXkgIiINCiAg
>> "%B64%" echo U2F5ICIgIOKUjOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUkCIgIlJl
>> "%B64%" echo ZCINCiAgU2F5ICIgIOKUgiAg4p2MIOydtCDsl7Tsh6DroZzripQg7Iuc64yE7Iqk6rCAIOyViCDs
>> "%B64%" echo l7Trpr3ri4jri6QgICAgICDilIIiICJSZWQiDQogIFNheSAiICDilJTilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilJgiICJSZWQiDQogIFNheSAiIg0KICBTYXkgIiAg4pqg
>> "%B64%" echo ICoq6rmD7ZeI67iM7JeQIOu2meyXrOuEo+yngCDrp4jshLjsmpQuKiog64Sj7Ja064+EIOyYgeyD
>> "%B64%" echo geydtCDslYgg66eM65Ok7Ja07KeR64uI64ukLiIgIlllbGxvdyINCiAgU2F5ICIgIOychCDrkZAg
>> "%B64%" echo 7KSEKOyelOyVocK37Iuc64yE7IqkIOqyrOyggSnsnYQg6re464yA66GcIOuzteyCrO2VtOyEnCDs
>> "%B64%" echo lYzroKQg7KO87IS47JqULiDqt7gg6rCS7Jy866GcIOuLpOydjCDsiJjrpbwg7KCV7ZWp64uI64uk
>> "%B64%" echo LiINCiAgU2F5ICIiDQogIFNldC1Db250ZW50IC1QYXRoICRLZXlQYXRoIC1WYWx1ZSAiIiAtRW5j
>> "%B64%" echo b2RpbmcgQVNDSUkgLU5vTmV3bGluZQ0KICBEb25lIDENCn0NClNheSAiICAg4pyFIOyLnOuMhOyK
>> "%B64%" echo pCDsl7Trprwg7ZmV7J24IiAiR3JlZW4iDQoNCiMg4pqgIOqwkuunjCDtlZwg7KSE66GcIOyTtOuL
>> "%B64%" echo pCDigJQg7YGwIOuNqeyWtOumrOyXkOyEnCDriIjsnLzroZwg7J6Y652864K06rKMIO2VmOuptCDs
>> "%B64%" echo gqzqs6DqsIAg64Kc64ukLg0KIyAgIO2UhOuhnOq3uOueqCDrsojtmLjrj4Qg6rCZ7J20IO2VhOya
>> "%B64%" echo lO2VtOyEnCDtlZwg7KSE66GcIOustuuKlOuLpCjrtpnsl6zrhKPquLAgMe2ajCDsm5DsuZkpLg0K
>> "%B64%" echo U2V0LUNvbnRlbnQgLVBhdGggJEtleVBhdGggLVZhbHVlICgkY2xpZW50SWQgKyAiOiIgKyAkcmVm
>> "%B64%" echo cmVzaCkgLUVuY29kaW5nIEFTQ0lJIC1Ob05ld2xpbmUNCg0KU2F5ICIiDQpTYXkgIiAg4pSM4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSQIiAiR3JlZW4iDQpTYXkgIiAg
>> "%B64%" echo 4pSCICDrgZ3rgqzsirXri4jri6QuIOuRkCDqsbjsnYzrp4wg7ZWY66m0IOuQqeuLiOuLpCAgICAg
>> "%B64%" echo ICAg4pSCIiAiR3JlZW4iDQpTYXkgIiAg4pSU4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSYIiAiR3JlZW4iDQpTYXkgIiINClNheSAiICAxKSDrsJTtg5XtmZTrqbTsnZgg
>> "%B64%" echo 44CM7Z6J7Iqk7ZWE65Oc7Je07IegX+u2meyXrOuEo+q4sC50eHTjgI0g66W8IOyXtOyWtCDslYjs
>> "%B64%" echo nZgg6rCS7J2EIOyghOu2gCDrs7XsgqwiDQpTYXkgIiINClNheSAiICAyKSDquYPtl4jruIwg66CI
>> "%B64%" echo 7Y+sIOKGkiBTZXR0aW5ncyDihpIgU2VjcmV0cyBhbmQgdmFyaWFibGVzIOKGkiBBY3Rpb25zIg0K
>> "%B64%" echo U2F5ICgiICAgICDihpIgIiArICRTRUNSRVRfTkFNRSArICIg66W8IOydtCDqsJLsnLzroZwg67CU
>> "%B64%" echo 6r646riwKFVwZGF0ZSBzZWNyZXQpIikNClNheSAiIg0KU2F5ICIgIOKaoCDrtpnsl6zrhKPsnYAg
>> "%B64%" echo 65Kk7JeQ64qUIOuwlO2Dle2ZlOuptOydmCDrkZAg7YyM7J287J2EIOyngOyasOyEuOyalC4iDQpT
>> "%B64%" echo YXkgIiAg4pqgIOydtCDqsJLsnYAg64Ko7JeQ6rKMIOyjvOyngCDrp4jshLjsmpQuIOqzhOyglSDt
>> "%B64%" echo gazroIjrlKfsnYQg7JO4IOyImCDsnojripQg6rCS7J6F64uI64ukLiINClNheSAiIg0KV3JpdGUt
>> "%B64%" echo SG9zdCAoIuyXtOyHoDogIiArICRLZXlQYXRoKSAtRm9yZWdyb3VuZENvbG9yIERhcmtHcmF5DQpE
>> "%B64%" echo b25lIDANCg==
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$t=[IO.File]::ReadAllText($env:B64); [IO.File]::WriteAllBytes((Join-Path $env:NM 'hf_probe.ps1'), [Convert]::FromBase64String(($t -replace '\s','')))"
if errorlevel 1 goto :fail
del "%B64%" >nul 2>&1

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%NM%\hf_probe.ps1"
set "RC=%ERRORLEVEL%"

del "%NM%\hf_probe.ps1" >nul 2>&1
rmdir "%NM%" >nul 2>&1
exit /b %RC%

:fail
echo.
echo   UNPACK FAILED - please send the lines above.
echo.
pause
exit /b 1
