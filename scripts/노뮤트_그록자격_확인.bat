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
>> "%B64%" echo IOuBhOuKlCDrspU6IOyViCDrj4zrpqzrqbQg64GdLiDshKTsuZjrkJjripQg6rKD64+ELCDsnpDr
>> "%B64%" echo j5kg7Iuk7ZaJ65CY64qUIOqyg+uPhCDsl4bri6QuDQoNCiRFcnJvckFjdGlvblByZWZlcmVuY2Ug
>> "%B64%" echo PSAiU3RvcCINCnRyeSB7IFtOZXQuU2VydmljZVBvaW50TWFuYWdlcl06OlNlY3VyaXR5UHJvdG9j
>> "%B64%" echo b2wgPSBbTmV0LlNlY3VyaXR5UHJvdG9jb2xUeXBlXTo6VGxzMTIgfSBjYXRjaCB7fQ0KdHJ5IHsg
>> "%B64%" echo JE91dHB1dEVuY29kaW5nID0gW0NvbnNvbGVdOjpPdXRwdXRFbmNvZGluZyA9IFtUZXh0LkVuY29k
>> "%B64%" echo aW5nXTo6VVRGOCB9IGNhdGNoIHt9DQoNCiRDTElFTlRfSUQgPSAiYjFhMDA0OTItMDczYS00N2Vh
>> "%B64%" echo LTgxNmYtNGMzMjkyNjRhODI4IiAgICMgeEFJIOqzteqwnCDrjbDsiqTtgazthrEg7YG065287J20
>> "%B64%" echo 7Ja47Yq4KOu5hOuwgO2CpCDsl4bsnYwpDQokU0NPUEUgICAgID0gIm9wZW5pZCBwcm9maWxlIGVt
>> "%B64%" echo YWlsIG9mZmxpbmVfYWNjZXNzIGdyb2stY2xpOmFjY2VzcyBhcGk6YWNjZXNzIg0KJERJU0NPVkVS
>> "%B64%" echo WSA9ICJodHRwczovL2F1dGgueC5haS8ud2VsbC1rbm93bi9vcGVuaWQtY29uZmlndXJhdGlvbiIN
>> "%B64%" echo CiRBUElfQkFTRSAgPSAiaHR0cHM6Ly9hcGkueC5haS92MSINCiRNT0RFTFMgICAgPSBAKCJncm9r
>> "%B64%" echo LTQuNSIsImdyb2stNC4zIiwiZ3Jvay0zIiwiZ3Jvay1iZXRhIikNCg0KIyDimqAg67CU7YOV7ZmU
>> "%B64%" echo 66m0IOqyveuhnOuKlCDruYgg66y47J6Q7Je066GcIOyYrCDsiJgg7J6I64ukKOybkOuTnOudvOyd
>> "%B64%" echo tOu4jCDrsLHsl4XCt+u5hOyciOuPhOyasCDtmZjqsr0g7Iuk7LihKSDihpIg7Y+067CxIOyCrOyK
>> "%B64%" echo rC4NCiMgICDtlZwg7Lm47J20652864+EIOu5hOuptCBKb2luLVBhdGgg6rCAIOq3uCDsnpDrpqzs
>> "%B64%" echo l5DshJwg7KO97Ja0IO2MkOyglSDsnpDssrTrpbwg66q7IO2VnOuLpCjssqsg7Iuk7ZaJIOyLpOy4
>> "%B64%" echo oSDrtIntlakpLg0KJERlc2sgPSAiIg0KIyAo4pqgIEpvaW4tUGF0aCDripQg67mIIOqwkuydhCDr
>> "%B64%" echo sJvsnLzrqbQg6re4IOyekOumrOyXkOyEnCDso73ripTri6QgPSDtj7TrsLHsnbQg7Y+067CxIOyg
>> "%B64%" echo hOyXkCDthLDsp4Tri6Qg4oaSIOusuOyekOyXtOuhnOunjCDsnofripTri6QpDQpmb3JlYWNoICgk
>> "%B64%" echo YyBpbiBAKFtFbnZpcm9ubWVudF06OkdldEZvbGRlclBhdGgoIkRlc2t0b3AiKSwNCiAgICAgICAg
>> "%B64%" echo ICAgICAgICAgIiRlbnY6VVNFUlBST0ZJTEVcRGVza3RvcCIsICIkZW52OlVTRVJQUk9GSUxFIiwg
>> "%B64%" echo IiRlbnY6VEVNUCIsIChHZXQtTG9jYXRpb24pLlBhdGgpKSB7DQogIGlmICgkYyAtYW5kICRjLlRy
>> "%B64%" echo aW0oKSAtYW5kIChUZXN0LVBhdGggLUxpdGVyYWxQYXRoICRjKSkgeyAkRGVzayA9ICRjOyBicmVh
>> "%B64%" echo ayB9DQp9DQppZiAoLW5vdCAkRGVzaykgeyAkRGVzayA9ICIuIiB9DQokTG9nUGF0aCAgID0gSm9p
>> "%B64%" echo bi1QYXRoICREZXNrICLqt7jroZ3tmZXsnbhf6rKw6rO8LnR4dCINCiRUb2tlblBhdGggPSBKb2lu
>> "%B64%" echo LVBhdGggJERlc2sgIuq3uOuhne2GoO2BsC5qc29uIg0KJHNjcmlwdDpMb2cgPSBOZXctT2JqZWN0
>> "%B64%" echo IFN5c3RlbS5Db2xsZWN0aW9ucy5BcnJheUxpc3QNCg0KZnVuY3Rpb24gU2F5KCR0KSB7IFdyaXRl
>> "%B64%" echo LUhvc3QgJHQ7IFt2b2lkXSRzY3JpcHQ6TG9nLkFkZCgkdCkgfQ0KZnVuY3Rpb24gTWFzaygkcykg
>> "%B64%" echo eyBpZiAoJHMgLWFuZCAkcy5MZW5ndGggLWd0IDEyKSB7ICRzLlN1YnN0cmluZygwLDEyKSArICLi
>> "%B64%" echo gKY8IiArICRzLkxlbmd0aCArICLsnpAg6rCA66a8PiIgfSBlbHNlIHsgJHMgfSB9DQpmdW5jdGlv
>> "%B64%" echo biBTYXZlTG9nIHsgdHJ5IHsgJHNjcmlwdDpMb2cgLWpvaW4gImByYG4iIHwgT3V0LUZpbGUgLUZp
>> "%B64%" echo bGVQYXRoICRMb2dQYXRoIC1FbmNvZGluZyBVVEY4IH0gY2F0Y2gge30gfQ0KDQojIOyDge2DnOy9
>> "%B64%" echo lOuTnOq5jOyngCDrsJvslYTsmKTripQg7JqU7LKt6riwKO2MjOybjOyFuCA1LjEg7JeQ7ISgIOyL
>> "%B64%" echo pO2MqCDsnZHri7Ug67O466y47J2EIOyngeygkSDsnb3slrTslbwg7ZWc64ukKQ0KZnVuY3Rpb24g
>> "%B64%" echo V2ViKCR1cmwsICRib2R5LCAkdG9rZW4sICRtZXRob2QpIHsNCiAgJGggPSBAe30NCiAgaWYgKCR0
>> "%B64%" echo b2tlbikgeyAkaFsiQXV0aG9yaXphdGlvbiJdID0gIkJlYXJlciAkdG9rZW4iIH0NCiAgJHAgPSBA
>> "%B64%" echo eyBVcmkgPSAkdXJsOyBIZWFkZXJzID0gJGg7IFRpbWVvdXRTZWMgPSA5MDsgVXNlQmFzaWNQYXJz
>> "%B64%" echo aW5nID0gJHRydWUgfQ0KICBpZiAoJG1ldGhvZCkgeyAkcFsiTWV0aG9kIl0gPSAkbWV0aG9kIH0g
>> "%B64%" echo ZWxzZWlmICgkYm9keSkgeyAkcFsiTWV0aG9kIl0gPSAiUE9TVCIgfSBlbHNlIHsgJHBbIk1ldGhv
>> "%B64%" echo ZCJdID0gIkdFVCIgfQ0KICBpZiAoJGJvZHkgLWlzIFtoYXNodGFibGVdKSB7ICRwWyJCb2R5Il0g
>> "%B64%" echo PSAkYm9keTsgJHBbIkNvbnRlbnRUeXBlIl0gPSAiYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxl
>> "%B64%" echo bmNvZGVkIiB9DQogIGVsc2VpZiAoJGJvZHkpIHsgJHBbIkJvZHkiXSA9IFtUZXh0LkVuY29kaW5n
>> "%B64%" echo XTo6VVRGOC5HZXRCeXRlcygkYm9keSk7ICRwWyJDb250ZW50VHlwZSJdID0gImFwcGxpY2F0aW9u
>> "%B64%" echo L2pzb24iIH0NCiAgdHJ5IHsNCiAgICAkciA9IEludm9rZS1XZWJSZXF1ZXN0IEBwDQogICAgJHR4
>> "%B64%" echo dCA9ICRyLkNvbnRlbnQNCiAgICAkb2JqID0gJG51bGw7IHRyeSB7ICRvYmogPSAkdHh0IHwgQ29u
>> "%B64%" echo dmVydEZyb20tSnNvbiB9IGNhdGNoIHt9DQogICAgcmV0dXJuIEB7IGNvZGUgPSBbaW50XSRyLlN0
>> "%B64%" echo YXR1c0NvZGU7IHRleHQgPSAkdHh0OyBvYmogPSAkb2JqIH0NCiAgfSBjYXRjaCB7DQogICAgIyDi
>> "%B64%" echo mqAg7YyM7JuM7IW4IDUuMSDqs7wgNyDsnbQg7Iuk7YyoIOydkeuLteydhCDri6TrpbTqsowg64SY
>> "%B64%" echo 6ri064ukIOKAlCA1LjHsnYAgUmVzcG9uc2Ug7Iqk7Yq466a8LCA37J2AIEVycm9yRGV0YWlscy4N
>> "%B64%" echo CiAgICAjICAg7ZWc7Kq966eMIOydveycvOuptCAi7ISc67KE6rCAIOutkOudvOqzoCDqsbDsoIjt
>> "%B64%" echo lojripTsp4Ai6rCAIO2GteynuOuhnCDsgqzrnbzsp4Tri6QoPSDsnbQg7YyQ7KCV6riw7J2YIOyh
>> "%B64%" echo tOyerCDsnbTsnKDqsIAg7IKs65287KeE64ukKS4NCiAgICAkY29kZSA9IDA7ICR0eHQgPSAiJCgk
>> "%B64%" echo Xy5FeGNlcHRpb24uTWVzc2FnZSkiDQogICAgdHJ5IHsgaWYgKCRfLkVycm9yRGV0YWlscyAtYW5k
>> "%B64%" echo ICRfLkVycm9yRGV0YWlscy5NZXNzYWdlKSB7ICR0eHQgPSAkXy5FcnJvckRldGFpbHMuTWVzc2Fn
>> "%B64%" echo ZSB9IH0gY2F0Y2gge30NCiAgICAkcmVzcCA9ICRudWxsDQogICAgdHJ5IHsgJHJlc3AgPSAkXy5F
>> "%B64%" echo eGNlcHRpb24uUmVzcG9uc2UgfSBjYXRjaCB7fQ0KICAgIGlmICgkcmVzcCkgew0KICAgICAgdHJ5
>> "%B64%" echo IHsgJGNvZGUgPSBbaW50XSRyZXNwLlN0YXR1c0NvZGUgfSBjYXRjaCB7fQ0KICAgICAgaWYgKCR0
>> "%B64%" echo eHQgLWVxICIkKCRfLkV4Y2VwdGlvbi5NZXNzYWdlKSIpIHsNCiAgICAgICAgdHJ5IHsNCiAgICAg
>> "%B64%" echo ICAgICAkc3IgPSBOZXctT2JqZWN0IElPLlN0cmVhbVJlYWRlcigkcmVzcC5HZXRSZXNwb25zZVN0
>> "%B64%" echo cmVhbSgpKQ0KICAgICAgICAgICR0eHQgPSAkc3IuUmVhZFRvRW5kKCk7ICRzci5DbG9zZSgpDQog
>> "%B64%" echo ICAgICAgIH0gY2F0Y2gge30NCiAgICAgIH0NCiAgICB9DQogICAgJG9iaiA9ICRudWxsOyB0cnkg
>> "%B64%" echo eyAkb2JqID0gJHR4dCB8IENvbnZlcnRGcm9tLUpzb24gfSBjYXRjaCB7fQ0KICAgIHJldHVybiBA
>> "%B64%" echo eyBjb2RlID0gJGNvZGU7IHRleHQgPSAkdHh0OyBvYmogPSAkb2JqIH0NCiAgfQ0KfQ0KDQpmdW5j
>> "%B64%" echo dGlvbiBTdG9wLUJhZCgkdGl0bGUsICRkZXRhaWwsICRoaW50KSB7DQogIFNheSAiIg0KICBTYXkg
>> "%B64%" echo KCI9IiAqIDU4KQ0KICBTYXkgIltYXSAkdGl0bGUiDQogIFNheSAoIj0iICogNTgpDQogIFNheSAk
>> "%B64%" echo ZGV0YWlsDQogIGlmICgkaGludCkgeyBTYXkgIiI7IFNheSAkaGludCB9DQogIFNheSAiIg0KICBT
>> "%B64%" echo YXkgIuq4sOuhnTogJExvZ1BhdGgiDQogIFNhdmVMb2cNCiAgV3JpdGUtSG9zdCAiIg0KICBSZWFk
>> "%B64%" echo LUhvc3QgIuyXlO2EsOulvCDriITrpbTrqbQg7LC97J20IOuLq+2ejOuLpCINCiAgZXhpdCAxDQp9
>> "%B64%" echo DQoNClNheSAiIg0KU2F5ICIrLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
>> "%B64%" echo LS0tLS0tLS0tLS0tLS0tLS0tLSsiDQpTYXkgInwg6re466GdIOq1rOuPhSDsnpDqsqkg7YyQ7KCV
>> "%B64%" echo 6riwIC0g66Gc6re47J24IDHtmowgKyDsi6TsoJwg7Zi47LacIDHtmowgICAgICAgIHwiDQpTYXkg
>> "%B64%" echo IistLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t
>> "%B64%" echo LS0tKyINClNheSAiIg0KDQojICgxKSDsl5Trk5ztj6zsnbjtirjripQg7ZWY65Oc7L2U65SpIOuM
>> "%B64%" echo gOyLoCB4QUkg6rCAIOyVjOugpOyjvOuKlCDqsJLsnYQg7JO064ukKOyjvOyGjOqwgCDrsJTrgIzs
>> "%B64%" echo lrTrj4Qg65Sw65286rCE64ukKQ0KJHIgPSBXZWIgJERJU0NPVkVSWSAkbnVsbCAkbnVsbCAiR0VU
>> "%B64%" echo Ig0KaWYgKCRyLmNvZGUgLW5lIDIwMCAtb3IgLW5vdCAkci5vYmopIHsNCiAgU3RvcC1CYWQgIuyd
>> "%B64%" echo uOymnSDshJzrsoQg7KCV67O066W8IOuquyDrsJvslZjri6QiICJIVFRQICQoJHIuY29kZSlgcmBu
>> "%B64%" echo JCgkci50ZXh0KSIgIuyduO2EsOuEt+ydtOuCmCDtmozsgqwg67Cp7ZmU67K9IOusuOygnOydvCDs
>> "%B64%" echo iJgg7J6I64ukLiDruIzrnbzsmrDsoIDroZwgJERJU0NPVkVSWSDqsIAg7Je066as64qU7KeAIO2Z
>> "%B64%" echo leyduO2VtOu0kOudvC4iDQp9DQokZGV2VXJsID0gJHIub2JqLmRldmljZV9hdXRob3JpemF0aW9u
>> "%B64%" echo X2VuZHBvaW50DQokdG9rVXJsID0gJHIub2JqLnRva2VuX2VuZHBvaW50DQokd2hvVXJsID0gJHIu
>> "%B64%" echo b2JqLnVzZXJpbmZvX2VuZHBvaW50DQppZiAoLW5vdCAkZGV2VXJsIC1vciAtbm90ICR0b2tVcmwp
>> "%B64%" echo IHsgU3RvcC1CYWQgIuydtCDshJzrsoTripQg7L2U65OcIOyKueyduCDrsKnsi53snYQg7JWIIOuw
>> "%B64%" echo m+uKlOuLpCIgJHIudGV4dCAiIiB9DQpTYXkgIiAg7J247KadIOyEnOuyhCDtmZXsnbgg7JmE66OM
>> "%B64%" echo Ig0KDQojICgyKSDsvZTrk5wg67Cc6riJDQokciA9IFdlYiAkZGV2VXJsIEB7IGNsaWVudF9pZCA9
>> "%B64%" echo ICRDTElFTlRfSUQ7IHNjb3BlID0gJFNDT1BFIH0gJG51bGwgIlBPU1QiDQppZiAoJHIuY29kZSAt
>> "%B64%" echo bmUgMjAwIC1vciAtbm90ICRyLm9iai51c2VyX2NvZGUpIHsNCiAgU3RvcC1CYWQgIuuhnOq3uOyd
>> "%B64%" echo uCDsvZTrk5wg67Cc6riJ7J20IOqxsOygiOuQkOuLpCIgIkhUVFAgJCgkci5jb2RlKWByYG4kKCRy
>> "%B64%" echo LnRleHQpIiAi7J6g7IucIOuSpCDri6Tsi5wg7Iuk7ZaJ7ZW067SQ6528LiINCn0NCiRkZXYgICAg
>> "%B64%" echo ICA9ICRyLm9iag0KJHZlcmlmeSAgID0gaWYgKCRkZXYudmVyaWZpY2F0aW9uX3VyaV9jb21wbGV0
>> "%B64%" echo ZSkgeyAkZGV2LnZlcmlmaWNhdGlvbl91cmlfY29tcGxldGUgfSBlbHNlIHsgJGRldi52ZXJpZmlj
>> "%B64%" echo YXRpb25fdXJpIH0NCiRpbnRlcnZhbCA9IGlmICgkZGV2LmludGVydmFsKSB7IFtpbnRdJGRldi5p
>> "%B64%" echo bnRlcnZhbCB9IGVsc2UgeyA1IH0NCiRleHBpcmVzICA9IGlmICgkZGV2LmV4cGlyZXNfaW4pIHsg
>> "%B64%" echo W2ludF0kZGV2LmV4cGlyZXNfaW4gfSBlbHNlIHsgOTAwIH0NCg0KU2F5ICIiDQpTYXkgIiAgKy0t
>> "%B64%" echo LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSsiDQpT
>> "%B64%" echo YXkgIiAgfCDruIzrnbzsmrDsoIDqsIAg7Je066aw64ukLiDroZzqt7jsnbjtlZjqs6AgW+yKueyd
>> "%B64%" echo uF0g64iE66W066m0IOuBneydtOuLpC4gICB8Ig0KU2F5ICIgICstLS0tLS0tLS0tLS0tLS0tLS0t
>> "%B64%" echo LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0rIg0KU2F5ICIiDQpTYXkgIiAgICDs
>> "%B64%" echo o7zshowgOiAkdmVyaWZ5Ig0KU2F5ICIgICAg7L2U65OcIDogJCgkZGV2LnVzZXJfY29kZSkiDQpT
>> "%B64%" echo YXkgIiINClNheSAiICAo7KCc7ZWcIOyLnOqwhCAkKFtpbnRdKCRleHBpcmVzLzYwKSnrtoQgwrcg
>> "%B64%" echo 7Iq57J247ZWY66m0IOyXrOq4sOyEnCDsnpDrj5nsnLzroZwg64SY7Ja06rCE64ukKSINClNheSAi
>> "%B64%" echo Ig0KdHJ5IHsgU3RhcnQtUHJvY2VzcyAkdmVyaWZ5IH0gY2F0Y2ggeyBTYXkgIiAgKOu4jOudvOya
>> "%B64%" echo sOyggCDsnpDrj5kg7Je06riwIOyLpO2MqCAtIOychCDso7zshozrpbwg7KeB7KCRIOyXtOyWtOud
>> "%B64%" echo vCkiIH0NCg0KIyAoMykg7Iq57J24IOuMgOq4sA0KJGRlYWRsaW5lID0gKEdldC1EYXRlKS5BZGRT
>> "%B64%" echo ZWNvbmRzKCRleHBpcmVzKQ0KJHRva2VucyA9ICRudWxsDQokd2FpdGVkID0gMA0Kd2hpbGUgKChH
>> "%B64%" echo ZXQtRGF0ZSkgLWx0ICRkZWFkbGluZSkgew0KICBTdGFydC1TbGVlcCAtU2Vjb25kcyAkaW50ZXJ2
>> "%B64%" echo YWwNCiAgJHdhaXRlZCArPSAkaW50ZXJ2YWwNCiAgJHIgPSBXZWIgJHRva1VybCBAeyBjbGllbnRf
>> "%B64%" echo aWQgPSAkQ0xJRU5UX0lEOyBkZXZpY2VfY29kZSA9ICRkZXYuZGV2aWNlX2NvZGU7IGdyYW50X3R5
>> "%B64%" echo cGUgPSAidXJuOmlldGY6cGFyYW1zOm9hdXRoOmdyYW50LXR5cGU6ZGV2aWNlX2NvZGUiIH0gJG51
>> "%B64%" echo bGwgIlBPU1QiDQogIGlmICgkci5jb2RlIC1lcSAyMDAgLWFuZCAkci5vYmouYWNjZXNzX3Rva2Vu
>> "%B64%" echo KSB7ICR0b2tlbnMgPSAkci5vYmo7IGJyZWFrIH0NCiAgJGVyciA9ICRudWxsOyB0cnkgeyAkZXJy
>> "%B64%" echo ID0gJHIub2JqLmVycm9yIH0gY2F0Y2gge30NCiAgaWYgKCRlcnIgLWVxICJhdXRob3JpemF0aW9u
>> "%B64%" echo X3BlbmRpbmciKSB7IGlmICgkd2FpdGVkICUgMzAgLWx0ICRpbnRlcnZhbCkgeyBTYXkgIiAgLi4u
>> "%B64%" echo IOyKueyduCDquLDri6TrpqzripQg7KSRICgkd2FpdGVkIOy0iCkiIH07IGNvbnRpbnVlIH0NCiAg
>> "%B64%" echo aWYgKCRlcnIgLWVxICJzbG93X2Rvd24iKSB7ICRpbnRlcnZhbCArPSA1OyBjb250aW51ZSB9DQog
>> "%B64%" echo IGlmICgkZXJyIC1lcSAiZXhwaXJlZF90b2tlbiIgLW9yICRlcnIgLWVxICJhY2Nlc3NfZGVuaWVk
>> "%B64%" echo Iikgew0KICAgIFN0b3AtQmFkICLroZzqt7jsnbjsnbQg64Gd64KY6riwIOyghOyXkCDrgYrqsrzr
>> "%B64%" echo i6QiICLsgqzsnKA6ICRlcnJgcmBuJCgkci50ZXh0KSIgIuydtCDtjIzsnbzsnYQg64uk7IucIOyL
>> "%B64%" echo pO2Wie2VtOyEnCDsirnsnbjtlbTrnbwuIg0KICB9DQp9DQppZiAoLW5vdCAkdG9rZW5zKSB7IFN0
>> "%B64%" echo b3AtQmFkICLsoJztlZwg7Iuc6rCEIOyViOyXkCDsirnsnbjsnbQg7JWIIOuQkOuLpCIgIuuLpOyL
>> "%B64%" echo nCDsi6TtlontlbTrnbwuIiAiIiB9DQoNCiRhdCA9ICR0b2tlbnMuYWNjZXNzX3Rva2VuDQpTYXkg
>> "%B64%" echo IiINClNheSAiICBbT0tdIDHri6jqs4Qg7Ya16rO8IC0g66Gc6re47J24IOyEseqztSjrgrQg6rOE
>> "%B64%" echo 7KCV7J20IOyduOymneuQkOuLpCkiDQpbdm9pZF0kc2NyaXB0OkxvZy5BZGQoIiAgICAgIO2GoO2B
>> "%B64%" echo sCjqsIDrprwpOiAiICsgKE1hc2sgJGF0KSkNCg0KIyAoNCkg7Iug7JuQKOyLpO2MqO2VtOuPhCDs
>> "%B64%" echo p4TtlokpDQppZiAoJHdob1VybCkgew0KICAkciA9IFdlYiAkd2hvVXJsICRudWxsICRhdCAiR0VU
>> "%B64%" echo Ig0KICBpZiAoJHIuY29kZSAtZXEgMjAwIC1hbmQgJHIub2JqKSB7DQogICAgJG5tID0gJHIub2Jq
>> "%B64%" echo LmVtYWlsOyBpZiAoLW5vdCAkbm0pIHsgJG5tID0gJHIub2JqLm5hbWUgfTsgaWYgKC1ub3QgJG5t
>> "%B64%" echo KSB7ICRubSA9ICRyLm9iai5zdWIgfQ0KICAgIFNheSAiICAgICAgIOqzhOyglTogJG5tIg0KICB9
>> "%B64%" echo DQp9DQoNCiMgKDUpIOyTuCDsiJgg7J6I64qUIOuqqOuNuCDrqqnroZ0gLSDsnpDqsqkg6rGw7KCI
>> "%B64%" echo 7J2066m0IOyXrOq4sOyEnCDsnbTrr7gg6rCI66aw64ukDQokYXZhaWwgPSBAKCkNCiRyID0gV2Vi
>> "%B64%" echo ICIkQVBJX0JBU0UvbW9kZWxzIiAkbnVsbCAkYXQgIkdFVCINCmlmICgkci5jb2RlIC1lcSAyMDAg
>> "%B64%" echo LWFuZCAkci5vYmouZGF0YSkgew0KICAkYXZhaWwgPSBAKCRyLm9iai5kYXRhIHwgRm9yRWFjaC1P
>> "%B64%" echo YmplY3QgeyAkXy5pZCB9IHwgV2hlcmUtT2JqZWN0IHsgJF8gfSkNCiAgU2F5ICIgICAgICAg7JO4
>> "%B64%" echo IOyImCDsnojripQg66qo6424ICQoJGF2YWlsLkNvdW50KeqwnDogJCgoJGF2YWlsIHwgU2VsZWN0
>> "%B64%" echo LU9iamVjdCAtRmlyc3QgOCkgLWpvaW4gJywgJykiDQp9IGVsc2Ugew0KICBTYXkgIiAgICAgICDr
>> "%B64%" echo qqjrjbgg66qp66Gd7J2AIOuquyDrsJvslZjri6QoSFRUUCAkKCRyLmNvZGUpKSAtIOq3uOuemOuP
>> "%B64%" echo hCDtmLjstpzsnYAg7Iuc64+E7ZWc64ukIg0KICBbdm9pZF0kc2NyaXB0OkxvZy5BZGQoIiAgICAg
>> "%B64%" echo ICAo66qp66GdIOydkeuLtSkgIiArICRyLnRleHQpDQp9DQoNCiMgKDYpIOyLpOygnCAx7L2cIC0g
>> "%B64%" echo 7J206rKMIO2MkOygleydmCDsoITrtoDri6QNCiRvcmRlciA9IEAoKQ0KZm9yZWFjaCAoJG0gaW4g
>> "%B64%" echo JGF2YWlsKSB7IGlmICgkTU9ERUxTIC1jb250YWlucyAkbSkgeyAkb3JkZXIgKz0gJG0gfSB9DQpm
>> "%B64%" echo b3JlYWNoICgkbSBpbiAkTU9ERUxTKSB7IGlmICgkb3JkZXIgLW5vdGNvbnRhaW5zICRtKSB7ICRv
>> "%B64%" echo cmRlciArPSAkbSB9IH0NCmZvcmVhY2ggKCRtIGluICRhdmFpbCkgIHsgaWYgKCRvcmRlciAtbm90
>> "%B64%" echo Y29udGFpbnMgJG0pIHsgJG9yZGVyICs9ICRtIH0gfQ0KJG9yZGVyID0gJG9yZGVyIHwgU2VsZWN0
>> "%B64%" echo LU9iamVjdCAtRmlyc3QgNg0KDQokbGFzdCA9ICRudWxsDQpmb3JlYWNoICgkbSBpbiAkb3JkZXIp
>> "%B64%" echo IHsNCiAgJHBheWxvYWQgPSBAeyBtb2RlbCA9ICRtOyBtZXNzYWdlcyA9IEAoQHsgcm9sZSA9ICJ1
>> "%B64%" echo c2VyIjsgY29udGVudCA9ICLtlZzqta3slrTroZwgJ+2GteqzvCfrnbzqs6Drp4wg64u17ZW0LiIg
>> "%B64%" echo fSk7IG1heF90b2tlbnMgPSAxNiB9IHwgQ29udmVydFRvLUpzb24gLURlcHRoIDUgLUNvbXByZXNz
>> "%B64%" echo DQogICRyID0gV2ViICIkQVBJX0JBU0UvY2hhdC9jb21wbGV0aW9ucyIgJHBheWxvYWQgJGF0ICJQ
>> "%B64%" echo T1NUIg0KICBTYXkgIiAgICAgICDtmLjstpwg7Iuc64+EIFskbV0gLT4gSFRUUCAkKCRyLmNvZGUp
>> "%B64%" echo Ig0KICAkbGFzdCA9IEB7IG0gPSAkbTsgciA9ICRyIH0NCiAgaWYgKCRyLmNvZGUgLWVxIDIwMCAt
>> "%B64%" echo YW5kICRyLm9iaikgew0KICAgICRzYXkgPSAiIg0KICAgIHRyeSB7ICRzYXkgPSAkci5vYmouY2hv
>> "%B64%" echo aWNlc1swXS5tZXNzYWdlLmNvbnRlbnQgfSBjYXRjaCB7ICRzYXkgPSAkci50ZXh0IH0NCiAgICAk
>> "%B64%" echo a2VlcCA9IEB7DQogICAgICBhY2Nlc3NfdG9rZW4gPSAkYXQ7IHJlZnJlc2hfdG9rZW4gPSAkdG9r
>> "%B64%" echo ZW5zLnJlZnJlc2hfdG9rZW47IGV4cGlyZXNfaW4gPSAkdG9rZW5zLmV4cGlyZXNfaW4NCiAgICAg
>> "%B64%" echo IGNsaWVudF9pZCA9ICRDTElFTlRfSUQ7IHNjb3BlID0gJFNDT1BFOyB0b2tlbl9lbmRwb2ludCA9
>> "%B64%" echo ICR0b2tVcmw7IGFwaV9iYXNlID0gJEFQSV9CQVNFDQogICAgICBtb2RlbF9vayA9ICRtOyBzYXZl
>> "%B64%" echo ZF9hdCA9IChHZXQtRGF0ZSkuVG9TdHJpbmcoInl5eXktTU0tZGQgSEg6bW06c3MiKQ0KICAgIH0N
>> "%B64%" echo CiAgICB0cnkgeyAka2VlcCB8IENvbnZlcnRUby1Kc29uIC1EZXB0aCA1IHwgT3V0LUZpbGUgLUZp
>> "%B64%" echo bGVQYXRoICRUb2tlblBhdGggLUVuY29kaW5nIFVURjggfSBjYXRjaCB7fQ0KICAgIFNheSAiIg0K
>> "%B64%" echo ICAgIFNheSAoIj0iICogNTgpDQogICAgU2F5ICJb7Ya16rO8XSDrhKQg6rWs64+FIOyekOqyqeyc
>> "%B64%" echo vOuhnCDqt7jroZ3snbQg7Iuk7KCc66GcIOuMgOuLte2WiOuLpCINCiAgICBTYXkgKCI9IiAqIDU4
>> "%B64%" echo KQ0KICAgIFNheSAiICDrqqjrjbggOiAkbSINCiAgICBTYXkgIiAg64yA64u1IDogJCgkc2F5IC1y
>> "%B64%" echo ZXBsYWNlICdccysnLCcgJykiDQogICAgU2F5ICIgIO2GoO2BsCA6ICRUb2tlblBhdGggICjqsLHs
>> "%B64%" echo i6Ag7Je07IegIO2PrO2VqCAtIOuCqOyXkOqyjCDso7zsp4Ag66eI6528KSINCiAgICBTYXkgIiAg
>> "%B64%" echo 6riw66GdIDogJExvZ1BhdGgiDQogICAgU2F5ICIiDQogICAgU2F5ICIgIC0+IOq4sOuhnSDtjIzs
>> "%B64%" echo nbzsnYQg7YG066Gc65OcIOyEuOyFmOyXkCDso7zrqbQg6re464yA66GcIOuwsOyEoO2VnOuLpC4i
>> "%B64%" echo DQogICAgU2F2ZUxvZw0KICAgIFdyaXRlLUhvc3QgIiINCiAgICBSZWFkLUhvc3QgIuyXlO2EsOul
>> "%B64%" echo vCDriITrpbTrqbQg7LC97J20IOuLq+2ejOuLpCINCiAgICBleGl0IDANCiAgfQ0KICBpZiAoJHIu
>> "%B64%" echo Y29kZSAtZXEgNDA0KSB7IGNvbnRpbnVlIH0gICAjIOuqqOuNuCDsnbTrpoQg66y47KCcID0g64uk
>> "%B64%" echo 7J2MIO2bhOuztOuhnA0KfQ0KDQokbSA9ICRsYXN0Lm07ICRyID0gJGxhc3Qucg0KJHJlYXNvbiA9
>> "%B64%" echo ICRyLnRleHQNCnRyeSB7IGlmICgkci5vYmouZXJyb3IpIHsgJHJlYXNvbiA9ICgkci5vYmouZXJy
>> "%B64%" echo b3IgfCBPdXQtU3RyaW5nKSB9IH0gY2F0Y2gge30NClNheSAiIg0KU2F5ICgiPSIgKiA1OCkNClNh
>> "%B64%" echo eSAiW+qxsOygiF0g66Gc6re47J247J2AIOuQkOuKlOuNsCDtmLjstpzsnYQg66eJ7JWY64ukIg0K
>> "%B64%" echo U2F5ICgiPSIgKiA1OCkNClNheSAiICDrp4jsp4Drp4kg7Iuc64+EICA6ICRtIC0+IEhUVFAgJCgk
>> "%B64%" echo ci5jb2RlKSINClNheSAiICDshJzrsoTqsIAg7ZWcIOunkCA6ICQoJHJlYXNvbiAtcmVwbGFjZSAn
>> "%B64%" echo XHMrJywnICcpIg0KU2F5ICIiDQppZiAoJHIuY29kZSAtZXEgNDAzKSB7IFNheSAiICA0MDMgPSDs
>> "%B64%" echo npDqsqkg6rGw7KCI7J2064ukLiDqtazrj4XsnYAg7IK07JWEIOyeiOuKlOuNsCB4QUkg6rCAIOyd
>> "%B64%" echo tCDthrXroZzrpbwg7JWIIOyXtOyWtOykgCDqsoMuIiB9DQplbHNlaWYgKCRyLmNvZGUgLWVxIDQw
>> "%B64%" echo MSkgeyBTYXkgIiAgNDAxID0g7Yag7YGwIOusuOygnOuLpC4g64uk7IucIOyLpO2Wie2VtOyEnCDr
>> "%B64%" echo oZzqt7jsnbjrtoDthLAg7ZW067SQ6528LiIgfQ0KZWxzZWlmICgkci5jb2RlIC1lcSA0MjkpIHsg
>> "%B64%" echo U2F5ICIgIDQyOSA9IO2VnOuPhOuLpC4g7J6Q6rKp7J2AIOyeiOuLpOuKlCDrnLvsnbTri4gg7J6g
>> "%B64%" echo 7IucIOuSpCDri6Tsi5wg64+M66Ck6528LiIgfQ0KU2F5ICIiDQpTYXkgIiAg6riw66GdIDogJExv
>> "%B64%" echo Z1BhdGggICAo7J20IO2MjOydvOydhCDtgbTroZzrk5wg7IS47IWY7JeQIOyjvOuptCDsm5Dsnbgg
>> "%B64%" echo 7YyQ7KCV7ZWc64ukKSINClNhdmVMb2cNCldyaXRlLUhvc3QgIiINClJlYWQtSG9zdCAi7JeU7YSw
>> "%B64%" echo 66W8IOuIhOultOuptCDssL3snbQg64ur7Z6M64ukIg0KZXhpdCAyDQo=
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
