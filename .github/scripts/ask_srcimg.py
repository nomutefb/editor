#!/usr/bin/env python3
"""요약 요청의 출처 URL 페이지에서 **본문 이미지**를 내려받아 ask.sh 멀티모달 레일에 실어 준다.

[신설 사유 = 260804 실측 사고 fail-2026-08-04-0239-297it]
  SNS 카드 「전송」 → 보배드림 humor 글(No=1017600) → ANALYSIS_FAILED.
  실측 재현(WebFetch 직접 확인): 페이지는 **정상으로 열렸다**(제목 "이런걸 재능이라고 하는구나" ·
  댓글 8개 취득). 그런데 본문 텍스트가 **0자**이고 본문이 이미지 2장뿐이었다.
  → '사이트를 못 읽은 것'도 '내용을 긁고도 뜻을 모른 것'도 아니다. **읽을 글이 그림밖에 없었다.**
  제목은 순수 감상평이라 검색 키워드가 0 → 프롬프트 1-2 커뮤니티 폴백(제목 키워드 → 메이저 기사)도
  2회 검색에서 공회전 → 확보 사실 0 → 날조 대신 중단(모델 판단 자체는 정직했다).

  ⚠️ 파이프엔 **이미 멀티모달 레일이 있었다** — ask.sh 가 asks/*.json 의 images[](뷰어 캡처 첨부)를
  workdir/img-*.jpg 로 디코드해 프롬프트 '첨부 캡처 파일'로 넘긴다. 사각은 단 하나, **그 레일에
  '글의 본문 그림'이 실린 적이 없다**는 것: SNS 카드 전송은 {title, url, sum} 텍스트만 보낸다
  (viewer/index.html socBindSend · images 0장). 이 수확기가 그 빈 슬롯을 채운다 = 신규 분석 로직 0.

동작: URL → 페이지 취득(charset 정규화) → 본문 텍스트 길이 실측 → **얇을 때만** 본문 이미지 수확.
  텍스트가 충분한 일반 기사는 무동작(이미지 토큰 낭비 0) = 이 사고 축에만 발동한다.

계승(창작 0):
  · charset 판정·본문 텍스트 파서 = .github/scripts/fetch_article.sh 정본 관용구
  · 본문 <img src> 정규식 = scraper/knews_scraper.py `_IMG_SRC_RE` 정본
  · og:image 정규식 = scraper/sns_trends.py 정본(양방향 속성 순서 2패턴)
  · SSRF 호스트 가드 = functions/api/linkgrab/_lib.js `lgBlockedHost` 정본의 파이썬 미러

사용: python3 ask_srcimg.py <url> <outdir> [--max N] [--thin N] [--prefix src]
출력: stdout 1줄 JSON {"ok":bool,"text_len":int,"saved":[path…],"why":str}
      ⚠️ 항상 rc=0(fail-soft) — 수확 실패가 요약 자체를 죽이면 안 된다(사고 재발 방지의 역효과 차단).
"""
import html
import ipaddress
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

# ── cupid.js 봇월 통과 정본(shared/cupid_wall.py · 260912) ──
#   [왜 여기냐 = 실측 사고 fail-2026-09-12-0926] 이슈링크 커뮤니티 글(맘다니 뉴욕시장) 전송 →
#   이 수확기가 797B 챌린지 껍데기를 받아 페이지 텍스트 0자 → 본선이 원문을 못 보고 제목만으로
#   검색 시작 → effort max 600s 두 번 초과 = 21분 실패. 통과 코드는 레포에 이미 있었다
#   (scraper/social_burst.py 260625 · 같은 도메인) — 그 정본을 여기서도 쓴다(사본 0).
#   ⚠ 미설치·import 실패는 None 으로 떨어뜨려 **종전 동작 그대로**(회귀 0 · 수확기 전 경로 fail-soft 원칙).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared'))
try:
    import cupid_wall
except Exception:
    cupid_wall = None

# UA 2단(⚠️ 실측 260804 = 이 순서가 사고 재현의 핵심): 보배드림은 **모바일 UA 를 봇으로 차단**한다 —
#   fetch_article.sh 의 모바일 UA 그대로면 http 200 인데 본문 없는 3,566바이트 껍데기만 온다(조용한 실패).
#   데스크톱 UA 로 바꾸면 같은 URL 이 160,268바이트 = 본문 이미지 2장(IMG_0551·IMG_0552) 취득 성공.
#   → 데스크톱 1순위, 껍데기면 모바일로 1회 재시도(모바일 전용 서빙 매체 대비) = 두 성향을 다 흡수.
UA_DESK = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/151.0.0.0 Safari/537.36")
UA_MOB = ("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/124 Mobile Safari/537.36")   # fetch_article.sh 동값
SHELL_BYTES = 8_000     # 이보다 작은 HTML = 봇차단 껍데기 의심 → UA 교대 재시도(실측 차단본 = 3,566B)
FRAME_HOP_MAX = 2       # 프레임 셸 해제 추적 상한(네이버 블로그 = 1홉 · JS→프레임 이중 셸 대비 2)
TRY_MAX = 14            # 이미지 다운로드 시도 상한 — 커뮤니티 페이지는 사이드바 썸네일이 수십 장(실측 79장)

# ⚠️ 텍스트 길이로 '그림이 본문인가'를 가르려던 1차 설계는 **실측에서 폐기**했다(260804):
#   본문이 0자인 그 사고 페이지의 전체 텍스트가 7,558자로 나온다 — 사이드바·추천글·메뉴가 다 섞이기 때문.
#   본문 컨테이너 스코프는 매체마다 달라 일반해가 아니고, 오판하면 사고가 그대로 재발한다.
#   → 게이트를 **바이트로 실측 가능한 축**으로 옮겼다: 텍스트 길이는 리포트 값으로만 두고(기본 thin=0 =
#     길이 무관 수확), '본문이냐'는 이미지 자체의 성질(치수 미명시 + 다운로드 바이트 하한)로 가른다.
#   낭비 우려는 스코프가 흡수한다 — 이 수확기는 ask.sh 에서 **출처 URL 축(SNS 카드 전송·요청문 URL)에만**
#   걸리고, 원문 링크 레일(link)이 잡은 요청은 건드리지 않는다.
THIN_DEFAULT = 0        # 0 = 텍스트 길이와 무관하게 수확 · >0 이면 그 글자 수 이상일 때 생략(카나리아용)
WALL_TEXT_MIN = 50     # 봇월 통과 본문을 '전문'으로 실을 최소 자수(정제 후) — 이보다 짧으면 본문 선별 실패로 보고 안 싣는다.
#   ⚠ 기사용 하한(fetch_article.sh 200자)을 그대로 쓰면 안 된다 — 커뮤니티 글 본문은 원래 짧다
#   (실사고 글의 게시자 본문은 4줄·약 120자 · 나머지는 댓글). 그 120자가 바로 제목만으론 안 나오던
#   검색어(인물·쟁점)를 주는 대목이라, 기사 하한으로 걸러 버리면 사고 경로가 그대로 남는다.
#   dense_text 가 이미 '한글 20자 이상 줄'만 남기므로 50자 = 유의미한 2~3줄 = 잔해와 본문의 실질 경계.
WALL_TEXT_MAX = 6000   # 전문 주입 문자 상한 — fetch_article.sh 정본 값 계승(창작 0)
DENSE_LINES = 40       # 본문 줄 상한 — 같은 정본 값 계승
MAX_DEFAULT = 4         # 수확 상한(뷰어 캡처 images[:8]과 합류해도 여유) — 짤방 글은 대개 1~3장
IMG_MIN_BYTES = 15_000  # 이보다 작으면 아이콘·버튼·1x1 추적픽셀 취급(본문 짤방은 수십 KB↑)
IMG_MAX_BYTES = 12 << 20
PAGE_MAX_BYTES = 4 << 20
TIMEOUT = 20

# 본문이 아닌 장식·추적 이미지 경로 힌트(수확 대상에서 제외)
JUNK_RE = re.compile(
    r'(?:^|[/_.-])(?:icon|ico|logo|btn|button|banner|blank|spacer|pixel|dot|bullet|arrow|'
    r'emoticon|emoji|profile|avatar|thumb_s|loading|ad[sv]?|sprite|bg|watermark)(?:[/_.-]|\d|$)',
    re.I)
IMG_EXT_RE = re.compile(r'\.(jpe?g|png|gif|webp|bmp)(?:[?#]|$)', re.I)

_IMG_TAG_RE = re.compile(r'<img[^>]*>', re.I)
_IMG_SRC_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.I)   # knews_scraper.py 정본 사본
_LAZY_RE = re.compile(r'<img[^>]+data-(?:src|original|lazy-src)=["\']([^"\']+)["\']', re.I)
_DIM_RE = re.compile(r'\b(?:width|height)\s*=\s*["\']?(\d{1,4})', re.I)
THUMB_DIM = 200         # width/height 가 이보다 작게 명시된 img = 격자 썸네일(본문 아님 · 실측 78×54·45)
PX_MIN = 300            # 받아본 실측 픽셀의 짧은 변 하한 — 속성 미명시 썸네일까지 컷(실측 244×170 배너)
CT_EXT = {'image/jpeg': '.jpg', 'image/jpg': '.jpg', 'image/png': '.png',
          'image/gif': '.gif', 'image/webp': '.webp', 'image/bmp': '.bmp'}


def px_size(b):
    """바이트 → (w, h) 실측. 표준 라이브러리만(PIL 의존 0) · 못 읽으면 (0, 0).

    HTML 의 width/height 속성은 '안 적힌' 썸네일을 못 거른다(실측 = 244×170 추천 배너가 THUMB_DIM 통과).
    받아본 뒤 실제 픽셀로 재는 이 축이 최종 판정선 = 본문 짤방(1000px 급)과 격자 썸네일이 확실히 갈린다."""
    try:
        if b[:2] == b'\xff\xd8':                                   # JPEG — SOFn 마커 스캔
            i, n = 2, len(b)
            while i + 9 < n:
                if b[i] != 0xFF:
                    i += 1
                    continue
                mk = b[i + 1]
                if mk in (0xD8, 0x01) or 0xD0 <= mk <= 0xD7:
                    i += 2
                    continue
                seg = int.from_bytes(b[i + 2:i + 4], 'big')
                if 0xC0 <= mk <= 0xCF and mk not in (0xC4, 0xC8, 0xCC):
                    return (int.from_bytes(b[i + 7:i + 9], 'big'),
                            int.from_bytes(b[i + 5:i + 7], 'big'))
                if seg <= 0:
                    break
                i += 2 + seg
        elif b[:8] == b'\x89PNG\r\n\x1a\n':                         # PNG — IHDR
            return int.from_bytes(b[16:20], 'big'), int.from_bytes(b[20:24], 'big')
        elif b[:6] in (b'GIF87a', b'GIF89a'):
            return int.from_bytes(b[6:8], 'little'), int.from_bytes(b[8:10], 'little')
        elif b[:4] == b'RIFF' and b[8:12] == b'WEBP':               # WebP — VP8 / VP8L / VP8X
            c = b[12:16]
            if c == b'VP8 ':
                return (int.from_bytes(b[26:28], 'little') & 0x3FFF,
                        int.from_bytes(b[28:30], 'little') & 0x3FFF)
            if c == b'VP8L':
                v = int.from_bytes(b[21:25], 'little')
                return (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1
            if c == b'VP8X':
                return (int.from_bytes(b[24:27], 'little') + 1,
                        int.from_bytes(b[27:30], 'little') + 1)
    except Exception:
        pass
    return 0, 0


def _blocked_host(host):
    """functions/api/linkgrab/_lib.js lgBlockedHost 정본 미러 — 사설·예약·내부 대상 차단(SSRF)."""
    host = (host or '').lower().strip('[]')
    if not host:
        return True
    if (host == 'localhost' or host.endswith('.localhost') or host.endswith('.local')
            or host.endswith('.internal') or host == 'metadata.google.internal'):
        return True
    if ':' not in host:
        if re.search(r'(^|\.)0x[0-9a-f]+', host):
            return True
        labels = host.split('.')
        if any(re.fullmatch(r'0\d+', l) for l in labels):
            return True
        if re.fullmatch(r'\d+', host):
            return True
        if len(labels) < 4 and re.fullmatch(r'\d{1,3}(\.\d{1,3}){0,3}', host):
            return True
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return False   # 해석 실패 = fetch 가 어차피 실패 — 여기서 막을 필요 없음
    for inf in infos:
        try:
            ip = ipaddress.ip_address(inf[4][0])
        except Exception:
            continue
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified):
            return True
    return False


def _guard(url):
    try:
        p = urllib.parse.urlparse(url)
    except Exception:
        return None
    if p.scheme not in ('http', 'https') or not p.netloc:
        return None
    if _blocked_host(p.netloc.split('@')[-1].split(':')[0]):
        return None
    return url


def _get(url, referer='', limit=PAGE_MAX_BYTES, ua=UA_DESK, cookie='', ret_url=False):
    """(bytes, content_type) — 실패는 (b'', ''). ret_url=True 면 (bytes, ct, 최종URL).

    cookie = 'NAME=value' 한 줄(cupid 챌린지 재요청용 · 빈 값이면 헤더 자체를 안 붙여 종전 요청과 동일).
    ret_url = 리다이렉트 최종 도착지 반환(이슈링크 /community/go/… → 실제 커뮤니티 글 주소 축 · 260912).
    """
    if not _guard(url):
        return (b'', '', '') if ret_url else (b'', '')
    req = urllib.request.Request(url, headers={
        'User-Agent': ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        **({'Referer': referer} if referer else {}),
        **({'Cookie': cookie} if cookie else {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            fin = r.geturl()
            if not _guard(fin):           # 리다이렉트 최종 도착지 재검문(linkgrab lgFinalGuard 축)
                return (b'', '', '') if ret_url else (b'', '')
            raw, ct = r.read(limit + 1), (r.headers.get('content-type') or '')
            return (raw, ct, fin) if ret_url else (raw, ct)
    except Exception:
        return (b'', '', '') if ret_url else (b'', '')


def _ua_swap_get(url, referer=''):
    """데스크톱 1순위 + 껍데기(SHELL_BYTES 미만)면 모바일 UA 1회 교대(260804 실측 봉합)."""
    raw, ct = _get(url, referer=referer, ua=UA_DESK)
    if len(raw) < SHELL_BYTES:
        raw2, ct2 = _get(url, referer=referer, ua=UA_MOB)
        if len(raw2) > len(raw):
            return raw2, ct2
    return raw, ct


def _frame_target(raw, base):
    """껍데기 HTML 안의 진짜 본문 주소(260805 실측 사고 fail-2026-08-04-1528-idagw 봉합).

    네이버 블로그류는 본문을 **프레임 뒤에 숨긴다** — blog.naver.com/<id>/<no> 가 데스크톱 UA 엔
    2,859B iframe 셸(mainFrame → PostView.naver), 모바일 UA 엔 184B JS 리다이렉트
    (top.location.replace)만 준다 = UA 교대(SHELL_BYTES)로는 못 뚫는 축.
    → 셸(SHELL_BYTES 미만)일 때만 mainFrame iframe·JS 리다이렉트·meta refresh 의 목적지를 꺼낸다.
    가드 = 동일 사이트(마지막 2라벨 동일 · 광고 iframe 의 제3자 추적 차단) + 기존 _guard(SSRF)."""
    if len(raw) >= SHELL_BYTES:
        return ''
    t = raw.decode('utf-8', 'ignore').replace('\\/', '/')   # JS 문자열 이스케이프(https:\/\/…) 해제
    m = (re.search(r'<i?frame[^>]+(?:id|name)=["\']mainFrame["\'][^>]*\ssrc=["\']([^"\']+)', t, re.I)
         or re.search(r'<i?frame[^>]+src=["\']([^"\']+)["\'][^>]*(?:id|name)=["\']mainFrame["\']', t, re.I)
         or re.search(r'location(?:\.href\s*=|\.replace\()\s*["\']([^"\']{8,})', t, re.I)
         or re.search(r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+url=([^"\'>;\s]+)', t, re.I))
    if not m:
        return ''
    u = urllib.parse.urljoin(base, html.unescape(next(g for g in m.groups() if g)).strip())
    try:
        hu = (urllib.parse.urlparse(u).hostname or '').lower()
        hb = (urllib.parse.urlparse(base).hostname or '').lower()
        if not hu or not hb or hu.split('.')[-2:] != hb.split('.')[-2:]:
            return ''
    except Exception:
        return ''
    return u if _guard(u) else ''


def _cupid_pass(raw, ct, url):
    """cupid.js 봇월 껍데기면 쿠키를 만들어 재요청 — (raw, ct, final_url, note) · 미해당은 입력 그대로.

    [왜 UA 교대로는 안 되나] 챌린지 응답은 어느 UA 로도 같은 797B 스크립트다(실측). 통과의 조건은
    **쿠키 한 개**뿐이고 그 값은 페이지 안 a·b·c 로 결정론적으로 계산된다(shared/cupid_wall.py 참조).
    통과 뒤 이슈링크 `/community/go/<커뮤니티>/<id>` 는 302 로 실제 글로 가므로 그 최종 주소도 함께
    돌려준다 — 본선 WebFetch 가 봇월 주소가 아니라 실제 글 주소를 열게 하는 축(FRAMEURL_BLOCK).
    """
    if cupid_wall is None:
        return raw, ct, url, ''
    try:
        host = urllib.parse.urlparse(url).netloc
        if not cupid_wall.is_wall_host(host):
            return raw, ct, url, ''
        text = _decode(raw, ct)
        if not cupid_wall.is_challenge(text):
            return raw, ct, url, ''          # 이미 통과 페이지(쿠키 불요)
        cookie = cupid_wall.cookie_for(text)
        if not cookie:
            return raw, ct, url, cupid_wall.why_failed(text)
        sep = '&' if '?' in url else '?'
        raw2, ct2, fin = _get(url + sep + cupid_wall.RETRY_PARAM,
                              cookie='%s=%s' % (cupid_wall.COOKIE_NAME, cookie), ret_url=True)
        if len(raw2) <= len(raw):
            return raw, ct, url, 'cupid 재요청이 껍데기 — 봇월 포맷 변경 의심'
        return raw2, ct2, (fin or url), 'cupid 봇월 통과'
    except Exception as ex:   # noqa: BLE001 — 수확기 전 경로 fail-soft(통과 실패가 요약을 죽이지 않는다)
        return raw, ct, url, 'cupid 통과 예외: %s' % ex


def _get_page(url):
    """페이지 취득 — ① UA 교대(260804) ② cupid 봇월 쿠키 통과(260912) ③ 그래도 껍데기면 프레임 셸 해제 추적(260805 · 최대 2홉).
    반환 = (raw, ct, final_url) — final 은 실제 본문을 준 주소(봇월 통과 후 302 · 프레임 해제 결과 · 미해당이면 입력 그대로)."""
    raw, ct = _ua_swap_get(url)
    final = url
    raw, ct, final, wall = _cupid_pass(raw, ct, url)
    if wall:
        print('::warning::%s (%s)' % (wall, url), file=sys.stderr)
    for _ in range(FRAME_HOP_MAX):
        nxt = _frame_target(raw, final)
        if not nxt or nxt == final:
            break
        raw2, ct2 = _ua_swap_get(nxt, referer=final)
        if len(raw2) <= len(raw):
            break             # 해제해도 안 커지면 셸이 아니었던 것 — 원본 유지(오탐 0 지향)
        raw, ct, final = raw2, ct2, nxt
    return raw, ct, final, wall


def _decode(raw, ct):
    """fetch_article.sh charset 관용구 계승 — 한국 레거시 인코딩(EUC-KR/CP949) 오독 차단."""
    cs = (re.search(r'charset=["\']?([a-z0-9_-]+)', ct or '', re.I) or [None, ''])[1].lower()
    if not cs:
        m = re.search(rb'charset=["\']?([a-zA-Z0-9_-]+)', raw[:4096])
        cs = m.group(1).decode('ascii', 'ignore').lower() if m else ''
    if cs in ('euc-kr', 'euckr', 'ks_c_5601-1987', 'ksc5601', 'ksc_5601',
              'cp949', 'x-windows-949', 'windows-949', 'ms949'):
        return raw.decode('cp949', 'ignore')
    return raw.decode('utf-8', 'ignore')


def body_text(t):
    """fetch_article.sh 본문 파서 계승 — 스크립트·태그 제거 후 순수 텍스트 길이 측정용."""
    b = re.sub(r'(?is)<(script|style|noscript|head)[^>]*>.*?</\1>', ' ', t)
    b = re.sub(r'(?is)<br\s*/?>', '\n', b)
    b = re.sub(r'(?is)</(p|div|li|h\d|td|tr)>', '\n', b)
    b = re.sub(r'<[^>]+>', ' ', b)
    b = html.unescape(b)
    return re.sub(r'[ \t ]+', ' ', b).strip()


def dense_text(txt):
    """본문 줄만 남긴 밀집 텍스트 — `fetch_article.sh` 본문 선별 정본 관용구 계승(창작 0).

    정본 4축 그대로: ① 한글 20자 미만 줄 버림(내비·메뉴·잔재) ② 중복 줄 제거
    ③ 40줄 상한 ④ 문자 상한. 커뮤니티 페이지는 사이트 메뉴가 수백 줄이라(실측 mlbpark
    34,583자 중 앞 수천 자가 통째로 메뉴) 이 선별 없이 앞부분만 자르면 **본문이 한 줄도 안 실린다**.
    ⚠ 바이라인 면제 축은 안 가져온다 — 이 경로의 산출물은 '기자명 추출'이 아니라 '읽을 본문'이고,
      커뮤니티 글엔 바이라인이 없다(정본의 그 축은 기사 경로 전용 = 여기서 쓰면 잡음만 늘린다).
    """
    seen, keep = set(), []
    for l in (txt or '').split('\n'):
        l = re.sub(r'\s+', ' ', l).strip()
        if len(re.findall(r'[가-힣]', l)) < 20:
            continue
        if l in seen:
            continue
        seen.add(l)
        keep.append(l)
        if len(keep) >= DENSE_LINES:
            break
    return '\n'.join(keep)


def _meta_og_image(t):
    """sns_trends.py og:image 정본 2패턴(속성 순서 양방향)."""
    m = (re.search(r'<meta[^>]+(?:property|name)=["\']og:image(?::secure_url|:url)?["\'][^>]+content=["\']([^"\'>]+)', t, re.I)
         or re.search(r'<meta[^>]+content=["\']([^"\'>]+)["\'][^>]+(?:property|name)=["\']og:image(?::secure_url|:url)?["\']', t, re.I))
    return html.unescape(m.group(1)).strip() if m else ''


def candidates(page, base):
    """본문 이미지 후보 URL(등장 순서 유지·중복 제거) — 본문 <img> 우선, og:image 는 마지막 보루.

    ⚠️ 커뮤니티 페이지는 사이드바·추천·광고 썸네일이 본문보다 압도적으로 많다(실측 = 본문 2장 / 전체 79장).
    구분 축은 사이트별 컨테이너 클래스가 아니라 **본문 이미지는 크기를 지정하지 않는다**는 보편 성질:
    사이드바 썸네일은 width/height 를 작게 박아 격자에 끼워 넣는다(실측 78×54·height=45).
    → 작은 치수가 명시된 img 를 컷하면 사이트 지식 없이 본문만 남는다(짝 = 다운로드 후 바이트 하한)."""
    out, seen = [], set()
    for m in _IMG_TAG_RE.finditer(page):
        tag = m.group(0)
        sm = _IMG_SRC_RE.search(tag) or _LAZY_RE.search(tag)
        if not sm:
            continue
        dim = [int(d) for d in _DIM_RE.findall(tag)]
        if dim and min(dim) < THUMB_DIM:
            continue          # 작은 치수 명시 = 격자 썸네일(본문 아님)
        u = html.unescape(sm.group(1)).strip()
        if u.startswith('data:'):
            continue
        u = urllib.parse.urljoin(base, u)
        if u in seen:
            continue
        if JUNK_RE.search(urllib.parse.urlparse(u).path):
            continue
        if not IMG_EXT_RE.search(u) and '/image' not in u.lower():
            continue          # 확장자도 경로 힌트도 없으면 이미지 확신 불가 → 버림(오탐 0 지향)
        seen.add(u)
        out.append(u)
    og = _meta_og_image(page)
    if og:
        og = urllib.parse.urljoin(base, og)
        if og not in seen:
            out.append(og)
    return out


def harvest(url, outdir, max_n=MAX_DEFAULT, thin=THIN_DEFAULT, prefix='src'):
    res = {'ok': False, 'text_len': -1, 'saved': [], 'why': '', 'final': '', 'wall': '', 'text': ''}
    if not _guard(url):
        res['why'] = '차단·비정상 URL'
        return res
    raw, ct, final, wall = _get_page(url)
    res['final'] = final   # 프레임 해제·봇월 통과 결과 주소 — ask.sh 가 본선 프롬프트에 '실제 본문 주소'로 전달
    res['wall'] = wall     # 봇월 통과 사유 문구(빈 값 = 해당 없음) — 실패 알림·진단서가 원인 분류에 쓴다
    if not raw:
        res['why'] = '페이지 취득 실패(차단·타임아웃)'
        return res
    if 'html' not in (ct or '').lower() and not raw[:512].lstrip().lower().startswith((b'<!doctype', b'<html')):
        res['why'] = 'HTML 아님'
        return res
    page = _decode(raw, ct)
    txt = body_text(page)
    res['text_len'] = len(txt)
    # ⭐ 봇월을 통과해서 얻은 본문만 프롬프트에 전문으로 싣는다(260912 · 사고 봉합의 본체).
    #   [왜 봇월 축에만 주는가] 이 글은 **모델이 직접은 못 읽는다** — 본선의 WebFetch 도 같은 챌린지에
    #   막혀 0자를 받는다(실측). 그러니 스크립트가 확보한 본문을 넘겨주지 않으면 모델에게 남는 건 제목뿐이고,
    #   그 상태의 검색이 정확히 10분 예산을 태운 원인이다(fail-2026-09-12-0926).
    #   반대로 평범한 기사 URL 은 모델이 스스로 잘 열기 때문에 주입하지 않는다 = 종전 동작 보존(회귀 0 ·
    #   프롬프트 팽창 0). 상한은 커뮤니티 글 실측(3,006자)의 여유 배수.
    if wall:
        _dense = dense_text(txt)
        if len(_dense) >= WALL_TEXT_MIN:
            res['text'] = _dense[:WALL_TEXT_MAX]
    if thin and len(txt) >= thin:
        res['ok'] = True
        res['why'] = f'페이지 텍스트 {len(txt)}자≥{thin} — 수확 생략'
        return res

    os.makedirs(outdir, exist_ok=True)
    n = tried = 0
    for u in candidates(page, final):   # 상대경로 기준 = 실제 본문을 준 주소(프레임 해제 결과)
        if n >= max_n or tried >= TRY_MAX:
            break
        tried += 1
        blob, ict = _get(u, referer=url, limit=IMG_MAX_BYTES)
        if not blob or not (ict or '').lower().startswith('image/'):
            continue
        if len(blob) < IMG_MIN_BYTES or len(blob) > IMG_MAX_BYTES:
            continue
        w, h = px_size(blob)
        if w and h and min(w, h) < PX_MIN:
            continue          # 실측 픽셀이 작다 = 격자 썸네일·배너(본문 아님)
        ext = CT_EXT.get((ict or '').split(';')[0].strip().lower())
        if not ext:
            continue          # Claude Read 가 못 여는 포맷(svg·avif 등)은 넘긴다
        n += 1
        p = os.path.join(outdir, f'{prefix}-{n}{ext}')
        with open(p, 'wb') as fp:
            fp.write(blob)
        res['saved'].append(p)
    res['ok'] = True
    _w = f' · {wall}' if wall else ''
    _t = f' · 본문 전문 {len(res["text"])}자 전달' if res['text'] else ''
    res['why'] = ((f'본문 이미지 {n}장 수확(후보 {tried}장 시도 · 페이지 텍스트 {len(txt)}자{_w}{_t})'
                   if n else f'수확 가능한 본문 이미지 0장(후보 {tried}장 시도 · 페이지 텍스트 {len(txt)}자{_w}{_t})'))
    return res


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--resolve':
        # 프레임 해제 주소만 출력(이미지 수확 0) — ask.sh 링크 레일(article)이 같은 셸 함정을 밟지 않게
        # 해제기를 공용화(260805). 실패·미해제 = 빈 출력(호출부 fail-soft).
        try:
            if len(a) > 1 and _guard(a[1]):
                _, _, _fin, _ = _get_page(a[1])
                if _fin and _fin != a[1]:
                    print(_fin)
        except Exception:
            pass
        raise SystemExit(0)
    if len(a) < 2:
        print(json.dumps({'ok': False, 'text_len': -1, 'saved': [], 'why': 'usage'}, ensure_ascii=False))
        raise SystemExit(0)
    kw = {}
    for i, v in enumerate(a):
        if v == '--max' and i + 1 < len(a):
            kw['max_n'] = max(1, min(8, int(a[i + 1] or MAX_DEFAULT)))
        elif v == '--thin' and i + 1 < len(a):
            kw['thin'] = max(0, int(a[i + 1] or THIN_DEFAULT))
        elif v == '--prefix' and i + 1 < len(a):
            kw['prefix'] = re.sub(r'[^A-Za-z0-9_-]', '', a[i + 1]) or 'src'
    try:
        out = harvest(a[0], a[1], **kw)
    except Exception as e:   # fail-soft 절대 — 수확기가 요약 파이프를 죽이면 안 된다
        out = {'ok': False, 'text_len': -1, 'saved': [], 'why': f'예외: {type(e).__name__}'}
    print(json.dumps(out, ensure_ascii=False))
    raise SystemExit(0)
