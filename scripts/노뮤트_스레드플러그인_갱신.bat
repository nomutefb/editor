@echo off
REM ===========================================================================
REM  nomute - Threads yt-dlp plugin updater : ONE-CLICK
REM
REM  Replaces nomute_threads.py used by Downloader.bat with the repo version,
REM  so that threads.com/share/<code> links can be downloaded.
REM  (all Korean text lives inside the embedded ps1, never in this file -
REM   cmd reads .bat in codepage 949 and would corrupt it)
REM
REM  Run this file whenever the plugin looks outdated. Nothing stays resident.
REM  The old plugin is kept next to the new one as *.bak
REM
REM  GENERATED FILE - do not edit by hand.
REM  Source of truth: scripts/threads_plugin_update.ps1
REM  Regenerate     : python3 scripts/build_threads_plugin_bundle.py
REM ===========================================================================
setlocal
set "NM=%LOCALAPPDATA%\nomute"
if not exist "%NM%" mkdir "%NM%"
set "B64=%NM%\_thplug.b64"
if exist "%B64%" del "%B64%"

echo [1/2] Unpacking updater...
>> "%B64%" echo 77u/IyDsiqTroIjrk5wg7ZSM65+s6re47J24IOqwseyLoOq4sCDigJQgUEMg64uk7Jq066Gc642U
>> "%B64%" echo KERvd25sb2FkZXIuYmF0KeqwgCDsnb3ripQgbm9tdXRlX3RocmVhZHMucHkg66W8IOq5g+2XiOu4
>> "%B64%" echo jCDsoJXrs7jsnLzroZwg6rWQ7LK0LgojCiMg7JmcIC5wczEg7J246rCAOiBjbWQg64qUIC5iYXQg
>> "%B64%" echo 7J2EIE9FTSDsvZTrk5ztjpjsnbTsp4AoOTQ5KeuhnCDsnb3slrQg7ZWc6riA7J20IOuwmOuTnOyL
>> "%B64%" echo nCDquajsp4Tri6QoMjYwODA0IOyLpOyCrOqzoCDigJQKIyAgIOyatOyYgeyekCDtmZTrqbTsl5Ag
>> "%B64%" echo IidmaW5lZCfsnYAo64qUKSDrgrTrtoAg65iQ64qUIOyZuOu2gCDrqoXroLnsnbQg7JWE64uZ64uI
>> "%B64%" echo 64ukIiDqsIAg7KSE7KSE7J20IOuWtOuLpCkuCiMgICDihpIg66CI7Y+sIOygleuzuCDrsKnsi50o
>> "%B64%" echo YnVpbGRfZHJpdmVfbW92ZV9idW5kbGUucHkpIOq3uOuMgOuhnDog7ZWc6riA7J2AIOyghOu2gCDs
>> "%B64%" echo nbQgcHMxIOyViOyXkCDrkZDqs6AsCiMgICAgIC5iYXQg7J2AIGJhc2U2NCDtjpjsnbTroZzrk5zr
>> "%B64%" echo p4wg7Iuk7J2AIOyInOyImCBBU0NJSSDroZwg66eM65Og64ukLgojCiMg64GE64qUIOuylTog6re4
>> "%B64%" echo 64OlIOyViCDrj4zrpqzrqbQg65Cc64ukKOyDgeyjvO2VmOuKlCDqsoMg7JeG7J2MKS4g66Gc6re4
>> "%B64%" echo ID0g7J20IOywvSDstpzroKUuCgokRXJyb3JBY3Rpb25QcmVmZXJlbmNlID0gJ1N0b3AnCiRSQVcg
>> "%B64%" echo PSAnaHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL25vbXV0ZWZiL2VkaXRvci9tYWlu
>> "%B64%" echo L2FwcHMvdmlkbC9wbHVnaW5zL3l0X2RscF9wbHVnaW5zL2V4dHJhY3Rvci9ub211dGVfdGhyZWFk
>> "%B64%" echo cy5weScKCmZ1bmN0aW9uIFNheSgkbSkgeyBXcml0ZS1Ib3N0ICIgICRtIiB9CgpXcml0ZS1Ib3N0
>> "%B64%" echo ICcnCldyaXRlLUhvc3QgJyAgW+yKpOugiOuTnCDtlIzrn6zqt7jsnbgg6rCx7IugXScKV3JpdGUt
>> "%B64%" echo SG9zdCAnJwoKIyDilIDilIAg4pGgIHl0LWRscCDtj7TrjZQg7LC+6riwIOKAlCDqs6DsoJUg6rK9
>> "%B64%" echo 66GcIOuovOyggCwg7JeG7Jy866m0IE9uZURyaXZlIOyVhOuemOyXkOyEnCB5dC1kbHAuZXhlIOul
>> "%B64%" echo vCDsi6TsoJzroZwg6rKA7IOJIOKUgOKUgAokY2FuZHMgPSBAKCkKZm9yZWFjaCAoJGJhc2UgaW4g
>> "%B64%" echo QCgkZW52Ok9uZURyaXZlQ29tbWVyY2lhbCwgJGVudjpPbmVEcml2ZSkpIHsKICBpZiAoJGJhc2Up
>> "%B64%" echo IHsgJGNhbmRzICs9IChKb2luLVBhdGggJGJhc2UgJ+2ZqeyEuOybhVw2LiAgTm9tdXRlXOywveqz
>> "%B64%" echo oFwwNS4gVXRpbGl0eVx5dC1kbHAnKSB9Cn0KJGNhbmRzICs9IChKb2luLVBhdGggJGVudjpVU0VS
>> "%B64%" echo UFJPRklMRSAnRG93bmxvYWRzXHl0LWRscCcpCgokeXRkbHAgPSAkbnVsbApmb3JlYWNoICgkYyBp
>> "%B64%" echo biAkY2FuZHMpIHsgaWYgKFRlc3QtUGF0aCAtTGl0ZXJhbFBhdGggJGMpIHsgJHl0ZGxwID0gJGM7
>> "%B64%" echo IGJyZWFrIH0gfQoKaWYgKC1ub3QgJHl0ZGxwKSB7CiAgU2F5ICfqs6DsoJUg6rK966Gc7JeQIOyX
>> "%B64%" echo huyWtOyEnCBPbmVEcml2ZSDslYjsnYQg7LC+64qUIOykkS4uLicKICBmb3JlYWNoICgkYmFzZSBp
>> "%B64%" echo biBAKCRlbnY6T25lRHJpdmVDb21tZXJjaWFsLCAkZW52Ok9uZURyaXZlKSkgewogICAgaWYgKC1u
>> "%B64%" echo b3QgJGJhc2UpIHsgY29udGludWUgfQogICAgJGhpdCA9IEdldC1DaGlsZEl0ZW0gLUxpdGVyYWxQ
>> "%B64%" echo YXRoICRiYXNlIC1GaWx0ZXIgJ3l0LWRscC5leGUnIC1SZWN1cnNlIC1GaWxlIC1FcnJvckFjdGlv
>> "%B64%" echo biBTaWxlbnRseUNvbnRpbnVlIHwKICAgICAgICAgICBTZWxlY3QtT2JqZWN0IC1GaXJzdCAxCiAg
>> "%B64%" echo ICBpZiAoJGhpdCkgeyAkeXRkbHAgPSAkaGl0LkRpcmVjdG9yeS5GdWxsTmFtZTsgYnJlYWsgfQog
>> "%B64%" echo IH0KfQoKaWYgKC1ub3QgJHl0ZGxwKSB7CiAgU2F5ICdb7Iuk7YyoXSB5dC1kbHAg7Y+0642U66W8
>> "%B64%" echo IOuquyDssL7slZjslrTsmpQuJwogIFNheSAnICAgICAgIE9uZURyaXZlIOuPmeq4sO2ZlOqwgCDs
>> "%B64%" echo vJzsoLgg7J6I64qU7KeAIO2ZleyduO2VmOqzoCDri6Tsi5wg7Iuk7ZaJ7ZW0IOyjvOyEuOyalC4n
>> "%B64%" echo CiAgcmV0dXJuCn0KU2F5ICJ5dC1kbHAg7Y+0642UOiAkeXRkbHAiCgojIOKUgOKUgCDikaEg6riw
>> "%B64%" echo 7KG0IO2UjOufrOq3uOyduCDsnITsuZgo7ZWY7JyEIOyWtOuUlOyXkCDsnojrk6ApIOKUgOKUgAok
>> "%B64%" echo dGFyZ2V0ID0gR2V0LUNoaWxkSXRlbSAtTGl0ZXJhbFBhdGggJHl0ZGxwIC1GaWx0ZXIgJ25vbXV0
>> "%B64%" echo ZV90aHJlYWRzLnB5JyAtUmVjdXJzZSAtRmlsZSAtRXJyb3JBY3Rpb24gU2lsZW50bHlDb250aW51
>> "%B64%" echo ZSB8CiAgICAgICAgICBTZWxlY3QtT2JqZWN0IC1GaXJzdCAxIC1FeHBhbmRQcm9wZXJ0eSBGdWxs
>> "%B64%" echo TmFtZQoKZnVuY3Rpb24gR2V0LVZlcigkcGF0aCkgewogIGlmICgtbm90IChUZXN0LVBhdGggLUxp
>> "%B64%" echo dGVyYWxQYXRoICRwYXRoKSkgeyByZXR1cm4gJyjsl4bsnYwpJyB9CiAgJG0gPSBbcmVnZXhdOjpN
>> "%B64%" echo YXRjaCgoR2V0LUNvbnRlbnQgLUxpdGVyYWxQYXRoICRwYXRoIC1SYXcpLCAiX192ZXJzaW9uX19c
>> "%B64%" echo cyo9XHMqJyhbXiddKyknIikKICBpZiAoJG0uU3VjY2VzcykgeyByZXR1cm4gJG0uR3JvdXBzWzFd
>> "%B64%" echo LlZhbHVlIH0gZWxzZSB7IHJldHVybiAnKOuyhOyghCDtkZzquLAg7JeG7J2MKScgfQp9CgppZiAo
>> "%B64%" echo JHRhcmdldCkgewogIFNheSAi6riw7KG0IO2MjOydvDogJHRhcmdldCIKICBTYXkgIu2YhOyerCDr
>> "%B64%" echo soTsoIQ6ICQoR2V0LVZlciAkdGFyZ2V0KSIKfSBlbHNlIHsKICAjIHl0LWRscCDripQg7Iuk7ZaJ
>> "%B64%" echo 7YyM7J28IOyYhiB5dC1kbHAtcGx1Z2lucy8qL3l0X2RscF9wbHVnaW5zL2V4dHJhY3Rvci8qLnB5
>> "%B64%" echo IOulvCDsnpDrj5nsnLzroZwg7J2964qU64ukCiAgJHRhcmdldCA9IEpvaW4tUGF0aCAkeXRkbHAg
>> "%B64%" echo J3l0LWRscC1wbHVnaW5zXG5vbXV0ZVx5dF9kbHBfcGx1Z2luc1xleHRyYWN0b3Jcbm9tdXRlX3Ro
>> "%B64%" echo cmVhZHMucHknCiAgU2F5ICLquLDsobQg7YyM7J287J20IOyXhuyWtCDsg4jroZwg7ISk7LmY7ZWp
>> "%B64%" echo 64uI64ukOiAkdGFyZ2V0Igp9CiRkaXIgPSBTcGxpdC1QYXRoIC1QYXJlbnQgJHRhcmdldAppZiAo
>> "%B64%" echo LW5vdCAoVGVzdC1QYXRoIC1MaXRlcmFsUGF0aCAkZGlyKSkgeyBOZXctSXRlbSAtSXRlbVR5cGUg
>> "%B64%" echo RGlyZWN0b3J5IC1QYXRoICRkaXIgLUZvcmNlIHwgT3V0LU51bGwgfQoKIyDilIDilIAg4pGiIOyg
>> "%B64%" echo leuzuCDsiJjsi6Ag4oaSIOqygOymnSDihpIg6rWQ7LK0KOyehOyLnO2MjOydvCDqsr3snKDrnbwg
>> "%B64%" echo 7Iuk7Yyo7ZW064+EIOq4sOyhtCDtjIzsnbwg66y07IaQ7IOBKSDilIDilIAKU2F5ICfquYPtl4jr
>> "%B64%" echo uIwg7KCV67O4IOuwm+uKlCDspJEuLi4nCiR0bXAgPSBKb2luLVBhdGggJGVudjpURU1QICdub211
>> "%B64%" echo dGVfdGhyZWFkcy5uZXcucHknCnRyeSB7CiAgW05ldC5TZXJ2aWNlUG9pbnRNYW5hZ2VyXTo6U2Vj
>> "%B64%" echo dXJpdHlQcm90b2NvbCA9IFtOZXQuU2VjdXJpdHlQcm90b2NvbFR5cGVdOjpUbHMxMgogIEludm9r
>> "%B64%" echo ZS1XZWJSZXF1ZXN0IC1VcmkgJFJBVyAtT3V0RmlsZSAkdG1wIC1Vc2VCYXNpY1BhcnNpbmcKfSBj
>> "%B64%" echo YXRjaCB7CiAgU2F5ICdb7Iuk7YyoXSDrgrTroKTrsJvquLAg7Iuk7YyoIOKAlCDsnbjthLDrhLcg
>> "%B64%" echo 7Jew6rKw7J2EIO2ZleyduO2VtCDso7zshLjsmpQuIOq4sOyhtCDtjIzsnbzsnYAg6re464yA66Gc
>> "%B64%" echo 7J6F64uI64ukLicKICByZXR1cm4KfQoKaWYgKChHZXQtQ29udGVudCAtTGl0ZXJhbFBhdGggJHRt
>> "%B64%" echo cCAtUmF3KSAtbm90bWF0Y2ggJ05vbXV0ZVRocmVhZHNJRScpIHsKICBTYXkgJ1vsi6TtjKhdIOuw
>> "%B64%" echo m+ydgCDtjIzsnbzsnbQg7ZSM65+s6re47J247J20IOyVhOuLmeuLiOuLpCjsmKTrpZgg7Y6Y7J20
>> "%B64%" echo 7KeAIOy2lOyglSkuIOq4sOyhtCDtjIzsnbzsnYAg6re464yA66Gc7J6F64uI64ukLicKICBSZW1v
>> "%B64%" echo dmUtSXRlbSAtTGl0ZXJhbFBhdGggJHRtcCAtRm9yY2UgLUVycm9yQWN0aW9uIFNpbGVudGx5Q29u
>> "%B64%" echo dGludWUKICByZXR1cm4KfQoKaWYgKFRlc3QtUGF0aCAtTGl0ZXJhbFBhdGggJHRhcmdldCkgeyBD
>> "%B64%" echo b3B5LUl0ZW0gLUxpdGVyYWxQYXRoICR0YXJnZXQgLURlc3RpbmF0aW9uICIkdGFyZ2V0LmJhayIg
>> "%B64%" echo LUZvcmNlIH0KQ29weS1JdGVtIC1MaXRlcmFsUGF0aCAkdG1wIC1EZXN0aW5hdGlvbiAkdGFyZ2V0
>> "%B64%" echo IC1Gb3JjZQpSZW1vdmUtSXRlbSAtTGl0ZXJhbFBhdGggJHRtcCAtRm9yY2UgLUVycm9yQWN0aW9u
>> "%B64%" echo IFNpbGVudGx5Q29udGludWUKCldyaXRlLUhvc3QgJycKU2F5ICJb7JmE66OMXSDqsLHsi6DrkKgg
>> "%B64%" echo 4oCUIOyDiCDrsoTsoIQ6ICQoR2V0LVZlciAkdGFyZ2V0KSIKU2F5ICcgICAgICAg7JibIO2MjOyd
>> "%B64%" echo vOydgCDqsJnsnYAg7Y+0642U7JeQIC5iYWsg7Jy866GcIOuCqOqyqOuSgOyWtOyalC4nCldyaXRl
>> "%B64%" echo LUhvc3QgJycKU2F5ICfsnbTsoJwgRG93bmxvYWRlci5iYXQg7JeQIHRocmVhZHMuY29tL3NoYXJl
>> "%B64%" echo Ly4uLiDso7zshozrpbwg64Sj7Ja064+EIOuwm+yVhOynkeuLiOuLpC4nCg==
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$t=[IO.File]::ReadAllText($env:B64); [IO.File]::WriteAllBytes((Join-Path $env:NM 'threads_plugin_update.ps1'), [Convert]::FromBase64String(($t -replace '\s','')))"
if errorlevel 1 goto :fail
del "%B64%" >nul 2>&1

echo [2/2] Updating plugin...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%NM%\threads_plugin_update.ps1"
if errorlevel 1 goto :fail

echo.
pause
exit /b 0

:fail
echo.
echo   UPDATE FAILED - please send the lines above.
echo.
pause
exit /b 1
