# ═══════════════════════════════════════════════════════════════════════════════
# hf_probe.ps1 (2판) — 힉스필드 자격을 러너가 쓸 수 있는 **열쇠 한 줄**로 바꾼다
#
# ⚠ 1판(기기 코드 방식)은 **모델이 안 열렸다**(260812 실측 · 런 31624564002).
#   자격도 잔액도 통과했는데(3,060 크레딧 · ultra) 러너가 보는 모델 목록이 6종뿐이고
#   그 안에 시댄스가 없었다. 같은 계정인데 사람이 붙인 연결에서는 시댄스가 그대로 먹혔다
#   → 차이는 **어느 로그인 방식으로 받은 자격이냐**였다. 창구가 공개한 안내에도 기기 코드 방식은
#   다른 프로그램용으로 적혀 있다. → 2판은 **브라우저 방식**(사람이 붙인 연결과 같은 길)으로 간다.
#
# 흐름(실측 규격 · 260812) =
#   ① POST /oauth2/register  → 우리 프로그램 번호(등록에 승인 불요 · 즉시 발급)
#   ② 브라우저로 /oauth2/authorize (PKCE) → 로그인·허용
#   ③ 내 PC 가 잠깐 연 창구로 승인 코드가 돌아온다(127.0.0.1)
#   ④ POST /oauth2/token → 접속 열쇠 + **갱신 열쇠**
#
# 산출:  바탕화면\힉스필드확인_결과.txt   (기록 · 열쇠는 앞 12자만 남기고 가린다)
#        바탕화면\힉스필드열쇠_붙여넣기.txt (붙여넣을 값 **한 줄** = 프로그램번호:갱신열쇠)
# 끄는 법: 안 돌리면 끝. 설치되는 것도, 자동 실행되는 것도 없다. 크레딧 0.
# 생성 정본: scripts/hf_probe.ps1 · 번들 재생성 = python3 scripts/build_hf_probe_bundle.py
# ═══════════════════════════════════════════════════════════════════════════════
$ErrorActionPreference = "Stop"
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
try { $OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

$BASE = "https://mcp.higgsfield.ai"
$PORT = 8765
$REDIR = "http://127.0.0.1:$PORT/callback"
$SCOPE = "openid email offline_access"
$SECRET_NAME = "HIGGSFIELD_REFRESH_TOKEN"
# ⚠ 창구 앞단이 파이썬·기본 서명을 막는다(1010) → 브라우저 서명을 단다(260812 실측).
$UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"

# ⚠ 바탕화면 경로는 빈 문자열로 올 수 있다(원드라이브 백업 실측) → 폴백 사슬.
$Desk = ""
foreach ($c in @([Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory),
                 [Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop),
                 (Join-Path $env:USERPROFILE "Desktop"),
                 (Join-Path $env:USERPROFILE "바탕 화면"),
                 $env:USERPROFILE, $env:TEMP)) {
  if ($c -and (Test-Path $c)) { $Desk = $c; break }
}
if (-not $Desk) { $Desk = "." }
$LogPath = Join-Path $Desk "힉스필드확인_결과.txt"
$KeyPath = Join-Path $Desk "힉스필드열쇠_붙여넣기.txt"
$Lines = New-Object System.Collections.ArrayList

function Say([string]$m, [string]$color = "Gray") { Write-Host $m -ForegroundColor $color; [void]$Lines.Add($m) }
function Mask([string]$v) { if (-not $v) { return "(없음)" } ; if ($v.Length -le 12) { return "***" } ; return $v.Substring(0,12) + "…(" + $v.Length + "자)" }
function Done([int]$rc) {
  $Lines -join "`r`n" | Set-Content -Path $LogPath -Encoding UTF8
  Write-Host ""; Write-Host ("기록: " + $LogPath) -ForegroundColor DarkGray
  Read-Host "엔터를 누르면 닫힙니다" | Out-Null
  exit $rc
}
function B64Url([byte[]]$b) { [Convert]::ToBase64String($b).TrimEnd('=').Replace('+','-').Replace('/','_') }

Say ""
Say "  ┌────────────────────────────────┐" "Cyan"
Say "  │  노뮤트 — 힉스필드 자격 확인 (2판)         │" "Cyan"
Say "  │  브라우저로 한 번 허용하면 끝납니다      │" "Cyan"
Say "  │  크레딧은 쓰지 않습니다                │" "Cyan"
Say "  └────────────────────────────────┘" "Cyan"
Say ""
Say ("실행 시각 : " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
Say ""

# ── ① 프로그램 등록 ───────────────────────────────────
try {
  $reg = Invoke-RestMethod -Uri "$BASE/oauth2/register" -Method Post -TimeoutSec 40 `
    -Headers @{ "User-Agent" = $UA } -ContentType "application/json" -Body (@{
      client_name = "nomute-editor"; redirect_uris = @($REDIR)
      grant_types = @("authorization_code","refresh_token"); response_types = @("code")
      token_endpoint_auth_method = "none"; scope = $SCOPE } | ConvertTo-Json -Compress)
} catch {
  Say "❌ 프로그램 등록 실패." "Red"; Say ("   사유: " + $_.Exception.Message) "Red"; Done 1
}
$clientId = [string]$reg.client_id
Say ("① 프로그램 등록 ✓  번호 " + $clientId)

# ── ② 승인 창 ─────────────────────────────────────────────────────
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$vb = New-Object byte[] 64; $rng.GetBytes($vb); $verifier = B64Url $vb
$sha = [Security.Cryptography.SHA256]::Create()
$challenge = B64Url $sha.ComputeHash([Text.Encoding]::ASCII.GetBytes($verifier))
$sb = New-Object byte[] 16; $rng.GetBytes($sb); $state = B64Url $sb

$authUrl = "$BASE/oauth2/authorize?response_type=code&client_id=$clientId" +
           "&redirect_uri=" + [Uri]::EscapeDataString($REDIR) +
           "&scope=" + [Uri]::EscapeDataString($SCOPE) +
           "&state=$state&code_challenge=$challenge&code_challenge_method=S256"

$listener = New-Object System.Net.Sockets.TcpListener([Net.IPAddress]::Loopback, $PORT)
try { $listener.Start() } catch {
  Say ("❌ 내 PC 창구(" + $PORT + "번)를 못 열었습니다: " + $_.Exception.Message) "Red"
  Say "   다른 프로그램이 그 번호를 쓰고 있을 수 있습니다. 잠시 뒤 다시 실행해 주세요."
  Done 1
}

Say ""
Say "② 승인 창을 엽니다. 브라우저에서 허용을 누르세요."
Say ""
Say ("   " + $authUrl) "DarkGray"
Say ""
try { Start-Process $authUrl | Out-Null } catch { Say "   (브라우저가 안 열리면 위 주소를 직접 붙여넣으세요)" "Yellow" }

$code = $null; $deadline = (Get-Date).AddMinutes(5)
while ((Get-Date) -lt $deadline -and -not $code) {
  if (-not $listener.Pending()) { Start-Sleep -Milliseconds 300; continue }
  $cl = $listener.AcceptTcpClient(); $st = $cl.GetStream()
  $buf = New-Object byte[] 8192; $n = $st.Read($buf, 0, $buf.Length)
  $req = [Text.Encoding]::ASCII.GetString($buf, 0, $n)
  $first = ($req -split "`r`n")[0]
  if ($first -match 'GET\s+(\S+)') {
    $q = $Matches[1]
    if ($q -match '[?&]code=([^&\s]+)') { $code = [Uri]::UnescapeDataString($Matches[1]) }
    if ($q -match '[?&]state=([^&\s]+)') {
      if ([Uri]::UnescapeDataString($Matches[1]) -ne $state) {
        Say "❌ 응답의 표식이 안 맞습니다(중간에서 가로채였을 수 있습니다)." "Red"; $code = $null
      }
    }
  }
  $html = "<html><head><meta charset='utf-8'></head><body style='font-family:sans-serif;background:#111;color:#eee;padding:40px'><h2>" +
          $(if ($code) { "승인 완료" } else { "승인 실패" }) +
          "</h2><p>이 창을 닫고 검은 창으로 돌아가세요.</p></body></html>"
  $body = [Text.Encoding]::UTF8.GetBytes($html)
  $head = [Text.Encoding]::ASCII.GetBytes("HTTP/1.1 200 OK`r`nContent-Type: text/html; charset=utf-8`r`nContent-Length: $($body.Length)`r`nConnection: close`r`n`r`n")
  $st.Write($head, 0, $head.Length); $st.Write($body, 0, $body.Length); $st.Flush()
  $cl.Close()
}
$listener.Stop()

if (-not $code) { Say ""; Say "❌ 시간 안에 승인이 안 됐습니다. 다시 실행해 주세요." "Red"; Done 1 }
Say ""
Say "   ✅ 승인 완료" "Green"

# ── ③ 열쇠 교환 ───────────────────────────────────────────────
$form = "grant_type=authorization_code&code=" + [Uri]::EscapeDataString($code) +
        "&redirect_uri=" + [Uri]::EscapeDataString($REDIR) +
        "&client_id=" + [Uri]::EscapeDataString($clientId) +
        "&code_verifier=" + [Uri]::EscapeDataString($verifier)
try {
  $tok = Invoke-RestMethod -Uri "$BASE/oauth2/token" -Method Post -TimeoutSec 40 `
    -Headers @{ "User-Agent" = $UA } -ContentType "application/x-www-form-urlencoded" -Body $form
} catch {
  Say "❌ 열쇠 교환 실패." "Red"; Say ("   사유: " + $_.Exception.Message) "Red"; Done 1
}
$access = [string]$tok.access_token
$refresh = [string]$tok.refresh_token
Say ""
Say "③ 열쇠 받음 ✓"
Say ("   접속 열쇠 : " + (Mask $access))
Say ("   갱신 열쇠 : " + (Mask $refresh))
if ($tok.expires_in) { Say ("   접속 열쇠 수명 : " + $tok.expires_in + "초") }

if (-not $refresh) {
  Say ""
  Say "❌ 갱신 열쇠가 응답에 없습니다 — 이 줄을 그대로 알려 주세요." "Red"; Done 1
}


# ── ④ **붙여넣기 전에 여기서 증명한다** ─────────────────────────────────────────
# ⚠ 왜 이 단계가 있나(260812 실사고) = 1판으로 받은 열쇠는 자격·잔액이 다 통과하는데
#   **모델 목록에 시댄스가 없었다.** 그걸 깃허브에 넣고 러너를 돌린 뒤에야 알았다 =
#   운영자가 헛수고를 했다. 그래서 2판은 **열쇠를 주기 전에** 창구에 직접 물어본다.
Say ""
Say "④ 이 열쇠로 시댄스가 열리는지 지금 확인합니다."

$hdr = @{ "Authorization" = "Bearer $access"; "User-Agent" = $UA
          "Accept" = "application/json, text/event-stream"; "MCP-Protocol-Version" = "2025-06-18" }
$script:sid = $null
function Rpc([string]$method, $prm) {
  $body = (@{ jsonrpc = "2.0"; id = (Get-Random -Maximum 99999); method = $method; params = $prm } | ConvertTo-Json -Depth 12 -Compress)
  $h = $hdr.Clone(); if ($script:sid) { $h["Mcp-Session-Id"] = $script:sid }
  $r = Invoke-WebRequest -Uri "$BASE/mcp" -Method Post -Headers $h -ContentType "application/json" -Body $body -TimeoutSec 60 -UseBasicParsing
  if ($r.Headers["Mcp-Session-Id"]) { $script:sid = [string]$r.Headers["Mcp-Session-Id"] }
  $t = [string]$r.Content
  if ($t -match '(?m)^data:\s*(\{.*)$') { $t = $Matches[1] }   # 이벤트 스트림이면 알맹이만
  return ($t | ConvertFrom-Json)
}
function Tool([string]$name, $args2) {
  $res = Rpc "tools/call" @{ name = $name; arguments = $args2 }
  if ($res.error) { return "ERR " + ($res.error | ConvertTo-Json -Compress) }
  foreach ($c in $res.result.content) { if ($c.type -eq "text") { return [string]$c.text } }
  return ($res.result | ConvertTo-Json -Depth 8 -Compress)
}

$ok = $false
try {
  Rpc "initialize" @{ protocolVersion = "2025-06-18"; capabilities = @{}
                      clientInfo = @{ name = "nomute-probe"; version = "2.0" } } | Out-Null
  try { Rpc "notifications/initialized" @{} | Out-Null } catch {}
  $bal = Tool "balance" @{}
  Say ("   잔액 : " + $bal)
  $cost = Tool "generate_video" @{ params = @{ model = "seedance_2_5"; prompt = "cost check"
      duration = 30; resolution = "720p"; mode = "omni_reference"; aspect_ratio = "9:16"
      generate_audio = $true; use_unlim = $false; get_cost = $true } }
  Say ("   시댄스 견적 : " + $cost)
  if ($cost -match '"credits"' -or $cost -match '\d+\s*credit') { $ok = $true }
} catch {
  Say ("   ⚠ 확인 호출이 실패했습니다: " + $_.Exception.Message) "Yellow"
}

if (-not $ok) {
  Say ""
  Say "  ┌────────────────────────────────┐" "Red"
  Say "  │  ❌ 이 열쇠로는 시댄스가 안 열립니다      │" "Red"
  Say "  └────────────────────────────────┘" "Red"
  Say ""
  Say "  ⚠ **깃허브에 붙여넣지 마세요.** 넣어도 영상이 안 만들어집니다." "Yellow"
  Say "  위 두 줄(잔액·시댄스 견적)을 그대로 복사해서 알려 주세요. 그 값으로 다음 수를 정합니다."
  Say ""
  Set-Content -Path $KeyPath -Value "" -Encoding ASCII -NoNewline
  Done 1
}
Say "   ✅ 시댄스 열림 확인" "Green"

# ⚠ 값만 한 줄로 쓴다 — 큰 덩어리에서 눈으로 잘라내게 하면 사고가 난다.
#   프로그램 번호도 같이 필요해서 한 줄로 묶는다(붙여넣기 1회 원칙).
Set-Content -Path $KeyPath -Value ($clientId + ":" + $refresh) -Encoding ASCII -NoNewline

Say ""
Say "  ┌────────────────────────────────┐" "Green"
Say "  │  끝났습니다. 두 걸음만 하면 됩니다        │" "Green"
Say "  └────────────────────────────────┘" "Green"
Say ""
Say "  1) 바탕화면의 「힉스필드열쇠_붙여넣기.txt」 를 열어 안의 값을 전부 복사"
Say ""
Say "  2) 깃허브 레포 → Settings → Secrets and variables → Actions"
Say ("     → " + $SECRET_NAME + " 를 이 값으로 바꾸기(Update secret)")
Say ""
Say "  ⚠ 붙여넣은 뒤에는 바탕화면의 두 파일을 지우세요."
Say "  ⚠ 이 값은 남에게 주지 마세요. 계정 크레딧을 쓸 수 있는 값입니다."
Say ""
Write-Host ("열쇠: " + $KeyPath) -ForegroundColor DarkGray
Done 0
