# ═══════════════════════════════════════════════════════════════════════════════
# hf_probe.ps1 — 힉스필드 구독 자격을 러너가 쓸 수 있는 **열쇠 한 줄**로 바꾼다
#   (운영자 260812 "여튼 bat 주면 바로함")
#
# 왜 필요한가 = 힉스필드는 붙여넣을 API 키를 **안 준다**. 계정 로그인 방식이라 화면 어디에도
#   복사할 값이 없다. 러너(사람 없는 자동 실행)가 쓰려면 한 번 로그인해서 **갱신 열쇠**를
#   받아 깃허브 비밀값에 넣어야 하고, 그 한 번을 여기서 한다.
#
# 왜 작업 흐름이 아니라 PC 인가 = 이 레포는 **공개**다. 승인 코드를 러너에서 띄우면 공개 기록에
#   찍히고, 15분 승인 창 동안 남이 자기 계정으로 승인해버릴 수 있다. 네 화면에만 뜨는 건 네 PC 뿐이다.
#
# ⚠ 판정기다. 배선 아님(레포 라이브 무접촉 · 자동 실행 0 · 안 돌리면 아무 일도 안 일어난다).
# ⚠ 크레딧 0 — 영상·그림을 만들지 않는다. 로그인과 자격 확인만 한다.
#
# 흐름(실측 규격 · 260812) =
#   ① POST /authorize          → 기기 코드 + 승인 주소(15분 · 3초 간격)
#   ② 브라우저에서 승인
#   ③ POST /token {device_code} → 접속 열쇠 + **갱신 열쇠**
#   ④ POST /validate {token}    → 계정 번호 회신 = 실제로 쓸 수 있다는 증거
#
# 산출:  바탕화면\힉스필드확인_결과.txt   (기록 · 열쇠는 앞 12자만 남기고 가린다)
#        바탕화면\힉스필드열쇠_붙여넣기.txt (갱신 열쇠 **값 한 줄만** · 남에게 주지 마라)
# 끄는 법: 안 돌리면 끝. 설치되는 것도, 자동 실행되는 것도 없다.
# 생성 정본: scripts/hf_probe.ps1 · 번들 재생성 = python3 scripts/build_hf_probe_bundle.py
# ═══════════════════════════════════════════════════════════════════════════════
$ErrorActionPreference = "Stop"
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}
try { $OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

$AUTH = "https://fnf-device-auth.higgsfield.ai"
$SECRET_NAME = "HIGGSFIELD_REFRESH_TOKEN"

# ⚠ 바탕화면 경로는 빈 문자열로 올 수 있다(원드라이브 백업·비윈도우 실측) → 폴백 사슬.
#   한 칸이라도 비면 Join-Path 가 그 자리에서 죽어 판정 자체를 못 한다(그록 판정기 첫 실행 봉합).
$Desk = ""
foreach ($c in @([Environment]::GetFolderPath([Environment+SpecialFolder]::DesktopDirectory),
                 [Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop),
                 (Join-Path $env:USERPROFILE "Desktop"),
                 (Join-Path $env:USERPROFILE "바탕 화면"),
                 $env:USERPROFILE, $env:TEMP)) {
  if ($c -and (Test-Path $c)) { $Desk = $c; break }
}
if (-not $Desk) { $Desk = "." }

$LogPath  = Join-Path $Desk "힉스필드확인_결과.txt"
$KeyPath  = Join-Path $Desk "힉스필드열쇠_붙여넣기.txt"
$Lines = New-Object System.Collections.ArrayList

function Say([string]$m, [string]$color = "Gray") {
  Write-Host $m -ForegroundColor $color
  [void]$Lines.Add($m)
}
function Mask([string]$v) {
  if (-not $v) { return "(없음)" }
  if ($v.Length -le 12) { return "***" }
  return $v.Substring(0, 12) + "…(" + $v.Length + "자)"
}
function PostJson([string]$url, $body) {
  $json = if ($body) { $body | ConvertTo-Json -Compress } else { "{}" }
  return Invoke-RestMethod -Uri $url -Method Post -ContentType "application/json" -Body $json -TimeoutSec 40
}

Say ""
Say "  ┌────────────────────────────────────────────────┐" "Cyan"
Say "  │  노뮤트 — 힉스필드 자격 확인                    │" "Cyan"
Say "  │  로그인 1회로 러너가 쓸 열쇠를 받아옵니다       │" "Cyan"
Say "  │  크레딧은 쓰지 않습니다(영상·그림 제작 없음)    │" "Cyan"
Say "  └────────────────────────────────────────────────┘" "Cyan"
Say ""
Say ("실행 시각 : " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
Say ""

# ── ① 기기 코드 발급 ──────────────────────────────────────────────────────────
try {
  $a = PostJson "$AUTH/authorize" $null
} catch {
  Say "❌ 승인 코드를 못 받았습니다." "Red"
  Say ("   사유: " + $_.Exception.Message) "Red"
  Say ""
  Say "   회선이 막혔거나 힉스필드 쪽이 잠시 불안정한 경우입니다. 잠시 뒤 다시 실행해 주세요."
  $Lines -join "`r`n" | Set-Content -Path $LogPath -Encoding UTF8
  Write-Host ""; Read-Host "엔터를 누르면 닫힙니다" | Out-Null
  exit 1
}

$deviceCode = [string]$a.device_code
$uri        = [string]$a.verification_uri
$interval   = if ($a.interval) { [int]$a.interval } else { 3 }
$expires    = if ($a.expires_in) { [int]$a.expires_in } else { 900 }

Say "① 승인 창을 엽니다."
Say ""
Say ("   " + $uri) "Yellow"
Say ""
Say "   브라우저가 안 열리면 위 주소를 직접 여세요(폰으로 열어도 됩니다)."
Say ("   유효 시간 " + [int]($expires / 60) + "분")
Say ""
try { Start-Process $uri | Out-Null } catch { }

# ── ② 승인 기다리기 ───────────────────────────────────────────────────────────
Say "② 승인을 기다립니다… (브라우저에서 허용을 누르세요)"
$deadline = (Get-Date).AddSeconds($expires)
$tok = $null
$dots = 0
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Seconds $interval
  try {
    $tok = PostJson "$AUTH/token" @{ device_code = $deviceCode }
    if ($tok -and $tok.access_token) { break }
  } catch {
    # 아직 승인 전이면 422/4xx 가 정상이다 — 조용히 계속 기다린다.
    $tok = $null
  }
  $dots++
  if ($dots % 10 -eq 0) { Write-Host ("   … " + [int](($deadline - (Get-Date)).TotalSeconds) + "초 남음") -ForegroundColor DarkGray }
}

if (-not $tok -or -not $tok.access_token) {
  Say ""
  Say "❌ 시간 안에 승인이 안 됐습니다." "Red"
  Say "   다시 실행해서 브라우저에서 허용을 눌러 주세요."
  $Lines -join "`r`n" | Set-Content -Path $LogPath -Encoding UTF8
  Write-Host ""; Read-Host "엔터를 누르면 닫힙니다" | Out-Null
  exit 1
}

$access  = [string]$tok.access_token
$refresh = [string]$tok.refresh_token
Say ""
Say "   ✅ 승인 완료" "Green"
Say ("   접속 열쇠 : " + (Mask $access))
Say ("   갱신 열쇠 : " + (Mask $refresh))
if ($tok.expires_in)         { Say ("   접속 열쇠 수명 : " + $tok.expires_in + "초") }
if ($tok.refresh_expires_in) { Say ("   갱신 열쇠 수명 : " + $tok.refresh_expires_in + "초") }

# ── ③ 실제로 쓸 수 있는지 확인 ────────────────────────────────────────────────
Say ""
Say "③ 열쇠가 실제로 통하는지 확인합니다."
try {
  $v = PostJson "$AUTH/validate" @{ token = $access }
  Say ("   ✅ 통과 — 계정 번호 " + $v.user_id) "Green"
} catch {
  Say ("   ⚠ 확인 호출이 실패했습니다: " + $_.Exception.Message) "Yellow"
  Say "   열쇠는 받았으니 붙여넣기는 진행하세요. 이 줄은 그대로 알려 주세요."
}

# ── ④ 붙여넣을 값 ────────────────────────────────────────────────────────────
if (-not $refresh) {
  Say ""
  Say "❌ 갱신 열쇠가 응답에 없습니다 — 이 줄을 그대로 알려 주세요." "Red"
  $Lines -join "`r`n" | Set-Content -Path $LogPath -Encoding UTF8
  Write-Host ""; Read-Host "엔터를 누르면 닫힙니다" | Out-Null
  exit 1
}

# ⚠ 값만 한 줄로 쓴다 — 큰 덩어리에서 눈으로 잘라내게 하면 반드시 사고가 난다(그록 260811 실측 봉합).
Set-Content -Path $KeyPath -Value $refresh -Encoding ASCII -NoNewline

Say ""
Say "  ┌────────────────────────────────────────────────┐" "Green"
Say "  │  끝났습니다. 이제 두 걸음만 하면 됩니다        │" "Green"
Say "  └────────────────────────────────────────────────┘" "Green"
Say ""
Say "  1) 바탕화면의 「힉스필드열쇠_붙여넣기.txt」 를 열어 안의 값을 전부 복사"
Say ""
Say "  2) 깃허브 레포 → Settings → Secrets and variables → Actions"
Say ("     → New repository secret → 이름 " + $SECRET_NAME + " → 값 붙여넣기 → Add secret")
Say ""
Say "  ⚠ 붙여넣은 뒤에는 바탕화면의 두 파일을 지우세요(열쇠가 담긴 파일입니다)."
Say "  ⚠ 이 값은 남에게 주지 마세요. 계정 크레딧을 쓸 수 있는 값입니다."
Say ""

$Lines -join "`r`n" | Set-Content -Path $LogPath -Encoding UTF8
Write-Host ("기록: " + $LogPath) -ForegroundColor DarkGray
Write-Host ("열쇠: " + $KeyPath) -ForegroundColor DarkGray
Write-Host ""
Read-Host "엔터를 누르면 닫힙니다" | Out-Null
exit 0
