# grok_probe.ps1 — X(엑스) 구독 자격으로 Grok API 를 부를 수 있는지 실호출로 판정한다.
#
# 배경(260810 · 운영자 "이미 내가 가지고 있는 x계정에 속한 그록 oauth 를 빼서 배선시킬 수 있는 방법있나?"):
#   xAI 가 2026-05 부터 구독자용 OAuth 를 열었다 — API 키(종량제) 없이 SuperGrok / X Premium+ 자격만으로
#   https://api.x.ai/v1 를 부른다. 다만 백엔드가 그 통로에 자체 허용목록을 걸고 있다는 신고가 다수 있어
#   **우리 계정이 되는지는 실호출로만 알 수 있다** → 이 파일은 그 한 가지만 한다.
#
# ⚠ 판정기다. 배선 아님(레포 라이브 무접촉 · 자동 실행 0 · 안 돌리면 아무 일도 안 일어난다).
#
# 파이썬 판(shared/grok_oauth_probe.py)과 같은 판정을 하되, 운영자 PC 에서 **더블클릭 1회**로 끝나게
# 파워셸로 옮긴 사본이다(260810 실측 = 윈도우에서 python3 가 헛돌고 실행 폴더도 어긋났다 = 첫 실행 장애를
# 코드로 흡수 · CLAUDE [9-3]).
#
# 산출:  바탕화면\그록확인_결과.txt (기록 · 토큰은 앞 12자만 남기고 가린다)
#        바탕화면\그록토큰.json     (통과했을 때만 · 배선 재료 · 남에게 주지 마라)
# 끄는 법: 안 돌리면 끝. 설치되는 것도, 자동 실행되는 것도 없다.

$ErrorActionPreference = "Stop"
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
try { $OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

$CLIENT_ID = "b1a00492-073a-47ea-816f-4c329264a828"   # xAI 공개 데스크톱 클라이언트(비밀키 없음)
$SCOPE     = "openid profile email offline_access grok-cli:access api:access"
$DISCOVERY = "https://auth.x.ai/.well-known/openid-configuration"
$API_BASE  = "https://api.x.ai/v1"
$MODELS    = @("grok-4.5","grok-4.3","grok-3","grok-beta")

# ⚠ 바탕화면 경로는 빈 문자열로 올 수 있다(원드라이브 백업·비윈도우 환경 실측) → 폴백 사슬.
#   한 칸이라도 비면 Join-Path 가 그 자리에서 죽어 판정 자체를 못 한다(첫 실행 실측 봉합).
$Desk = ""
# (⚠ Join-Path 는 빈 값을 받으면 그 자리에서 죽는다 = 폴백이 폴백 전에 터진다 → 문자열로만 잇는다)
foreach ($c in @([Environment]::GetFolderPath("Desktop"),
                 "$env:USERPROFILE\Desktop", "$env:USERPROFILE", "$env:TEMP", (Get-Location).Path)) {
  if ($c -and $c.Trim() -and (Test-Path -LiteralPath $c)) { $Desk = $c; break }
}
if (-not $Desk) { $Desk = "." }
$LogPath   = Join-Path $Desk "그록확인_결과.txt"
$TokenPath = Join-Path $Desk "그록토큰.json"
$script:Log = New-Object System.Collections.ArrayList

function Say($t) { Write-Host $t; [void]$script:Log.Add($t) }
function Mask($s) { if ($s -and $s.Length -gt 12) { $s.Substring(0,12) + "…<" + $s.Length + "자 가림>" } else { $s } }
function SaveLog { try { $script:Log -join "`r`n" | Out-File -FilePath $LogPath -Encoding UTF8 } catch {} }

# 상태코드까지 받아오는 요청기(파워셸 5.1 에선 실패 응답 본문을 직접 읽어야 한다)
function Web($url, $body, $token, $method) {
  $h = @{}
  if ($token) { $h["Authorization"] = "Bearer $token" }
  $p = @{ Uri = $url; Headers = $h; TimeoutSec = 90; UseBasicParsing = $true }
  if ($method) { $p["Method"] = $method } elseif ($body) { $p["Method"] = "POST" } else { $p["Method"] = "GET" }
  if ($body -is [hashtable]) { $p["Body"] = $body; $p["ContentType"] = "application/x-www-form-urlencoded" }
  elseif ($body) { $p["Body"] = [Text.Encoding]::UTF8.GetBytes($body); $p["ContentType"] = "application/json" }
  try {
    $r = Invoke-WebRequest @p
    $txt = $r.Content
    $obj = $null; try { $obj = $txt | ConvertFrom-Json } catch {}
    return @{ code = [int]$r.StatusCode; text = $txt; obj = $obj }
  } catch {
    # ⚠ 파워셸 5.1 과 7 이 실패 응답을 다르게 넘긴다 — 5.1은 Response 스트림, 7은 ErrorDetails.
    #   한쪽만 읽으면 "서버가 뭐라고 거절했는지"가 통째로 사라진다(= 이 판정기의 존재 이유가 사라진다).
    $code = 0; $txt = "$($_.Exception.Message)"
    try { if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $txt = $_.ErrorDetails.Message } } catch {}
    $resp = $null
    try { $resp = $_.Exception.Response } catch {}
    if ($resp) {
      try { $code = [int]$resp.StatusCode } catch {}
      if ($txt -eq "$($_.Exception.Message)") {
        try {
          $sr = New-Object IO.StreamReader($resp.GetResponseStream())
          $txt = $sr.ReadToEnd(); $sr.Close()
        } catch {}
      }
    }
    $obj = $null; try { $obj = $txt | ConvertFrom-Json } catch {}
    return @{ code = $code; text = $txt; obj = $obj }
  }
}

function Stop-Bad($title, $detail, $hint) {
  Say ""
  Say ("=" * 58)
  Say "[X] $title"
  Say ("=" * 58)
  Say $detail
  if ($hint) { Say ""; Say $hint }
  Say ""
  Say "기록: $LogPath"
  SaveLog
  Write-Host ""
  Read-Host "엔터를 누르면 창이 닫힌다"
  exit 1
}

Say ""
Say "+----------------------------------------------------------+"
Say "| 그록 구독 자격 판정기 - 로그인 1회 + 실제 호출 1회        |"
Say "+----------------------------------------------------------+"
Say ""

# (1) 엔드포인트는 하드코딩 대신 xAI 가 알려주는 값을 쓴다(주소가 바뀌어도 따라간다)
$r = Web $DISCOVERY $null $null "GET"
if ($r.code -ne 200 -or -not $r.obj) {
  Stop-Bad "인증 서버 정보를 못 받았다" "HTTP $($r.code)`r`n$($r.text)" "인터넷이나 회사 방화벽 문제일 수 있다. 브라우저로 $DISCOVERY 가 열리는지 확인해봐라."
}
$devUrl = $r.obj.device_authorization_endpoint
$tokUrl = $r.obj.token_endpoint
$whoUrl = $r.obj.userinfo_endpoint
if (-not $devUrl -or -not $tokUrl) { Stop-Bad "이 서버는 코드 승인 방식을 안 받는다" $r.text "" }
Say "  인증 서버 확인 완료"

# (2) 코드 발급
$r = Web $devUrl @{ client_id = $CLIENT_ID; scope = $SCOPE } $null "POST"
if ($r.code -ne 200 -or -not $r.obj.user_code) {
  Stop-Bad "로그인 코드 발급이 거절됐다" "HTTP $($r.code)`r`n$($r.text)" "잠시 뒤 다시 실행해봐라."
}
$dev      = $r.obj
$verify   = if ($dev.verification_uri_complete) { $dev.verification_uri_complete } else { $dev.verification_uri }
$interval = if ($dev.interval) { [int]$dev.interval } else { 5 }
$expires  = if ($dev.expires_in) { [int]$dev.expires_in } else { 900 }

Say ""
Say "  +------------------------------------------------------+"
Say "  | 브라우저가 열린다. 로그인하고 [승인] 누르면 끝이다.   |"
Say "  +------------------------------------------------------+"
Say ""
Say "    주소 : $verify"
Say "    코드 : $($dev.user_code)"
Say ""
Say "  (제한 시간 $([int]($expires/60))분 · 승인하면 여기서 자동으로 넘어간다)"
Say ""
try { Start-Process $verify } catch { Say "  (브라우저 자동 열기 실패 - 위 주소를 직접 열어라)" }

# (3) 승인 대기
$deadline = (Get-Date).AddSeconds($expires)
$tokens = $null
$waited = 0
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds $interval
  $waited += $interval
  $r = Web $tokUrl @{ client_id = $CLIENT_ID; device_code = $dev.device_code; grant_type = "urn:ietf:params:oauth:grant-type:device_code" } $null "POST"
  if ($r.code -eq 200 -and $r.obj.access_token) { $tokens = $r.obj; break }
  $err = $null; try { $err = $r.obj.error } catch {}
  if ($err -eq "authorization_pending") { if ($waited % 30 -lt $interval) { Say "  ... 승인 기다리는 중 ($waited 초)" }; continue }
  if ($err -eq "slow_down") { $interval += 5; continue }
  if ($err -eq "expired_token" -or $err -eq "access_denied") {
    Stop-Bad "로그인이 끝나기 전에 끊겼다" "사유: $err`r`n$($r.text)" "이 파일을 다시 실행해서 승인해라."
  }
}
if (-not $tokens) { Stop-Bad "제한 시간 안에 승인이 안 됐다" "다시 실행해라." "" }

$at = $tokens.access_token
Say ""
Say "  [OK] 1단계 통과 - 로그인 성공(내 계정이 인증됐다)"
[void]$script:Log.Add("      토큰(가림): " + (Mask $at))

# (4) 신원(실패해도 진행)
if ($whoUrl) {
  $r = Web $whoUrl $null $at "GET"
  if ($r.code -eq 200 -and $r.obj) {
    $nm = $r.obj.email; if (-not $nm) { $nm = $r.obj.name }; if (-not $nm) { $nm = $r.obj.sub }
    Say "       계정: $nm"
  }
}

# (5) 쓸 수 있는 모델 목록 - 자격 거절이면 여기서 이미 갈린다
$avail = @()
$r = Web "$API_BASE/models" $null $at "GET"
if ($r.code -eq 200 -and $r.obj.data) {
  $avail = @($r.obj.data | ForEach-Object { $_.id } | Where-Object { $_ })
  Say "       쓸 수 있는 모델 $($avail.Count)개: $(($avail | Select-Object -First 8) -join ', ')"
} else {
  Say "       모델 목록은 못 받았다(HTTP $($r.code)) - 그래도 호출은 시도한다"
  [void]$script:Log.Add("       (목록 응답) " + $r.text)
}

# (6) 실제 1콜 - 이게 판정의 전부다
$order = @()
foreach ($m in $avail) { if ($MODELS -contains $m) { $order += $m } }
foreach ($m in $MODELS) { if ($order -notcontains $m) { $order += $m } }
foreach ($m in $avail)  { if ($order -notcontains $m) { $order += $m } }
$order = $order | Select-Object -First 6

$last = $null
foreach ($m in $order) {
  $payload = @{ model = $m; messages = @(@{ role = "user"; content = "한국어로 '통과'라고만 답해." }); max_tokens = 16 } | ConvertTo-Json -Depth 5 -Compress
  $r = Web "$API_BASE/chat/completions" $payload $at "POST"
  Say "       호출 시도 [$m] -> HTTP $($r.code)"
  $last = @{ m = $m; r = $r }
  if ($r.code -eq 200 -and $r.obj) {
    $say = ""
    try { $say = $r.obj.choices[0].message.content } catch { $say = $r.text }
    $keep = @{
      access_token = $at; refresh_token = $tokens.refresh_token; expires_in = $tokens.expires_in
      client_id = $CLIENT_ID; scope = $SCOPE; token_endpoint = $tokUrl; api_base = $API_BASE
      model_ok = $m; saved_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
    try { $keep | ConvertTo-Json -Depth 5 | Out-File -FilePath $TokenPath -Encoding UTF8 } catch {}
    Say ""
    Say ("=" * 58)
    Say "[통과] 네 구독 자격으로 그록이 실제로 대답했다"
    Say ("=" * 58)
    Say "  모델 : $m"
    Say "  대답 : $($say -replace '\s+',' ')"
    Say "  토큰 : $TokenPath  (갱신 열쇠 포함 - 남에게 주지 마라)"
    Say "  기록 : $LogPath"
    Say ""
    Say "  -> 기록 파일을 클로드 세션에 주면 그대로 배선한다."
    SaveLog
    Write-Host ""
    Read-Host "엔터를 누르면 창이 닫힌다"
    exit 0
  }
  if ($r.code -eq 404) { continue }   # 모델 이름 문제 = 다음 후보로
}

$m = $last.m; $r = $last.r
$reason = $r.text
try { if ($r.obj.error) { $reason = ($r.obj.error | Out-String) } } catch {}
Say ""
Say ("=" * 58)
Say "[거절] 로그인은 됐는데 호출을 막았다"
Say ("=" * 58)
Say "  마지막 시도  : $m -> HTTP $($r.code)"
Say "  서버가 한 말 : $($reason -replace '\s+',' ')"
Say ""
if ($r.code -eq 403) { Say "  403 = 자격 거절이다. 구독은 살아 있는데 xAI 가 이 통로를 안 열어준 것." }
elseif ($r.code -eq 401) { Say "  401 = 토큰 문제다. 다시 실행해서 로그인부터 해봐라." }
elseif ($r.code -eq 429) { Say "  429 = 한도다. 자격은 있다는 뜻이니 잠시 뒤 다시 돌려라." }
Say ""
Say "  기록 : $LogPath   (이 파일을 클로드 세션에 주면 원인 판정한다)"
SaveLog
Write-Host ""
Read-Host "엔터를 누르면 창이 닫힌다"
exit 2
