#!/usr/bin/env python3
"""cupid.js(SlowAES JS 쿠키) 봇월 통과 — **정본 1곳**(260912).

[왜 공용 부품인가 = 260912 실측 사고 fail-2026-09-12-0926]
  SNS 카드 「전송」 → 이슈링크 커뮤니티 글(맘다니 뉴욕시장) → exit 124(21분 시간 초과).
  분해: 전송 페이로드 srcUrl = 이슈링크 `/community/go/<커뮤니티>/<id>` 주소 →
  수확기(ask_srcimg.py)가 리다이렉트 주소는 뽑았으나 **쿠키 절차를 몰라** 같은 797B 챌린지
  껍데기를 다시 받아 페이지 텍스트 0자 → 본선은 원문을 한 글자도 못 보고 제목만으로 검색 시작
  → effort max 600s 초과 → 재시도 또 초과.
  ⚠ 사고의 정체 = '사이트가 막았다'가 아니다. **통과 코드를 이 레포가 이미 갖고 있었다**
  (scraper/social_burst.py `_get_cupid` · 260625 · 같은 도메인 · 같은 챌린지).
  실측 대조: 같은 주소를 그 코드로 열면 실제 글로 302 되고 한글 3,006자 본문이 나온다.
  → 사본을 늘리지 않고 **복호 핵심만 여기로 정본화**해 두 호출부가 같은 것을 쓴다.

[챌린지 구조 = 결정론적 SlowAES(무료·무키·계정 무관)]
  챌린지 페이지 스크립트에 a=키·b=IV·c=암호문(각 1블록 hex)이 박혀 있고,
  쿠키 CUPID = hex(AES-128-CBC-decrypt(c, key=a, iv=b)) 한 값이면 `?ckattempt=1` 재요청이 통과한다.
  (1블록 CBC = AES-ECB-dec(c, a) XOR b — 블록이 하나라 패딩·체이닝 상태가 없다.)

[전송계층은 호출부 몫 = 이 모듈은 HTTP 를 모른다]
  social_burst 는 requests.Session(쿠키 자동), ask_srcimg 는 표준 urllib(Cookie 헤더 수동)로
  서로 다르다. 그 차이를 흡수하려고 한쪽 전송계층을 다른 쪽에 이식하면 두 경로 다 위험해진다
  → 여기서는 **감지·복호만** 책임지고(순수 함수 · 부작용 0), 쿠키를 어떻게 실어 보낼지는 호출부가 정한다.

[의존성 = pycryptodome 있으면 통과, 없으면 종전 동작(fail-soft)]
  news-ask.yml·social-scan.yml 이 설치를 배선한다. 미설치 환경에서는 None 을 돌려주고
  호출부는 챌린지 페이지 그대로 진행한다 = 이 모듈 도입 전과 바이트 동일(회귀 0).
"""
import re

# 챌린지 스크립트의 a·b·c 추출(정본 = scraper/social_burst.py `_CUPID_RE` 260625 실측 포맷 이동)
CHALLENGE_RE = re.compile(
    r'a\s*=\s*toNumbers\("([0-9a-fA-F]+)"\)\s*,\s*'
    r'b\s*=\s*toNumbers\("([0-9a-fA-F]+)"\)\s*,\s*'
    r'c\s*=\s*toNumbers\("([0-9a-fA-F]+)"\)')

# 이 봇월을 쓰는 호스트(실측 260625 이슈링크 · 서브도메인 포함 판정) — 호출부가 '이 도메인만' 절차를
# 타게 해 무관 사이트에 불필요한 재요청이 나가지 않게 한다(오버헤드 0 지향).
WALL_HOSTS = ('issuelink.co.kr',)

COOKIE_NAME = 'CUPID'
RETRY_PARAM = 'ckattempt=1'


def is_wall_host(host):
    """호스트가 cupid 봇월 사이트인가(서브도메인 포함)."""
    h = (host or '').strip().lower().split('@')[-1].split(':')[0]
    return any(h == d or h.endswith('.' + d) for d in WALL_HOSTS)


def is_challenge(text):
    """받은 본문이 cupid 챌린지 페이지인가(실측 797B 껍데기 = toNumbers 호출을 포함)."""
    return 'toNumbers(' in (text or '')


def cookie_for(text):
    """챌린지 본문 → CUPID 쿠키 값(hex) · 실패·미설치는 None(호출부 fail-soft).

    반환값을 그대로 쿠키 CUPID 에 넣고 RETRY_PARAM 을 붙여 재요청하면 통과 페이지가 온다.
    """
    m = CHALLENGE_RE.search(text or '')
    if not m:
        return None                      # 포맷 변경 = 상위에서 경고(조용한 0건 금지)
    try:
        from Crypto.Cipher import AES    # pycryptodome — 미설치 = 종전 동작
    except Exception:
        return None
    try:
        a, b, c = (bytes.fromhex(x) for x in m.groups())
        return AES.new(a, AES.MODE_CBC, b).decrypt(c).hex()
    except Exception:
        return None


def why_failed(text):
    """cookie_for 가 None 을 준 사유 문구(로그·진단서용 · 원인 3분류를 뭉개지 않는다)."""
    if not CHALLENGE_RE.search(text or ''):
        return 'cupid 챌린지 파싱 실패 — 포맷 변경 가능'
    try:
        from Crypto.Cipher import AES  # noqa: F401
    except Exception:
        return 'pycryptodome 미설치 — cupid 우회 불가'
    return 'cupid 복호 실패'
