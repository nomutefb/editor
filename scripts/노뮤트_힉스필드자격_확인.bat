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
>> "%B64%" echo lZDilZDilZDilZDilZANCiMgaGZfcHJvYmUucHMxIOKAlCDtnonsiqTtlYTrk5wg6rWs64+FIOye
>> "%B64%" echo kOqyqeydhCDrn6zrhIjqsIAg7JO4IOyImCDsnojripQgKirsl7Tsh6Ag7ZWcIOykhCoq66GcIOuw
>> "%B64%" echo lOq+vOuLpA0KIyAgICjsmrTsmIHsnpAgMjYwODEyICLsl6ztirwgYmF0IOyjvOuptCDrsJTroZzt
>> "%B64%" echo lagiKQ0KIw0KIyDsmZwg7ZWE7JqU7ZWc6rCAID0g7Z6J7Iqk7ZWE65Oc64qUIOu2meyXrOuEo+yd
>> "%B64%" echo hCBBUEkg7YKk66W8ICoq7JWIIOykgOuLpCoqLiDqs4TsoJUg66Gc6re47J24IOuwqeyLneydtOud
>> "%B64%" echo vCDtmZTrqbQg7Ja065SU7JeQ64+EDQojICAg67O17IKs7ZWgIOqwkuydtCDsl4bri6QuIOufrOuE
>> "%B64%" echo iCjsgqzrnowg7JeG64qUIOyekOuPmSDsi6Ttlokp6rCAIOyTsOugpOuptCDtlZwg67KIIOuhnOq3
>> "%B64%" echo uOyduO2VtOyEnCAqKuqwseyLoCDsl7Tsh6AqKuulvA0KIyAgIOuwm+yVhCDquYPtl4jruIwg67mE
>> "%B64%" echo 67CA6rCS7JeQIOuEo+yWtOyVvCDtlZjqs6AsIOq3uCDtlZwg67KI7J2EIOyXrOq4sOyEnCDtlZzr
>> "%B64%" echo i6QuDQojDQojIOyZnCDsnpHsl4Ug7Z2Q66aE7J20IOyVhOuLiOudvCBQQyDsnbjqsIAgPSDsnbQg
>> "%B64%" echo 66CI7Y+s64qUICoq6rO16rCcKirri6QuIOyKueyduCDsvZTrk5zrpbwg65+s64SI7JeQ7IScIOud
>> "%B64%" echo hOyasOuptCDqs7XqsJwg6riw66Gd7JeQDQojICAg7LCN7Z6I6rOgLCAxNeu2hCDsirnsnbgg7LC9
>> "%B64%" echo IOuPmeyViCDrgqjsnbQg7J6Q6riwIOqzhOygleycvOuhnCDsirnsnbjtlbTrsoTrprQg7IiYIOye
>> "%B64%" echo iOuLpC4g64SkIO2ZlOuptOyXkOunjCDrnKjripQg6rG0IOuEpCBQQyDrv5DsnbTri6QuDQojDQoj
>> "%B64%" echo IOKaoCDtjJDsoJXquLDri6QuIOuwsOyEoCDslYTri5go66CI7Y+sIOudvOydtOu4jCDrrLTsoJHs
>> "%B64%" echo tIkgwrcg7J6Q64+ZIOyLpO2WiSAwIMK3IOyViCDrj4zrpqzrqbQg7JWE66y0IOydvOuPhCDslYgg
>> "%B64%" echo 7J287Ja064Kc64ukKS4NCiMg4pqgIO2BrOugiOuUpyAwIOKAlCDsmIHsg4HCt+q3uOumvOydhCDr
>> "%B64%" echo p4zrk6Tsp4Ag7JWK64qU64ukLiDroZzqt7jsnbjqs7wg7J6Q6rKpIO2ZleyduOunjCDtlZzri6Qu
>> "%B64%" echo DQojDQojIO2dkOumhCjsi6TsuKEg6rec6rKpIMK3IDI2MDgxMikgPQ0KIyAgIOKRoCBQT1NUIC9h
>> "%B64%" echo dXRob3JpemUgICAgICAgICAg4oaSIOq4sOq4sCDsvZTrk5wgKyDsirnsnbgg7KO87IaMKDE167aE
>> "%B64%" echo IMK3IDPstIgg6rCE6rKpKQ0KIyAgIOKRoSDruIzrnbzsmrDsoIDsl5DshJwg7Iq57J24DQojICAg
>> "%B64%" echo 4pGiIFBPU1QgL3Rva2VuIHtkZXZpY2VfY29kZX0g4oaSIOygkeyGjSDsl7Tsh6AgKyAqKuqwseyL
>> "%B64%" echo oCDsl7Tsh6AqKg0KIyAgIOKRoyBQT1NUIC92YWxpZGF0ZSB7dG9rZW59ICAgIOKGkiDqs4TsoJUg
>> "%B64%" echo 67KI7Zi4IO2ajOyLoCA9IOyLpOygnOuhnCDsk7gg7IiYIOyeiOuLpOuKlCDspp3qsbANCiMNCiMg
>> "%B64%" echo 7IKw7LacOiAg67CU7YOV7ZmU66m0XO2eieyKpO2VhOuTnO2ZleyduF/qsrDqs7wudHh0ICAgKOq4
>> "%B64%" echo sOuhnSDCtyDsl7Tsh6DripQg7JWeIDEy7J6Q66eMIOuCqOq4sOqzoCDqsIDrprDri6QpDQojICAg
>> "%B64%" echo ICAgICDrsJTtg5XtmZTrqbRc7Z6J7Iqk7ZWE65Oc7Je07IegX+u2meyXrOuEo+q4sC50eHQgKOqw
>> "%B64%" echo seyLoCDsl7Tsh6AgKirqsJIg7ZWcIOykhOunjCoqIMK3IOuCqOyXkOqyjCDso7zsp4Ag66eI6528
>> "%B64%" echo KQ0KIyDrgYTripQg67KVOiDslYgg64+M66as66m0IOuBnS4g7ISk7LmY65CY64qUIOqyg+uPhCwg
>> "%B64%" echo 7J6Q64+ZIOyLpO2WieuQmOuKlCDqsoPrj4Qg7JeG64ukLg0KIyDsg53shLEg7KCV67O4OiBzY3Jp
>> "%B64%" echo cHRzL2hmX3Byb2JlLnBzMSDCtyDrsojrk6Qg7J6s7IOd7ISxID0gcHl0aG9uMyBzY3JpcHRzL2J1
>> "%B64%" echo aWxkX2hmX3Byb2JlX2J1bmRsZS5weQ0KIyDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi
>> "%B64%" echo lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi
>> "%B64%" echo lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi
>> "%B64%" echo lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDi
>> "%B64%" echo lZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZDilZANCiRFcnJvckFjdGlvblByZWZlcmVu
>> "%B64%" echo Y2UgPSAiU3RvcCINCnRyeSB7IFtOZXQuU2VydmljZVBvaW50TWFuYWdlcl06OlNlY3VyaXR5UHJv
>> "%B64%" echo dG9jb2wgPSBbTmV0LlNlY3VyaXR5UHJvdG9jb2xUeXBlXTo6VGxzMTIgfSBjYXRjaCB7fQ0KdHJ5
>> "%B64%" echo IHsgJE91dHB1dEVuY29kaW5nID0gW0NvbnNvbGVdOjpPdXRwdXRFbmNvZGluZyA9IFtUZXh0LkVu
>> "%B64%" echo Y29kaW5nXTo6VVRGOCB9IGNhdGNoIHt9DQoNCiRBVVRIID0gImh0dHBzOi8vZm5mLWRldmljZS1h
>> "%B64%" echo dXRoLmhpZ2dzZmllbGQuYWkiDQokU0VDUkVUX05BTUUgPSAiSElHR1NGSUVMRF9SRUZSRVNIX1RP
>> "%B64%" echo S0VOIg0KDQojIOKaoCDrsJTtg5XtmZTrqbQg6rK966Gc64qUIOu5iCDrrLjsnpDsl7TroZwg7Jis
>> "%B64%" echo IOyImCDsnojri6Qo7JuQ65Oc65287J2067iMIOuwseyXhcK367mE7JyI64+E7JqwIOyLpOy4oSkg
>> "%B64%" echo 4oaSIO2PtOuwsSDsgqzsiqwuDQojICAg7ZWcIOy5uOydtOudvOuPhCDruYTrqbQgSm9pbi1QYXRo
>> "%B64%" echo IOqwgCDqt7gg7J6Q66as7JeQ7IScIOyjveyWtCDtjJDsoJUg7J6Q7LK066W8IOuquyDtlZzri6Qo
>> "%B64%" echo 6re466GdIO2MkOygleq4sCDssqsg7Iuk7ZaJIOu0ie2VqSkuDQokRGVzayA9ICIiDQpmb3JlYWNo
>> "%B64%" echo ICgkYyBpbiBAKFtFbnZpcm9ubWVudF06OkdldEZvbGRlclBhdGgoW0Vudmlyb25tZW50K1NwZWNp
>> "%B64%" echo YWxGb2xkZXJdOjpEZXNrdG9wRGlyZWN0b3J5KSwNCiAgICAgICAgICAgICAgICAgW0Vudmlyb25t
>> "%B64%" echo ZW50XTo6R2V0Rm9sZGVyUGF0aChbRW52aXJvbm1lbnQrU3BlY2lhbEZvbGRlcl06OkRlc2t0b3Ap
>> "%B64%" echo LA0KICAgICAgICAgICAgICAgICAoSm9pbi1QYXRoICRlbnY6VVNFUlBST0ZJTEUgIkRlc2t0b3Ai
>> "%B64%" echo KSwNCiAgICAgICAgICAgICAgICAgKEpvaW4tUGF0aCAkZW52OlVTRVJQUk9GSUxFICLrsJTtg5Ug
>> "%B64%" echo 7ZmU66m0IiksDQogICAgICAgICAgICAgICAgICRlbnY6VVNFUlBST0ZJTEUsICRlbnY6VEVNUCkp
>> "%B64%" echo IHsNCiAgaWYgKCRjIC1hbmQgKFRlc3QtUGF0aCAkYykpIHsgJERlc2sgPSAkYzsgYnJlYWsgfQ0K
>> "%B64%" echo fQ0KaWYgKC1ub3QgJERlc2spIHsgJERlc2sgPSAiLiIgfQ0KDQokTG9nUGF0aCAgPSBKb2luLVBh
>> "%B64%" echo dGggJERlc2sgIu2eieyKpO2VhOuTnO2ZleyduF/qsrDqs7wudHh0Ig0KJEtleVBhdGggID0gSm9p
>> "%B64%" echo bi1QYXRoICREZXNrICLtnonsiqTtlYTrk5zsl7Tsh6Bf67aZ7Jes64Sj6riwLnR4dCINCiRMaW5l
>> "%B64%" echo cyA9IE5ldy1PYmplY3QgU3lzdGVtLkNvbGxlY3Rpb25zLkFycmF5TGlzdA0KDQpmdW5jdGlvbiBT
>> "%B64%" echo YXkoW3N0cmluZ10kbSwgW3N0cmluZ10kY29sb3IgPSAiR3JheSIpIHsNCiAgV3JpdGUtSG9zdCAk
>> "%B64%" echo bSAtRm9yZWdyb3VuZENvbG9yICRjb2xvcg0KICBbdm9pZF0kTGluZXMuQWRkKCRtKQ0KfQ0KZnVu
>> "%B64%" echo Y3Rpb24gTWFzayhbc3RyaW5nXSR2KSB7DQogIGlmICgtbm90ICR2KSB7IHJldHVybiAiKOyXhuyd
>> "%B64%" echo jCkiIH0NCiAgaWYgKCR2Lkxlbmd0aCAtbGUgMTIpIHsgcmV0dXJuICIqKioiIH0NCiAgcmV0dXJu
>> "%B64%" echo ICR2LlN1YnN0cmluZygwLCAxMikgKyAi4oCmKCIgKyAkdi5MZW5ndGggKyAi7J6QKSINCn0NCmZ1
>> "%B64%" echo bmN0aW9uIFBvc3RKc29uKFtzdHJpbmddJHVybCwgJGJvZHkpIHsNCiAgJGpzb24gPSBpZiAoJGJv
>> "%B64%" echo ZHkpIHsgJGJvZHkgfCBDb252ZXJ0VG8tSnNvbiAtQ29tcHJlc3MgfSBlbHNlIHsgInt9IiB9DQog
>> "%B64%" echo IHJldHVybiBJbnZva2UtUmVzdE1ldGhvZCAtVXJpICR1cmwgLU1ldGhvZCBQb3N0IC1Db250ZW50
>> "%B64%" echo VHlwZSAiYXBwbGljYXRpb24vanNvbiIgLUJvZHkgJGpzb24gLVRpbWVvdXRTZWMgNDANCn0NCg0K
>> "%B64%" echo U2F5ICIiDQpTYXkgIiAg4pSM4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSQIiAiQ3lh
>> "%B64%" echo biINClNheSAiICDilIIgIOuFuOuupO2KuCDigJQg7Z6J7Iqk7ZWE65OcIOyekOqyqSDtmZXsnbgg
>> "%B64%" echo ICAgICAgICAgICAgICAgICAgIOKUgiIgIkN5YW4iDQpTYXkgIiAg4pSCICDroZzqt7jsnbggMe2a
>> "%B64%" echo jOuhnCDrn6zrhIjqsIAg7JO4IOyXtOyHoOulvCDrsJvslYTsmLXri4jri6QgICAgICAg4pSCIiAi
>> "%B64%" echo Q3lhbiINClNheSAiICDilIIgIO2BrOugiOuUp+ydgCDsk7Dsp4Ag7JWK7Iq164uI64ukKOyYgeyD
>> "%B64%" echo gcK36re466a8IOygnOyekSDsl4bsnYwpICAgIOKUgiIgIkN5YW4iDQpTYXkgIiAg4pSU4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSYIiAiQ3lhbiINClNheSAiIg0KU2F5ICgi7Iuk7ZaJ
>> "%B64%" echo IOyLnOqwgSA6ICIgKyAoR2V0LURhdGUgLUZvcm1hdCAieXl5eS1NTS1kZCBISDptbTpzcyIpKQ0K
>> "%B64%" echo U2F5ICIiDQoNCiMg4pSA4pSAIOKRoCDquLDquLAg7L2U65OcIOuwnOq4iSDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIANCnRyeSB7DQog
>> "%B64%" echo ICRhID0gUG9zdEpzb24gIiRBVVRIL2F1dGhvcml6ZSIgJG51bGwNCn0gY2F0Y2ggew0KICBTYXkg
>> "%B64%" echo IuKdjCDsirnsnbgg7L2U65Oc66W8IOuquyDrsJvslZjsirXri4jri6QuIiAiUmVkIg0KICBTYXkg
>> "%B64%" echo KCIgICDsgqzsnKA6ICIgKyAkXy5FeGNlcHRpb24uTWVzc2FnZSkgIlJlZCINCiAgU2F5ICIiDQog
>> "%B64%" echo IFNheSAiICAg7ZqM7ISg7J20IOunie2YlOqxsOuCmCDtnonsiqTtlYTrk5wg7Kq97J20IOyeoOyL
>> "%B64%" echo nCDrtojslYjsoJXtlZwg6rK97Jqw7J6F64uI64ukLiDsnqDsi5wg65KkIOuLpOyLnCDsi6Ttlont
>> "%B64%" echo lbQg7KO87IS47JqULiINCiAgJExpbmVzIC1qb2luICJgcmBuIiB8IFNldC1Db250ZW50IC1QYXRo
>> "%B64%" echo ICRMb2dQYXRoIC1FbmNvZGluZyBVVEY4DQogIFdyaXRlLUhvc3QgIiI7IFJlYWQtSG9zdCAi7JeU
>> "%B64%" echo 7YSw66W8IOuIhOultOuptCDri6vtnpnri4jri6QiIHwgT3V0LU51bGwNCiAgZXhpdCAxDQp9DQoN
>> "%B64%" echo CiRkZXZpY2VDb2RlID0gW3N0cmluZ10kYS5kZXZpY2VfY29kZQ0KJHVyaSAgICAgICAgPSBbc3Ry
>> "%B64%" echo aW5nXSRhLnZlcmlmaWNhdGlvbl91cmkNCiRpbnRlcnZhbCAgID0gaWYgKCRhLmludGVydmFsKSB7
>> "%B64%" echo IFtpbnRdJGEuaW50ZXJ2YWwgfSBlbHNlIHsgMyB9DQokZXhwaXJlcyAgICA9IGlmICgkYS5leHBp
>> "%B64%" echo cmVzX2luKSB7IFtpbnRdJGEuZXhwaXJlc19pbiB9IGVsc2UgeyA5MDAgfQ0KDQpTYXkgIuKRoCDs
>> "%B64%" echo irnsnbgg7LC97J2EIOyXveuLiOuLpC4iDQpTYXkgIiINClNheSAoIiAgICIgKyAkdXJpKSAiWWVs
>> "%B64%" echo bG93Ig0KU2F5ICIiDQpTYXkgIiAgIOu4jOudvOyasOyggOqwgCDslYgg7Je066as66m0IOychCDs
>> "%B64%" echo o7zshozrpbwg7KeB7KCRIOyXrOyEuOyalCjtj7DsnLzroZwg7Je07Ja064+EIOuQqeuLiOuLpCku
>> "%B64%" echo Ig0KU2F5ICgiICAg7Jyg7ZqoIOyLnOqwhCAiICsgW2ludF0oJGV4cGlyZXMgLyA2MCkgKyAi67aE
>> "%B64%" echo IikNClNheSAiIg0KdHJ5IHsgU3RhcnQtUHJvY2VzcyAkdXJpIHwgT3V0LU51bGwgfSBjYXRjaCB7
>> "%B64%" echo IH0NCg0KIyDilIDilIAg4pGhIOyKueyduCDquLDri6TrpqzquLAg4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSADQpTYXkgIuKRoSDs
>> "%B64%" echo irnsnbjsnYQg6riw64uk66a964uI64uk4oCmICjruIzrnbzsmrDsoIDsl5DshJwg7ZeI7Jqp7J2E
>> "%B64%" echo IOuIhOultOyEuOyalCkiDQokZGVhZGxpbmUgPSAoR2V0LURhdGUpLkFkZFNlY29uZHMoJGV4cGly
>> "%B64%" echo ZXMpDQokdG9rID0gJG51bGwNCiRkb3RzID0gMA0Kd2hpbGUgKChHZXQtRGF0ZSkgLWx0ICRkZWFk
>> "%B64%" echo bGluZSkgew0KICBTdGFydC1TbGVlcCAtU2Vjb25kcyAkaW50ZXJ2YWwNCiAgdHJ5IHsNCiAgICAk
>> "%B64%" echo dG9rID0gUG9zdEpzb24gIiRBVVRIL3Rva2VuIiBAeyBkZXZpY2VfY29kZSA9ICRkZXZpY2VDb2Rl
>> "%B64%" echo IH0NCiAgICBpZiAoJHRvayAtYW5kICR0b2suYWNjZXNzX3Rva2VuKSB7IGJyZWFrIH0NCiAgfSBj
>> "%B64%" echo YXRjaCB7DQogICAgIyDslYTsp4Eg7Iq57J24IOyghOydtOuptCA0MjIvNHh4IOqwgCDsoJXsg4Hs
>> "%B64%" echo nbTri6Qg4oCUIOyhsOyaqe2eiCDqs4Tsho0g6riw64uk66aw64ukLg0KICAgICR0b2sgPSAkbnVs
>> "%B64%" echo bA0KICB9DQogICRkb3RzKysNCiAgaWYgKCRkb3RzICUgMTAgLWVxIDApIHsgV3JpdGUtSG9zdCAo
>> "%B64%" echo IiAgIOKApiAiICsgW2ludF0oKCRkZWFkbGluZSAtIChHZXQtRGF0ZSkpLlRvdGFsU2Vjb25kcykg
>> "%B64%" echo KyAi7LSIIOuCqOydjCIpIC1Gb3JlZ3JvdW5kQ29sb3IgRGFya0dyYXkgfQ0KfQ0KDQppZiAoLW5v
>> "%B64%" echo dCAkdG9rIC1vciAtbm90ICR0b2suYWNjZXNzX3Rva2VuKSB7DQogIFNheSAiIg0KICBTYXkgIuKd
>> "%B64%" echo jCDsi5zqsIQg7JWI7JeQIOyKueyduOydtCDslYgg65CQ7Iq164uI64ukLiIgIlJlZCINCiAgU2F5
>> "%B64%" echo ICIgICDri6Tsi5wg7Iuk7ZaJ7ZW07IScIOu4jOudvOyasOyggOyXkOyEnCDtl4jsmqnsnYQg64iM
>> "%B64%" echo 65+sIOyjvOyEuOyalC4iDQogICRMaW5lcyAtam9pbiAiYHJgbiIgfCBTZXQtQ29udGVudCAtUGF0
>> "%B64%" echo aCAkTG9nUGF0aCAtRW5jb2RpbmcgVVRGOA0KICBXcml0ZS1Ib3N0ICIiOyBSZWFkLUhvc3QgIuyX
>> "%B64%" echo lO2EsOulvCDriITrpbTrqbQg64ur7Z6Z64uI64ukIiB8IE91dC1OdWxsDQogIGV4aXQgMQ0KfQ0K
>> "%B64%" echo DQokYWNjZXNzICA9IFtzdHJpbmddJHRvay5hY2Nlc3NfdG9rZW4NCiRyZWZyZXNoID0gW3N0cmlu
>> "%B64%" echo Z10kdG9rLnJlZnJlc2hfdG9rZW4NClNheSAiIg0KU2F5ICIgICDinIUg7Iq57J24IOyZhOujjCIg
>> "%B64%" echo IkdyZWVuIg0KU2F5ICgiICAg7KCR7IaNIOyXtOyHoCA6ICIgKyAoTWFzayAkYWNjZXNzKSkNClNh
>> "%B64%" echo eSAoIiAgIOqwseyLoCDsl7Tsh6AgOiAiICsgKE1hc2sgJHJlZnJlc2gpKQ0KaWYgKCR0b2suZXhw
>> "%B64%" echo aXJlc19pbikgICAgICAgICB7IFNheSAoIiAgIOygkeyGjSDsl7Tsh6Ag7IiY66qFIDogIiArICR0
>> "%B64%" echo b2suZXhwaXJlc19pbiArICLstIgiKSB9DQppZiAoJHRvay5yZWZyZXNoX2V4cGlyZXNfaW4pIHsg
>> "%B64%" echo U2F5ICgiICAg6rCx7IugIOyXtOyHoCDsiJjrqoUgOiAiICsgJHRvay5yZWZyZXNoX2V4cGlyZXNf
>> "%B64%" echo aW4gKyAi7LSIIikgfQ0KDQojIOKUgOKUgCDikaIg7Iuk7KCc66GcIOyTuCDsiJgg7J6I64qU7KeA
>> "%B64%" echo IO2ZleyduCDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIANClNheSAiIg0KU2F5ICLikaIg
>> "%B64%" echo 7Je07Ieg6rCAIOyLpOygnOuhnCDthrXtlZjripTsp4Ag7ZmV7J247ZWp64uI64ukLiINCnRyeSB7
>> "%B64%" echo DQogICR2ID0gUG9zdEpzb24gIiRBVVRIL3ZhbGlkYXRlIiBAeyB0b2tlbiA9ICRhY2Nlc3MgfQ0K
>> "%B64%" echo ICBTYXkgKCIgICDinIUg7Ya16rO8IOKAlCDqs4TsoJUg67KI7Zi4ICIgKyAkdi51c2VyX2lkKSAi
>> "%B64%" echo R3JlZW4iDQp9IGNhdGNoIHsNCiAgU2F5ICgiICAg4pqgIO2ZleyduCDtmLjstpzsnbQg7Iuk7Yyo
>> "%B64%" echo 7ZaI7Iq164uI64ukOiAiICsgJF8uRXhjZXB0aW9uLk1lc3NhZ2UpICJZZWxsb3ciDQogIFNheSAi
>> "%B64%" echo ICAg7Je07Ieg64qUIOuwm+yVmOycvOuLiCDrtpnsl6zrhKPquLDripQg7KeE7ZaJ7ZWY7IS47JqU
>> "%B64%" echo LiDsnbQg7KSE7J2AIOq3uOuMgOuhnCDslYzroKQg7KO87IS47JqULiINCn0NCg0KIyDilIDilIAg
>> "%B64%" echo 4pGjIOu2meyXrOuEo+ydhCDqsJIg4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA
>> "%B64%" echo 4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSADQppZiAoLW5vdCAkcmVmcmVzaCkgew0KICBT
>> "%B64%" echo YXkgIiINCiAgU2F5ICLinYwg6rCx7IugIOyXtOyHoOqwgCDsnZHri7Xsl5Ag7JeG7Iq164uI64uk
>> "%B64%" echo IOKAlCDsnbQg7KSE7J2EIOq3uOuMgOuhnCDslYzroKQg7KO87IS47JqULiIgIlJlZCINCiAgJExp
>> "%B64%" echo bmVzIC1qb2luICJgcmBuIiB8IFNldC1Db250ZW50IC1QYXRoICRMb2dQYXRoIC1FbmNvZGluZyBV
>> "%B64%" echo VEY4DQogIFdyaXRlLUhvc3QgIiI7IFJlYWQtSG9zdCAi7JeU7YSw66W8IOuIhOultOuptCDri6vt
>> "%B64%" echo npnri4jri6QiIHwgT3V0LU51bGwNCiAgZXhpdCAxDQp9DQoNCiMg4pqgIOqwkuunjCDtlZwg7KSE
>> "%B64%" echo 66GcIOyTtOuLpCDigJQg7YGwIOuNqeyWtOumrOyXkOyEnCDriIjsnLzroZwg7J6Y652864K06rKM
>> "%B64%" echo IO2VmOuptCDrsJjrk5zsi5wg7IKs6rOg6rCAIOuCnOuLpCjqt7jroZ0gMjYwODExIOyLpOy4oSDr
>> "%B64%" echo tIntlakpLg0KU2V0LUNvbnRlbnQgLVBhdGggJEtleVBhdGggLVZhbHVlICRyZWZyZXNoIC1FbmNv
>> "%B64%" echo ZGluZyBBU0NJSSAtTm9OZXdsaW5lDQoNClNheSAiIg0KU2F5ICIgIOKUjOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKU
>> "%B64%" echo gOKUgOKUgOKUgOKUgOKUgOKUkCIgIkdyZWVuIg0KU2F5ICIgIOKUgiAg64Gd64Ks7Iq164uI64uk
>> "%B64%" echo LiDsnbTsoJwg65GQIOqxuOydjOunjCDtlZjrqbQg65Cp64uI64ukICAgICAgICDilIIiICJHcmVl
>> "%B64%" echo biINClNheSAiICDilJTilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDi
>> "%B64%" echo lIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilJgiICJHcmVlbiIN
>> "%B64%" echo ClNheSAiIg0KU2F5ICIgIDEpIOuwlO2Dle2ZlOuptOydmCDjgIztnonsiqTtlYTrk5zsl7Tsh6Bf
>> "%B64%" echo 67aZ7Jes64Sj6riwLnR4dOOAjSDrpbwg7Je07Ja0IOyViOydmCDqsJLsnYQg7KCE67aAIOuzteyC
>> "%B64%" echo rCINClNheSAiIg0KU2F5ICIgIDIpIOq5g+2XiOu4jCDroIjtj6wg4oaSIFNldHRpbmdzIOKGkiBT
>> "%B64%" echo ZWNyZXRzIGFuZCB2YXJpYWJsZXMg4oaSIEFjdGlvbnMiDQpTYXkgKCIgICAgIOKGkiBOZXcgcmVw
>> "%B64%" echo b3NpdG9yeSBzZWNyZXQg4oaSIOydtOumhCAiICsgJFNFQ1JFVF9OQU1FICsgIiDihpIg6rCSIOu2
>> "%B64%" echo meyXrOuEo+q4sCDihpIgQWRkIHNlY3JldCIpDQpTYXkgIiINClNheSAiICDimqAg67aZ7Jes64Sj
>> "%B64%" echo 7J2AIOuSpOyXkOuKlCDrsJTtg5XtmZTrqbTsnZgg65GQIO2MjOydvOydhCDsp4DsmrDshLjsmpQo
>> "%B64%" echo 7Je07Ieg6rCAIOuLtOq4tCDtjIzsnbzsnoXri4jri6QpLiINClNheSAiICDimqAg7J20IOqwkuyd
>> "%B64%" echo gCDrgqjsl5Dqsowg7KO87KeAIOuniOyEuOyalC4g6rOE7KCVIO2BrOugiOuUp+ydhCDsk7gg7IiY
>> "%B64%" echo IOyeiOuKlCDqsJLsnoXri4jri6QuIg0KU2F5ICIiDQoNCiRMaW5lcyAtam9pbiAiYHJgbiIgfCBT
>> "%B64%" echo ZXQtQ29udGVudCAtUGF0aCAkTG9nUGF0aCAtRW5jb2RpbmcgVVRGOA0KV3JpdGUtSG9zdCAoIuq4
>> "%B64%" echo sOuhnTogIiArICRMb2dQYXRoKSAtRm9yZWdyb3VuZENvbG9yIERhcmtHcmF5DQpXcml0ZS1Ib3N0
>> "%B64%" echo ICgi7Je07IegOiAiICsgJEtleVBhdGgpIC1Gb3JlZ3JvdW5kQ29sb3IgRGFya0dyYXkNCldyaXRl
>> "%B64%" echo LUhvc3QgIiINClJlYWQtSG9zdCAi7JeU7YSw66W8IOuIhOultOuptCDri6vtnpnri4jri6QiIHwg
>> "%B64%" echo T3V0LU51bGwNCmV4aXQgMA0K
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
