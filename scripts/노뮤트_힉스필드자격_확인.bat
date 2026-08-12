@echo off
REM ===========================================================================
REM  nomute - Higgsfield entitlement probe : DOUBLE-CLICK, RUN ONCE
REM
REM  What it does: opens the Higgsfield device-code login in your browser, then
REM  exchanges your approval for a refresh token the CI runner can use, and
REM  verifies it with one free validate call. Spends NO credits.
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
>> "%B64%" echo lZDilZDilZDilZDilZANDQojIGhmX3Byb2JlLnBzMSAoMu2MkCkg4oCUIO2eieyKpO2VhOuTnCDs
>> "%B64%" echo npDqsqnsnYQg65+s64SI6rCAIOyTuCDsiJgg7J6I64qUICoq7Je07IegIO2VnCDspIQqKuuhnCDr
>> "%B64%" echo sJTqvrzri6QNDQojDQ0KIyDimqAgMe2MkCjquLDquLAg7L2U65OcIOuwqeyLnSnsnYAgKirrqqjr
>> "%B64%" echo jbjsnbQg7JWIIOyXtOuguOuLpCoqKDI2MDgxMiDsi6TsuKEgwrcg65+wIDMxNjI0NTY0MDAyKS4N
>> "%B64%" echo DQojICAg7J6Q6rKp64+EIOyelOyVoeuPhCDthrXqs7ztlojripTrjbAoMywwNjAg7YGs66CI65Sn
>> "%B64%" echo IMK3IHVsdHJhKSDrn6zrhIjqsIAg67O064qUIOuqqOuNuCDrqqnroZ3snbQgNuyiheu/kOydtOqz
>> "%B64%" echo oA0NCiMgICDqt7gg7JWI7JeQIOyLnOuMhOyKpOqwgCDsl4bsl4jri6QuIOqwmeydgCDqs4TsoJXs
>> "%B64%" echo nbjrjbAg7IKs656M7J20IOu2meyduCDsl7DqsrDsl5DshJzripQg7Iuc64yE7Iqk6rCAIOq3uOuM
>> "%B64%" echo gOuhnCDrqLntmJTri6QNDQojICAg4oaSIOywqOydtOuKlCAqKuyWtOuKkCDroZzqt7jsnbgg67Cp
>> "%B64%" echo 7Iud7Jy866GcIOuwm+ydgCDsnpDqsqnsnbTrg5AqKuyYgOuLpC4g7LC96rWs6rCAIOqzteqwnO2V
>> "%B64%" echo nCDslYjrgrTsl5Drj4Qg6riw6riwIOy9lOuTnCDrsKnsi53snYANDQojICAg64uk66W4IO2UhOuh
>> "%B64%" echo nOq3uOueqOyaqeycvOuhnCDsoIHtmIAg7J6I64ukLiDihpIgMu2MkOydgCAqKuu4jOudvOyasOyg
>> "%B64%" echo gCDrsKnsi50qKijsgqzrnozsnbQg67aZ7J24IOyXsOqysOqzvCDqsJnsnYAg6ri4KeycvOuhnCDq
>> "%B64%" echo sITri6QuDQ0KIw0NCiMg7Z2Q66aEKOyLpOy4oSDqt5zqsqkgwrcgMjYwODEyKSA9DQ0KIyAgIOKR
>> "%B64%" echo oCBQT1NUIC9vYXV0aDIvcmVnaXN0ZXIgIOKGkiDsmrDrpqwg7ZSE66Gc6re4656oIOuyiO2YuCjr
>> "%B64%" echo k7HroZ3sl5Ag7Iq57J24IOu2iOyalCDCtyDsponsi5wg67Cc6riJKQ0NCiMgICDikaEg67iM6528
>> "%B64%" echo 7Jqw7KCA66GcIC9vYXV0aDIvYXV0aG9yaXplIChQS0NFKSDihpIg66Gc6re47J24wrftl4jsmqkN
>> "%B64%" echo DQojICAg4pGiIOuCtCBQQyDqsIAg7J6g6rmQIOyXsCDssL3qtazroZwg7Iq57J24IOy9lOuTnOqw
>> "%B64%" echo gCDrj4zslYTsmKjri6QoMTI3LjAuMC4xKQ0NCiMgICDikaMgUE9TVCAvb2F1dGgyL3Rva2VuIOKG
>> "%B64%" echo kiDsoJHsho0g7Je07IegICsgKirqsLHsi6Ag7Je07IegKioNDQojDQ0KIyDsgrDstpw6ICDrsJTt
>> "%B64%" echo g5XtmZTrqbRc7Z6J7Iqk7ZWE65Oc7ZmV7J24X+qysOqzvC50eHQgICAo6riw66GdIMK3IOyXtOyH
>> "%B64%" echo oOuKlCDslZ4gMTLsnpDrp4wg64Ko6riw6rOgIOqwgOumsOuLpCkNDQojICAgICAgICDrsJTtg5Xt
>> "%B64%" echo mZTrqbRc7Z6J7Iqk7ZWE65Oc7Je07IegX+u2meyXrOuEo+q4sC50eHQgKOu2meyXrOuEo+ydhCDq
>> "%B64%" echo sJIgKirtlZwg7KSEKiogPSDtlITroZzqt7jrnqjrsojtmLg66rCx7Iug7Je07IegKQ0NCiMg64GE
>> "%B64%" echo 64qUIOuylTog7JWIIOuPjOumrOuptCDrgZ0uIOyEpOy5mOuQmOuKlCDqsoPrj4QsIOyekOuPmSDs
>> "%B64%" echo i6TtlonrkJjripQg6rKD64+EIOyXhuuLpC4g7YGs66CI65SnIDAuDQ0KIyDsg53shLEg7KCV67O4
>> "%B64%" echo OiBzY3JpcHRzL2hmX3Byb2JlLnBzMSDCtyDrsojrk6Qg7J6s7IOd7ISxID0gcHl0aG9uMyBzY3Jp
>> "%B64%" echo cHRzL2J1aWxkX2hmX3Byb2JlX2J1bmRsZS5weQ0NCiMg4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ
>> "%B64%" echo 4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ
>> "%B64%" echo 4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ
>> "%B64%" echo 4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ
>> "%B64%" echo 4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQDQ0KJEVycm9yQWN0aW9u
>> "%B64%" echo UHJlZmVyZW5jZSA9ICJTdG9wIg0NCnRyeSB7IFtOZXQuU2VydmljZVBvaW50TWFuYWdlcl06OlNl
>> "%B64%" echo Y3VyaXR5UHJvdG9jb2wgPSBbTmV0LlNlY3VyaXR5UHJvdG9jb2xUeXBlXTo6VGxzMTIgfSBjYXRj
>> "%B64%" echo aCB7fQ0NCnRyeSB7ICRPdXRwdXRFbmNvZGluZyA9IFtDb25zb2xlXTo6T3V0cHV0RW5jb2Rpbmcg
>> "%B64%" echo PSBbVGV4dC5FbmNvZGluZ106OlVURjggfSBjYXRjaCB7fQ0NCg0NCiRCQVNFID0gImh0dHBzOi8v
>> "%B64%" echo bWNwLmhpZ2dzZmllbGQuYWkiDQ0KJFBPUlQgPSA4NzY1DQ0KJFJFRElSID0gImh0dHA6Ly8xMjcu
>> "%B64%" echo MC4wLjE6JFBPUlQvY2FsbGJhY2siDQ0KJFNDT1BFID0gIm9wZW5pZCBlbWFpbCBvZmZsaW5lX2Fj
>> "%B64%" echo Y2VzcyINDQokU0VDUkVUX05BTUUgPSAiSElHR1NGSUVMRF9SRUZSRVNIX1RPS0VOIg0NCiMg4pqg
>> "%B64%" echo IOywveq1rCDslZ7ri6jsnbQg7YyM7J207I2swrfquLDrs7gg7ISc66qF7J2EIOunieuKlOuLpCgx
>> "%B64%" echo MDEwKSDihpIg67iM65287Jqw7KCAIOyEnOuqheydhCDri6jri6QoMjYwODEyIOyLpOy4oSkuDQ0K
>> "%B64%" echo JFVBID0gIk1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2Vi
>> "%B64%" echo S2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xNDEuMC4wLjAgU2FmYXJpLzUz
>> "%B64%" echo Ny4zNiINDQoNDQojIOKaoCDrsJTtg5XtmZTrqbQg6rK966Gc64qUIOu5iCDrrLjsnpDsl7TroZwg
>> "%B64%" echo 7JisIOyImCDsnojri6Qo7JuQ65Oc65287J2067iMIOuwseyXhSDsi6TsuKEpIOKGkiDtj7TrsLEg
>> "%B64%" echo 7IKs7IqsLg0NCiREZXNrID0gIiINDQpmb3JlYWNoICgkYyBpbiBAKFtFbnZpcm9ubWVudF06Okdl
>> "%B64%" echo dEZvbGRlclBhdGgoW0Vudmlyb25tZW50K1NwZWNpYWxGb2xkZXJdOjpEZXNrdG9wRGlyZWN0b3J5
>> "%B64%" echo KSwNDQogICAgICAgICAgICAgICAgIFtFbnZpcm9ubWVudF06OkdldEZvbGRlclBhdGgoW0Vudmly
>> "%B64%" echo b25tZW50K1NwZWNpYWxGb2xkZXJdOjpEZXNrdG9wKSwNDQogICAgICAgICAgICAgICAgIChKb2lu
>> "%B64%" echo LVBhdGggJGVudjpVU0VSUFJPRklMRSAiRGVza3RvcCIpLA0NCiAgICAgICAgICAgICAgICAgKEpv
>> "%B64%" echo aW4tUGF0aCAkZW52OlVTRVJQUk9GSUxFICLrsJTtg5Ug7ZmU66m0IiksDQ0KICAgICAgICAgICAg
>> "%B64%" echo ICAgICAkZW52OlVTRVJQUk9GSUxFLCAkZW52OlRFTVApKSB7DQ0KICBpZiAoJGMgLWFuZCAoVGVz
>> "%B64%" echo dC1QYXRoICRjKSkgeyAkRGVzayA9ICRjOyBicmVhayB9DQ0KfQ0NCmlmICgtbm90ICREZXNrKSB7
>> "%B64%" echo ICREZXNrID0gIi4iIH0NDQokTG9nUGF0aCA9IEpvaW4tUGF0aCAkRGVzayAi7Z6J7Iqk7ZWE65Oc
>> "%B64%" echo 7ZmV7J24X+qysOqzvC50eHQiDQ0KJEtleVBhdGggPSBKb2luLVBhdGggJERlc2sgIu2eieyKpO2V
>> "%B64%" echo hOuTnOyXtOyHoF/rtpnsl6zrhKPquLAudHh0Ig0NCiRMaW5lcyA9IE5ldy1PYmplY3QgU3lzdGVt
>> "%B64%" echo LkNvbGxlY3Rpb25zLkFycmF5TGlzdA0NCg0NCmZ1bmN0aW9uIFNheShbc3RyaW5nXSRtLCBbc3Ry
>> "%B64%" echo aW5nXSRjb2xvciA9ICJHcmF5IikgeyBXcml0ZS1Ib3N0ICRtIC1Gb3JlZ3JvdW5kQ29sb3IgJGNv
>> "%B64%" echo bG9yOyBbdm9pZF0kTGluZXMuQWRkKCRtKSB9DQ0KZnVuY3Rpb24gTWFzayhbc3RyaW5nXSR2KSB7
>> "%B64%" echo IGlmICgtbm90ICR2KSB7IHJldHVybiAiKOyXhuydjCkiIH0gOyBpZiAoJHYuTGVuZ3RoIC1sZSAx
>> "%B64%" echo MikgeyByZXR1cm4gIioqKiIgfSA7IHJldHVybiAkdi5TdWJzdHJpbmcoMCwxMikgKyAi4oCmKCIg
>> "%B64%" echo KyAkdi5MZW5ndGggKyAi7J6QKSIgfQ0NCmZ1bmN0aW9uIERvbmUoW2ludF0kcmMpIHsNDQogICRM
>> "%B64%" echo aW5lcyAtam9pbiAiYHJgbiIgfCBTZXQtQ29udGVudCAtUGF0aCAkTG9nUGF0aCAtRW5jb2Rpbmcg
>> "%B64%" echo VVRGOA0NCiAgV3JpdGUtSG9zdCAiIjsgV3JpdGUtSG9zdCAoIuq4sOuhnTogIiArICRMb2dQYXRo
>> "%B64%" echo KSAtRm9yZWdyb3VuZENvbG9yIERhcmtHcmF5DQ0KICBSZWFkLUhvc3QgIuyXlO2EsOulvCDriITr
>> "%B64%" echo pbTrqbQg64ur7Z6Z64uI64ukIiB8IE91dC1OdWxsDQ0KICBleGl0ICRyYw0NCn0NDQpmdW5jdGlv
>> "%B64%" echo biBCNjRVcmwoW2J5dGVbXV0kYikgeyBbQ29udmVydF06OlRvQmFzZTY0U3RyaW5nKCRiKS5Ucmlt
>> "%B64%" echo RW5kKCc9JykuUmVwbGFjZSgnKycsJy0nKS5SZXBsYWNlKCcvJywnXycpIH0NDQoNDQpTYXkgIiIN
>> "%B64%" echo DQpTYXkgIiAg4pSM4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSQIiAi
>> "%B64%" echo Q3lhbiINDQpTYXkgIiAg4pSCICDrhbjrrqTtirgg4oCUIO2eieyKpO2VhOuTnCDsnpDqsqkg7ZmV
>> "%B64%" echo 7J24ICgy7YyQKSAgICAgICAgIOKUgiIgIkN5YW4iDQ0KU2F5ICIgIOKUgiAg67iM65287Jqw7KCA
>> "%B64%" echo 66GcIO2VnCDrsogg7ZeI7Jqp7ZWY66m0IOuBneuCqeuLiOuLpCAgICAgIOKUgiIgIkN5YW4iDQ0K
>> "%B64%" echo U2F5ICIgIOKUgiAg7YGs66CI65Sn7J2AIOyTsOyngCDslYrsirXri4jri6QgICAgICAgICAgICAg
>> "%B64%" echo ICAg4pSCIiAiQ3lhbiINDQpTYXkgIiAg4pSU4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSYIiAiQ3lhbiINDQpTYXkgIiINDQpTYXkgKCLsi6Ttlokg7Iuc6rCBIDogIiAr
>> "%B64%" echo IChHZXQtRGF0ZSAtRm9ybWF0ICJ5eXl5LU1NLWRkIEhIOm1tOnNzIikpDQ0KU2F5ICIiDQ0KDQ0K
>> "%B64%" echo IyDilIDilIAg4pGgIO2UhOuhnOq3uOueqCDrk7HroZ0g4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSADQ0KdHJ5IHsNDQogICRyZWcgPSBJbnZva2UtUmVzdE1l
>> "%B64%" echo dGhvZCAtVXJpICIkQkFTRS9vYXV0aDIvcmVnaXN0ZXIiIC1NZXRob2QgUG9zdCAtVGltZW91dFNl
>> "%B64%" echo YyA0MCBgDQ0KICAgIC1IZWFkZXJzIEB7ICJVc2VyLUFnZW50IiA9ICRVQSB9IC1Db250ZW50VHlw
>> "%B64%" echo ZSAiYXBwbGljYXRpb24vanNvbiIgLUJvZHkgKEB7DQ0KICAgICAgY2xpZW50X25hbWUgPSAibm9t
>> "%B64%" echo dXRlLWVkaXRvciI7IHJlZGlyZWN0X3VyaXMgPSBAKCRSRURJUikNDQogICAgICBncmFudF90eXBl
>> "%B64%" echo cyA9IEAoImF1dGhvcml6YXRpb25fY29kZSIsInJlZnJlc2hfdG9rZW4iKTsgcmVzcG9uc2VfdHlw
>> "%B64%" echo ZXMgPSBAKCJjb2RlIikNDQogICAgICB0b2tlbl9lbmRwb2ludF9hdXRoX21ldGhvZCA9ICJub25l
>> "%B64%" echo Ijsgc2NvcGUgPSAkU0NPUEUgfSB8IENvbnZlcnRUby1Kc29uIC1Db21wcmVzcykNDQp9IGNhdGNo
>> "%B64%" echo IHsNDQogIFNheSAi4p2MIO2UhOuhnOq3uOueqCDrk7HroZ0g7Iuk7YyoLiIgIlJlZCI7IFNheSAo
>> "%B64%" echo IiAgIOyCrOycoDogIiArICRfLkV4Y2VwdGlvbi5NZXNzYWdlKSAiUmVkIjsgRG9uZSAxDQ0KfQ0N
>> "%B64%" echo CiRjbGllbnRJZCA9IFtzdHJpbmddJHJlZy5jbGllbnRfaWQNDQpTYXkgKCLikaAg7ZSE66Gc6re4
>> "%B64%" echo 656oIOuTseuhnSDinJMgIOuyiO2YuCAiICsgJGNsaWVudElkKQ0NCg0NCiMg4pSA4pSAIOKRoSDs
>> "%B64%" echo irnsnbgg7LC9IOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgA0N
>> "%B64%" echo CiRybmcgPSBbU2VjdXJpdHkuQ3J5cHRvZ3JhcGh5LlJhbmRvbU51bWJlckdlbmVyYXRvcl06OkNy
>> "%B64%" echo ZWF0ZSgpDQ0KJHZiID0gTmV3LU9iamVjdCBieXRlW10gNjQ7ICRybmcuR2V0Qnl0ZXMoJHZiKTsg
>> "%B64%" echo JHZlcmlmaWVyID0gQjY0VXJsICR2Yg0NCiRzaGEgPSBbU2VjdXJpdHkuQ3J5cHRvZ3JhcGh5LlNI
>> "%B64%" echo QTI1Nl06OkNyZWF0ZSgpDQ0KJGNoYWxsZW5nZSA9IEI2NFVybCAkc2hhLkNvbXB1dGVIYXNoKFtU
>> "%B64%" echo ZXh0LkVuY29kaW5nXTo6QVNDSUkuR2V0Qnl0ZXMoJHZlcmlmaWVyKSkNDQokc2IgPSBOZXctT2Jq
>> "%B64%" echo ZWN0IGJ5dGVbXSAxNjsgJHJuZy5HZXRCeXRlcygkc2IpOyAkc3RhdGUgPSBCNjRVcmwgJHNiDQ0K
>> "%B64%" echo DQ0KJGF1dGhVcmwgPSAiJEJBU0Uvb2F1dGgyL2F1dGhvcml6ZT9yZXNwb25zZV90eXBlPWNvZGUm
>> "%B64%" echo Y2xpZW50X2lkPSRjbGllbnRJZCIgKw0NCiAgICAgICAgICAgIiZyZWRpcmVjdF91cmk9IiArIFtV
>> "%B64%" echo cmldOjpFc2NhcGVEYXRhU3RyaW5nKCRSRURJUikgKw0NCiAgICAgICAgICAgIiZzY29wZT0iICsg
>> "%B64%" echo W1VyaV06OkVzY2FwZURhdGFTdHJpbmcoJFNDT1BFKSArDQ0KICAgICAgICAgICAiJnN0YXRlPSRz
>> "%B64%" echo dGF0ZSZjb2RlX2NoYWxsZW5nZT0kY2hhbGxlbmdlJmNvZGVfY2hhbGxlbmdlX21ldGhvZD1TMjU2
>> "%B64%" echo Ig0NCg0NCiRsaXN0ZW5lciA9IE5ldy1PYmplY3QgU3lzdGVtLk5ldC5Tb2NrZXRzLlRjcExpc3Rl
>> "%B64%" echo bmVyKFtOZXQuSVBBZGRyZXNzXTo6TG9vcGJhY2ssICRQT1JUKQ0NCnRyeSB7ICRsaXN0ZW5lci5T
>> "%B64%" echo dGFydCgpIH0gY2F0Y2ggew0NCiAgU2F5ICgi4p2MIOuCtCBQQyDssL3qtawoIiArICRQT1JUICsg
>> "%B64%" echo IuuyiCnrpbwg66q7IOyXtOyXiOyKteuLiOuLpDogIiArICRfLkV4Y2VwdGlvbi5NZXNzYWdlKSAi
>> "%B64%" echo UmVkIg0NCiAgU2F5ICIgICDri6Trpbgg7ZSE66Gc6re4656o7J20IOq3uCDrsojtmLjrpbwg7JOw
>> "%B64%" echo 6rOgIOyeiOydhCDsiJgg7J6I7Iq164uI64ukLiDsnqDsi5wg65KkIOuLpOyLnCDsi6TtlontlbQg
>> "%B64%" echo 7KO87IS47JqULiINDQogIERvbmUgMQ0NCn0NDQoNDQpTYXkgIiINDQpTYXkgIuKRoSDsirnsnbgg
>> "%B64%" echo 7LC97J2EIOyXveuLiOuLpC4g67iM65287Jqw7KCA7JeQ7IScIO2XiOyaqeydhCDriITrpbTshLjs
>> "%B64%" echo mpQuIg0NClNheSAiIg0NClNheSAoIiAgICIgKyAkYXV0aFVybCkgIkRhcmtHcmF5Ig0NClNheSAi
>> "%B64%" echo Ig0NCnRyeSB7IFN0YXJ0LVByb2Nlc3MgJGF1dGhVcmwgfCBPdXQtTnVsbCB9IGNhdGNoIHsgU2F5
>> "%B64%" echo ICIgICAo67iM65287Jqw7KCA6rCAIOyViCDsl7TrpqzrqbQg7JyEIOyjvOyGjOulvCDsp4HsoJEg
>> "%B64%" echo 67aZ7Jes64Sj7Jy87IS47JqUKSIgIlllbGxvdyIgfQ0NCg0NCiRjb2RlID0gJG51bGw7ICRkZWFk
>> "%B64%" echo bGluZSA9IChHZXQtRGF0ZSkuQWRkTWludXRlcyg1KQ0NCndoaWxlICgoR2V0LURhdGUpIC1sdCAk
>> "%B64%" echo ZGVhZGxpbmUgLWFuZCAtbm90ICRjb2RlKSB7DQ0KICBpZiAoLW5vdCAkbGlzdGVuZXIuUGVuZGlu
>> "%B64%" echo ZygpKSB7IFN0YXJ0LVNsZWVwIC1NaWxsaXNlY29uZHMgMzAwOyBjb250aW51ZSB9DQ0KICAkY2wg
>> "%B64%" echo PSAkbGlzdGVuZXIuQWNjZXB0VGNwQ2xpZW50KCk7ICRzdCA9ICRjbC5HZXRTdHJlYW0oKQ0NCiAg
>> "%B64%" echo JGJ1ZiA9IE5ldy1PYmplY3QgYnl0ZVtdIDgxOTI7ICRuID0gJHN0LlJlYWQoJGJ1ZiwgMCwgJGJ1
>> "%B64%" echo Zi5MZW5ndGgpDQ0KICAkcmVxID0gW1RleHQuRW5jb2RpbmddOjpBU0NJSS5HZXRTdHJpbmcoJGJ1
>> "%B64%" echo ZiwgMCwgJG4pDQ0KICAkZmlyc3QgPSAoJHJlcSAtc3BsaXQgImByYG4iKVswXQ0NCiAgaWYgKCRm
>> "%B64%" echo aXJzdCAtbWF0Y2ggJ0dFVFxzKyhcUyspJykgew0NCiAgICAkcSA9ICRNYXRjaGVzWzFdDQ0KICAg
>> "%B64%" echo IGlmICgkcSAtbWF0Y2ggJ1s/Jl1jb2RlPShbXiZcc10rKScpIHsgJGNvZGUgPSBbVXJpXTo6VW5l
>> "%B64%" echo c2NhcGVEYXRhU3RyaW5nKCRNYXRjaGVzWzFdKSB9DQ0KICAgIGlmICgkcSAtbWF0Y2ggJ1s/Jl1z
>> "%B64%" echo dGF0ZT0oW14mXHNdKyknKSB7DQ0KICAgICAgaWYgKFtVcmldOjpVbmVzY2FwZURhdGFTdHJpbmco
>> "%B64%" echo JE1hdGNoZXNbMV0pIC1uZSAkc3RhdGUpIHsNDQogICAgICAgIFNheSAi4p2MIOydkeuLteydmCDt
>> "%B64%" echo kZzsi53snbQg7JWIIOunnuyKteuLiOuLpCjspJHqsITsl5DshJwg6rCA66Gc7LGE7JiA7J2EIOyI
>> "%B64%" echo mCDsnojsirXri4jri6QpLiIgIlJlZCI7ICRjb2RlID0gJG51bGwNDQogICAgICB9DQ0KICAgIH0N
>> "%B64%" echo DQogIH0NDQogICRodG1sID0gIjxodG1sPjxoZWFkPjxtZXRhIGNoYXJzZXQ9J3V0Zi04Jz48L2hl
>> "%B64%" echo YWQ+PGJvZHkgc3R5bGU9J2ZvbnQtZmFtaWx5OnNhbnMtc2VyaWY7YmFja2dyb3VuZDojMTExO2Nv
>> "%B64%" echo bG9yOiNlZWU7cGFkZGluZzo0MHB4Jz48aDI+IiArDQ0KICAgICAgICAgICQoaWYgKCRjb2RlKSB7
>> "%B64%" echo ICLsirnsnbgg7JmE66OMIiB9IGVsc2UgeyAi7Iq57J24IOyLpO2MqCIgfSkgKw0NCiAgICAgICAg
>> "%B64%" echo ICAiPC9oMj48cD7snbQg7LC97J2EIOuLq+qzoCDqsoDsnYAg7LC97Jy866GcIOuPjOyVhOqwgOyE
>> "%B64%" echo uOyalC48L3A+PC9ib2R5PjwvaHRtbD4iDQ0KICAkYm9keSA9IFtUZXh0LkVuY29kaW5nXTo6VVRG
>> "%B64%" echo OC5HZXRCeXRlcygkaHRtbCkNDQogICRoZWFkID0gW1RleHQuRW5jb2RpbmddOjpBU0NJSS5HZXRC
>> "%B64%" echo eXRlcygiSFRUUC8xLjEgMjAwIE9LYHJgbkNvbnRlbnQtVHlwZTogdGV4dC9odG1sOyBjaGFyc2V0
>> "%B64%" echo PXV0Zi04YHJgbkNvbnRlbnQtTGVuZ3RoOiAkKCRib2R5Lkxlbmd0aClgcmBuQ29ubmVjdGlvbjog
>> "%B64%" echo Y2xvc2VgcmBuYHJgbiIpDQ0KICAkc3QuV3JpdGUoJGhlYWQsIDAsICRoZWFkLkxlbmd0aCk7ICRz
>> "%B64%" echo dC5Xcml0ZSgkYm9keSwgMCwgJGJvZHkuTGVuZ3RoKTsgJHN0LkZsdXNoKCkNDQogICRjbC5DbG9z
>> "%B64%" echo ZSgpDQ0KfQ0NCiRsaXN0ZW5lci5TdG9wKCkNDQoNDQppZiAoLW5vdCAkY29kZSkgeyBTYXkgIiI7
>> "%B64%" echo IFNheSAi4p2MIOyLnOqwhCDslYjsl5Ag7Iq57J247J20IOyViCDrkJDsirXri4jri6QuIOuLpOyL
>> "%B64%" echo nCDsi6TtlontlbQg7KO87IS47JqULiIgIlJlZCI7IERvbmUgMSB9DQ0KU2F5ICIiDQ0KU2F5ICIg
>> "%B64%" echo ICDinIUg7Iq57J24IOyZhOujjCIgIkdyZWVuIg0NCg0NCiMg4pSA4pSAIOKRoiDsl7Tsh6Ag6rWQ
>> "%B64%" echo 7ZmYIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgA0NCiRmb3JtID0gImdyYW50X3R5cGU9YXV0
>> "%B64%" echo aG9yaXphdGlvbl9jb2RlJmNvZGU9IiArIFtVcmldOjpFc2NhcGVEYXRhU3RyaW5nKCRjb2RlKSAr
>> "%B64%" echo DQ0KICAgICAgICAiJnJlZGlyZWN0X3VyaT0iICsgW1VyaV06OkVzY2FwZURhdGFTdHJpbmcoJFJF
>> "%B64%" echo RElSKSArDQ0KICAgICAgICAiJmNsaWVudF9pZD0iICsgW1VyaV06OkVzY2FwZURhdGFTdHJpbmco
>> "%B64%" echo JGNsaWVudElkKSArDQ0KICAgICAgICAiJmNvZGVfdmVyaWZpZXI9IiArIFtVcmldOjpFc2NhcGVE
>> "%B64%" echo YXRhU3RyaW5nKCR2ZXJpZmllcikNDQp0cnkgew0NCiAgJHRvayA9IEludm9rZS1SZXN0TWV0aG9k
>> "%B64%" echo IC1VcmkgIiRCQVNFL29hdXRoMi90b2tlbiIgLU1ldGhvZCBQb3N0IC1UaW1lb3V0U2VjIDQwIGAN
>> "%B64%" echo DQogICAgLUhlYWRlcnMgQHsgIlVzZXItQWdlbnQiID0gJFVBIH0gLUNvbnRlbnRUeXBlICJhcHBs
>> "%B64%" echo aWNhdGlvbi94LXd3dy1mb3JtLXVybGVuY29kZWQiIC1Cb2R5ICRmb3JtDQ0KfSBjYXRjaCB7DQ0K
>> "%B64%" echo ICBTYXkgIuKdjCDsl7Tsh6Ag6rWQ7ZmYIOyLpO2MqC4iICJSZWQiOyBTYXkgKCIgICDsgqzsnKA6
>> "%B64%" echo ICIgKyAkXy5FeGNlcHRpb24uTWVzc2FnZSkgIlJlZCI7IERvbmUgMQ0NCn0NDQokYWNjZXNzID0g
>> "%B64%" echo W3N0cmluZ10kdG9rLmFjY2Vzc190b2tlbg0NCiRyZWZyZXNoID0gW3N0cmluZ10kdG9rLnJlZnJl
>> "%B64%" echo c2hfdG9rZW4NDQpTYXkgIiINDQpTYXkgIuKRoiDsl7Tsh6Ag67Cb7J2MIOKckyINDQpTYXkgKCIg
>> "%B64%" echo ICDsoJHsho0g7Je07IegIDogIiArIChNYXNrICRhY2Nlc3MpKQ0NClNheSAoIiAgIOqwseyLoCDs
>> "%B64%" echo l7Tsh6AgOiAiICsgKE1hc2sgJHJlZnJlc2gpKQ0NCmlmICgkdG9rLmV4cGlyZXNfaW4pIHsgU2F5
>> "%B64%" echo ICgiICAg7KCR7IaNIOyXtOyHoCDsiJjrqoUgOiAiICsgJHRvay5leHBpcmVzX2luICsgIuy0iCIp
>> "%B64%" echo IH0NDQoNDQppZiAoLW5vdCAkcmVmcmVzaCkgew0NCiAgU2F5ICIiDQ0KICBTYXkgIuKdjCDqsLHs
>> "%B64%" echo i6Ag7Je07Ieg6rCAIOydkeuLteyXkCDsl4bsirXri4jri6Qg4oCUIOydtCDspITsnYQg6re464yA
>> "%B64%" echo 66GcIOyVjOugpCDso7zshLjsmpQuIiAiUmVkIjsgRG9uZSAxDQ0KfQ0NCg0NCg0KIyDilIDilIAg
>> "%B64%" echo 4pGjICoq67aZ7Jes64Sj6riwIOyghOyXkCDsl6zquLDshJwg7Kad66qF7ZWc64ukKiog4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSADQojIOKaoCDsmZwg7J20IOuLqOqzhOqwgCDsnojrgpgoMjYwODEyIOyLpOyCrOqzoCkgPSAx
>> "%B64%" echo 7YyQ7Jy866GcIOuwm+ydgCDsl7Tsh6DripQg7J6Q6rKpwrfsnpTslaHsnbQg64ukIO2GteqzvO2V
>> "%B64%" echo mOuKlOuNsA0KIyAgICoq66qo6424IOuqqeuhneyXkCDsi5zrjITsiqTqsIAg7JeG7JeI64ukLioq
>> "%B64%" echo IOq3uOqxuCDquYPtl4jruIzsl5Ag64Sj6rOgIOufrOuEiOulvCDrj4zrprAg65Kk7JeQ7JW8IOyV
>> "%B64%" echo jOyVmOuLpCA9DQojICAg7Jq07JiB7J6Q6rCAIO2Xm+yImOqzoOulvCDtlojri6QuIOq3uOuemOyE
>> "%B64%" echo nCAy7YyQ7J2AICoq7Je07Ieg66W8IOyjvOq4sCDsoITsl5AqKiDssL3qtazsl5Ag7KeB7KCRIOus
>> "%B64%" echo vOyWtOuzuOuLpC4NClNheSAiIg0KU2F5ICLikaMg7J20IOyXtOyHoOuhnCDsi5zrjITsiqTqsIAg
>> "%B64%" echo 7Je066as64qU7KeAIOyngOq4iCDtmZXsnbjtlanri4jri6QuIg0KDQokaGRyID0gQHsgIkF1dGhv
>> "%B64%" echo cml6YXRpb24iID0gIkJlYXJlciAkYWNjZXNzIjsgIlVzZXItQWdlbnQiID0gJFVBDQogICAgICAg
>> "%B64%" echo ICAgIkFjY2VwdCIgPSAiYXBwbGljYXRpb24vanNvbiwgdGV4dC9ldmVudC1zdHJlYW0iOyAiTUNQ
>> "%B64%" echo LVByb3RvY29sLVZlcnNpb24iID0gIjIwMjUtMDYtMTgiIH0NCiRzY3JpcHQ6c2lkID0gJG51bGwN
>> "%B64%" echo CmZ1bmN0aW9uIFJwYyhbc3RyaW5nXSRtZXRob2QsICRwcm0pIHsNCiAgJGJvZHkgPSAoQHsganNv
>> "%B64%" echo bnJwYyA9ICIyLjAiOyBpZCA9IChHZXQtUmFuZG9tIC1NYXhpbXVtIDk5OTk5KTsgbWV0aG9kID0g
>> "%B64%" echo JG1ldGhvZDsgcGFyYW1zID0gJHBybSB9IHwgQ29udmVydFRvLUpzb24gLURlcHRoIDEyIC1Db21w
>> "%B64%" echo cmVzcykNCiAgJGggPSAkaGRyLkNsb25lKCk7IGlmICgkc2NyaXB0OnNpZCkgeyAkaFsiTWNwLVNl
>> "%B64%" echo c3Npb24tSWQiXSA9ICRzY3JpcHQ6c2lkIH0NCiAgJHIgPSBJbnZva2UtV2ViUmVxdWVzdCAtVXJp
>> "%B64%" echo ICIkQkFTRS9tY3AiIC1NZXRob2QgUG9zdCAtSGVhZGVycyAkaCAtQ29udGVudFR5cGUgImFwcGxp
>> "%B64%" echo Y2F0aW9uL2pzb24iIC1Cb2R5ICRib2R5IC1UaW1lb3V0U2VjIDYwIC1Vc2VCYXNpY1BhcnNpbmcN
>> "%B64%" echo CiAgaWYgKCRyLkhlYWRlcnNbIk1jcC1TZXNzaW9uLUlkIl0pIHsgJHNjcmlwdDpzaWQgPSBbc3Ry
>> "%B64%" echo aW5nXSRyLkhlYWRlcnNbIk1jcC1TZXNzaW9uLUlkIl0gfQ0KICAkdCA9IFtzdHJpbmddJHIuQ29u
>> "%B64%" echo dGVudA0KICBpZiAoJHQgLW1hdGNoICcoP20pXmRhdGE6XHMqKFx7LiopJCcpIHsgJHQgPSAkTWF0
>> "%B64%" echo Y2hlc1sxXSB9ICAgIyDsnbTrsqTtirgg7Iqk7Yq466a87J2066m0IOyVjOunueydtOunjA0KICBy
>> "%B64%" echo ZXR1cm4gKCR0IHwgQ29udmVydEZyb20tSnNvbikNCn0NCmZ1bmN0aW9uIFRvb2woW3N0cmluZ10k
>> "%B64%" echo bmFtZSwgJGFyZ3MyKSB7DQogICRyZXMgPSBScGMgInRvb2xzL2NhbGwiIEB7IG5hbWUgPSAkbmFt
>> "%B64%" echo ZTsgYXJndW1lbnRzID0gJGFyZ3MyIH0NCiAgaWYgKCRyZXMuZXJyb3IpIHsgcmV0dXJuICJFUlIg
>> "%B64%" echo IiArICgkcmVzLmVycm9yIHwgQ29udmVydFRvLUpzb24gLUNvbXByZXNzKSB9DQogIGZvcmVhY2gg
>> "%B64%" echo KCRjIGluICRyZXMucmVzdWx0LmNvbnRlbnQpIHsgaWYgKCRjLnR5cGUgLWVxICJ0ZXh0IikgeyBy
>> "%B64%" echo ZXR1cm4gW3N0cmluZ10kYy50ZXh0IH0gfQ0KICByZXR1cm4gKCRyZXMucmVzdWx0IHwgQ29udmVy
>> "%B64%" echo dFRvLUpzb24gLURlcHRoIDggLUNvbXByZXNzKQ0KfQ0KDQokb2sgPSAkZmFsc2UNCnRyeSB7DQog
>> "%B64%" echo IFJwYyAiaW5pdGlhbGl6ZSIgQHsgcHJvdG9jb2xWZXJzaW9uID0gIjIwMjUtMDYtMTgiOyBjYXBh
>> "%B64%" echo YmlsaXRpZXMgPSBAe30NCiAgICAgICAgICAgICAgICAgICAgICBjbGllbnRJbmZvID0gQHsgbmFt
>> "%B64%" echo ZSA9ICJub211dGUtcHJvYmUiOyB2ZXJzaW9uID0gIjIuMCIgfSB9IHwgT3V0LU51bGwNCiAgdHJ5
>> "%B64%" echo IHsgUnBjICJub3RpZmljYXRpb25zL2luaXRpYWxpemVkIiBAe30gfCBPdXQtTnVsbCB9IGNhdGNo
>> "%B64%" echo IHt9DQogICRiYWwgPSBUb29sICJiYWxhbmNlIiBAe30NCiAgU2F5ICgiICAg7J6U7JWhIDogIiAr
>> "%B64%" echo ICRiYWwpDQogICRjb3N0ID0gVG9vbCAiZ2VuZXJhdGVfdmlkZW8iIEB7IHBhcmFtcyA9IEB7IG1v
>> "%B64%" echo ZGVsID0gInNlZWRhbmNlXzJfNSI7IHByb21wdCA9ICJjb3N0IGNoZWNrIg0KICAgICAgZHVyYXRp
>> "%B64%" echo b24gPSAzMDsgcmVzb2x1dGlvbiA9ICI3MjBwIjsgbW9kZSA9ICJvbW5pX3JlZmVyZW5jZSI7IGFz
>> "%B64%" echo cGVjdF9yYXRpbyA9ICI5OjE2Ig0KICAgICAgZ2VuZXJhdGVfYXVkaW8gPSAkdHJ1ZTsgdXNlX3Vu
>> "%B64%" echo bGltID0gJGZhbHNlOyBnZXRfY29zdCA9ICR0cnVlIH0gfQ0KICBTYXkgKCIgICDsi5zrjITsiqQg
>> "%B64%" echo 6rKs7KCBIDogIiArICRjb3N0KQ0KICBpZiAoJGNvc3QgLW1hdGNoICciY3JlZGl0cyInIC1vciAk
>> "%B64%" echo Y29zdCAtbWF0Y2ggJ1xkK1xzKmNyZWRpdCcpIHsgJG9rID0gJHRydWUgfQ0KfSBjYXRjaCB7DQog
>> "%B64%" echo IFNheSAoIiAgIOKaoCDtmZXsnbgg7Zi47Lac7J20IOyLpO2MqO2WiOyKteuLiOuLpDogIiArICRf
>> "%B64%" echo LkV4Y2VwdGlvbi5NZXNzYWdlKSAiWWVsbG93Ig0KfQ0KDQppZiAoLW5vdCAkb2spIHsNCiAgU2F5
>> "%B64%" echo ICIiDQogIFNheSAiICDilIzilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lJAiICJSZWQiDQogIFNheSAiICDilIIgIOKdjCDsnbQg7Je07Ieg66Gc64qUIOyLnOuMhOyKpOqw
>> "%B64%" echo gCDslYgg7Je066a964uI64ukICAgICAg4pSCIiAiUmVkIg0KICBTYXkgIiAg4pSU4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSYIiAiUmVkIg0KICBTYXkgIiINCiAgU2F5
>> "%B64%" echo ICIgIOKaoCAqKuq5g+2XiOu4jOyXkCDrtpnsl6zrhKPsp4Ag66eI7IS47JqULioqIOuEo+yWtOuP
>> "%B64%" echo hCDsmIHsg4HsnbQg7JWIIOunjOuTpOyWtOynkeuLiOuLpC4iICJZZWxsb3ciDQogIFNheSAiICDs
>> "%B64%" echo nIQg65GQIOykhCjsnpTslaHCt+yLnOuMhOyKpCDqsqzsoIEp7J2EIOq3uOuMgOuhnCDrs7Xsgqzt
>> "%B64%" echo lbTshJwg7JWM66CkIOyjvOyEuOyalC4g6re4IOqwkuycvOuhnCDri6TsnYwg7IiY66W8IOygle2V
>> "%B64%" echo qeuLiOuLpC4iDQogIFNheSAiIg0KICBTZXQtQ29udGVudCAtUGF0aCAkS2V5UGF0aCAtVmFsdWUg
>> "%B64%" echo IiIgLUVuY29kaW5nIEFTQ0lJIC1Ob05ld2xpbmUNCiAgRG9uZSAxDQp9DQpTYXkgIiAgIOKchSDs
>> "%B64%" echo i5zrjITsiqQg7Je066a8IO2ZleyduCIgIkdyZWVuIg0KDQojIOKaoCDqsJLrp4wg7ZWcIOykhOuh
>> "%B64%" echo nCDsk7Tri6Qg4oCUIO2BsCDrjanslrTrpqzsl5DshJwg64iI7Jy866GcIOyemOudvOuCtOqyjCDt
>> "%B64%" echo lZjrqbQg7IKs6rOg6rCAIOuCnOuLpC4NDQojICAg7ZSE66Gc6re4656oIOuyiO2YuOuPhCDqsJns
>> "%B64%" echo nbQg7ZWE7JqU7ZW07IScIO2VnCDspITroZwg66y264qU64ukKOu2meyXrOuEo+q4sCAx7ZqMIOyb
>> "%B64%" echo kOy5mSkuDQ0KU2V0LUNvbnRlbnQgLVBhdGggJEtleVBhdGggLVZhbHVlICgkY2xpZW50SWQgKyAi
>> "%B64%" echo OiIgKyAkcmVmcmVzaCkgLUVuY29kaW5nIEFTQ0lJIC1Ob05ld2xpbmUNDQoNDQpTYXkgIiINDQpT
>> "%B64%" echo YXkgIiAg4pSM4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSQIiAiR3Jl
>> "%B64%" echo ZW4iDQ0KU2F5ICIgIOKUgiAg64Gd64Ks7Iq164uI64ukLiDrkZAg6rG47J2M66eMIO2VmOuptCDr
>> "%B64%" echo kKnri4jri6QgICAgICAgIOKUgiIgIkdyZWVuIg0NClNheSAiICDilJTilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilJgiICJHcmVlbiINDQpTYXkgIiINDQpTYXkgIiAgMSkg
>> "%B64%" echo 67CU7YOV7ZmU66m07J2YIOOAjO2eieyKpO2VhOuTnOyXtOyHoF/rtpnsl6zrhKPquLAudHh044CN
>> "%B64%" echo IOulvCDsl7TslrQg7JWI7J2YIOqwkuydhCDsoITrtoAg67O17IKsIg0NClNheSAiIg0NClNheSAi
>> "%B64%" echo ICAyKSDquYPtl4jruIwg66CI7Y+sIOKGkiBTZXR0aW5ncyDihpIgU2VjcmV0cyBhbmQgdmFyaWFi
>> "%B64%" echo bGVzIOKGkiBBY3Rpb25zIg0NClNheSAoIiAgICAg4oaSICIgKyAkU0VDUkVUX05BTUUgKyAiIOul
>> "%B64%" echo vCDsnbQg6rCS7Jy866GcIOuwlOq+uOq4sChVcGRhdGUgc2VjcmV0KSIpDQ0KU2F5ICIiDQ0KU2F5
>> "%B64%" echo ICIgIOKaoCDrtpnsl6zrhKPsnYAg65Kk7JeQ64qUIOuwlO2Dle2ZlOuptOydmCDrkZAg7YyM7J28
>> "%B64%" echo 7J2EIOyngOyasOyEuOyalC4iDQ0KU2F5ICIgIOKaoCDsnbQg6rCS7J2AIOuCqOyXkOqyjCDso7zs
>> "%B64%" echo p4Ag66eI7IS47JqULiDqs4TsoJUg7YGs66CI65Sn7J2EIOyTuCDsiJgg7J6I64qUIOqwkuyeheuL
>> "%B64%" echo iOuLpC4iDQ0KU2F5ICIiDQ0KV3JpdGUtSG9zdCAoIuyXtOyHoDogIiArICRLZXlQYXRoKSAtRm9y
>> "%B64%" echo ZWdyb3VuZENvbG9yIERhcmtHcmF5DQ0KRG9uZSAwDQ0K
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
