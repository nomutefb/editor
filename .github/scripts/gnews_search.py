#!/usr/bin/env python3
"""구글 뉴스 검색 리졸버(LLM 0 · 키 0) — 요약이 뽑은 검색어(image_query·image_query_en·제목)로 **같은 사건을 다룬
다른 매체 기사 URL**을 찾는다. 그 기사들의 대표사진(og:image)이 곧 검색이미지 후보다(추출·화질 컷 = thumb_gen 재사용).

운영자 260925 «요약이 완료된 이후에 이미지를 찾게» + «구글 검색만 · 어떻게 검색해야 효과적일지» —
  구판 = 요약 본선(오퍼스)·병렬 사진로봇(소넷)·보충(moreimg, 소넷 WebSearch 콜당 약 138만 토큰)이 전부 LLM 웹검색이었다.
  「키워드 → 같은 사건 기사 URL」은 판단이 아니라 검색이라 LLM 이 필요 없다(trend_images.py 260909 선례와 같은 결론).

파이프: ① news.google.com/rss/search(검색 RSS · 서버 렌더) → 기사 링크 = 구글 리다이렉트 ID
        ② 기사 ID 페이지(news.google.com/rss/articles/<id>)의 서명(data-n-a-sg)·시각(data-n-a-ts)
        ③ batchexecute(Fbv4je · garturlreq) 로 원문 URL 해제 — 세 단계 모두 공개 웹 요청.
검색어 사다리(효과 순 · 실측 260925 = 최근 기사 4건 × 방식별 단독 검색 → 화질 컷 통과 장수):
  해외 사건 = 영문(image_query_en · US판) 4·4장 > 국문 image_query 2·2장 > 제목 2·3장 → 영문 먼저.
  국내 사건 = image_query 0~2장 · 제목 1~3장(음역이 특이한 image_query 는 0건 = 제목이 구제) → image_query 다음 제목.
  「최근 7일(when:7d)」 제한은 결과만 줄었다(0~2장) = 안 쓴다(구글 뉴스 정렬이 이미 최신 우선). 사다리는 목표 개수에 차면 멈춘다.
안전 = 전부 fail-soft(차단·형식 변경·타임아웃 = 빈 목록 → 호출부가 다른 러너 재시도 · LLM 은 구글이 응답할 때만). 해제된 URL 은 호출부가
  thumb_gen._url_ok(SSRF 게이트)로 다시 거른다. 파서는 순수 함수(tests/test_gnews_search.py 오프라인 회귀).
"""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
       "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"}
_LOCALE = {"ko": "hl=ko&gl=KR&ceid=KR:ko", "en": "hl=en-US&gl=US&ceid=US:en"}
_ITEM_RE = re.compile(r"<item>(.*?)</item>", re.S)
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
_LINK_RE = re.compile(r"<link>(https://news\.google\.com/rss/articles/[^<\s]+)</link>")
_SRC_RE = re.compile(r'<source url="([^"]*)"')
_SRCNAME_RE = re.compile(r'<source url="[^"]*">(.*?)</source>', re.S)
_PUB_RE = re.compile(r"<pubDate>(.*?)</pubDate>", re.S)
_HEADTAG_RE = re.compile(r"^\s*(?:[\[【<(（][^\]】>)）]{1,12}[\]】>)）]|\S{1,4}\))\s*")   # [단독]·[포토]·<속보>·(종합)·속보) 머리말
_SRC_TAIL_RE = re.compile(r"\s+-\s+[^-]{1,40}$")   # RSS 제목 끝 「 - 매체명」
_STOP = {"the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "with", "by", "from", "as", "after", "over", "into", "amid"}
# 포털 재게재(다음·네이트·네이버) = 원문과 같은 사진의 사본 — 원문 매체 결과와 겹쳐 자리만 먹는다(실측 260925)
_PORTAL_HOSTS = ("v.daum.net", "news.nate.com", "m.news.nate.com", "sports.news.nate.com", "n.news.naver.com", "m.news.naver.com",
                 "news.naver.com", "news.daum.net")   # _host 가 m./www. 를 떼므로 뗀 형태도 등재(평의회 260925)
_SAFE_URL_RE = re.compile(r"https?://[^\s\x00-\x1f\x7f\"'<>`]{1,2048}")
_SIG_RE = re.compile(r'data-n-a-sg="([^"]+)"')
_TS_RE = re.compile(r'data-n-a-ts="([^"]+)"')
_FLASH_RE = re.compile(r"^\s*[\[【(<]\s*(속보|단독\s*속보|1보|2보|breaking)\s*[\]】)>]", re.I)   # 속보 플래시 = og 가 배너(thumb_gen _is_breaking_article 과 같은 축)
_PUNCT_RE = re.compile(r"[\[\]【】「」『』‘’“”\"'…·|<>()\\]")   # 역슬래시 = frontmatter 이스케이프(\") 잔재
_EXAMPLE_IQ = ("삼성전자 반도체 평택공장",)   # 프롬프트 예시값 베낌 = 무시(thumb_gen.parse_md 가드와 대칭)
# 러너·봇 요청을 거의 항상 막는 매체(실측 260925 = 401/403) — 해제 요청 2회 + 본문 fetch 1회를 헛쓰고 자리만 먹는다.
_BLOCKED_HOSTS = ("reuters.com", "apnews.com", "bloomberg.com", "wsj.com", "ft.com", "nytimes.com", "ndtv.com")


def enabled():
    """게이트 GNEWS_IMG(기본 ON · '0' = 구글 뉴스 레인 끔 = 종전 동작 100% 복귀)."""
    return os.environ.get("GNEWS_IMG", "1").strip() != "0"


def rss_url(query, lang="ko"):
    return "https://news.google.com/rss/search?q={}&{}".format(urllib.parse.quote(query), _LOCALE.get(lang, _LOCALE["ko"]))


def _unescape(s):
    import html as _h
    s = re.sub(r"^<!\[CDATA\[(.*)\]\]>$", r"\1", (s or "").strip(), flags=re.S)
    return _h.unescape(s).strip()


def parse_rss(xml):
    """검색 RSS → [{title, link, source}] (검색 순서 유지 · 링크 없는 항목 제외)."""
    out = []
    for it in _ITEM_RE.findall(xml or ""):
        lm = _LINK_RE.search(it)
        if not lm:
            continue
        tm = _TITLE_RE.search(it)
        sm = _SRC_RE.search(it)
        pm = _PUB_RE.search(it)
        nm = _SRCNAME_RE.search(it)
        out.append({"title": _unescape(tm.group(1)) if tm else "", "link": lm.group(1),
                    "source": _unescape(sm.group(1)) if sm else "", "pub": _pub_ts(pm.group(1)) if pm else 0,
                    "sname": _unescape(nm.group(1)) if nm else ""})
    return out


def _pub_ts(s):
    """RSS pubDate(RFC 822) → epoch 초(파싱 실패 = 0 = 나이 판정 보류)."""
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s.strip()).timestamp()
    except Exception:  # noqa: BLE001
        return 0


def _tokens(s):
    """관련성 대조용 토큰 — 2자 이상 어절(소문자) · 영문 불용어·4자리 연도 제외(of·in 만으로 다른 사건 통과 = 실측 260925)."""
    return {w for w in re.findall(r"[0-9A-Za-z가-힣]{2,}", (s or "").lower())
            if w not in _STOP and not re.fullmatch(r"(19|20)\d\d", w)}


def norm_title(t):
    """RSS 제목 정규화 — 끝 「 - 매체」·머리말·기호 제거(같은 기사 사본 판정·관련성 대조 공용)."""
    return clean_query(_SRC_TAIL_RE.sub("", t or "")).lower()


def relevant(query, title, lang="ko"):
    """검색 결과 제목이 검색어 핵심 어절을 충분히 공유하나(= 같은 사건).
    ⚠️ 제목 검색은 흔한 단어(소주·아빠·징역형)만으로도 다른 사건을 끌어온다(실측 260925 = 9/2 스포츠 기사) → 겹침 2개.
    ⚠️ 영문 긴 검색어(5어절+)는 인물 이름 2어절(Xi Jinping)만으로 다른 사건(방미)이 통과했다(실측 260925) → 겹침 3개.
       국문은 조사가 붙어 어절 일치가 덜 나오므로(분유를·분유) 2개 유지 — 올리면 같은 사건 기사까지 떨어진다."""
    qt = _tokens(query)
    if not qt:
        return False   # 대조 어절 0(비라틴·1자 어절뿐) = 판정 불가 → 무관 취급(구 True = 필터가 꺼져 무관 사진 통과 · 260925 평의회)
    need = 3 if (lang == "en" and len(qt) >= 5) else 2
    tt = _tokens(norm_title(title))
    hit = sum(1 for q in qt if any(t.startswith(q) for t in tt))   # 접두 일치 = 조사·어형 흡수(브릭스에·capsizes · 실측 누락 18/100 봉합)
    return hit >= min(need, len(qt))


def article_id(link):
    """구글 뉴스 링크 → 기사 ID(없으면 '')."""
    m = re.search(r"/articles/([A-Za-z0-9_-]+)", link or "")
    return m.group(1) if m else ""


def extract_sig(html):
    """기사 ID 페이지 → (서명, 시각) 또는 None."""
    s, t = _SIG_RE.search(html or ""), _TS_RE.search(html or "")
    return (s.group(1), t.group(1)) if s and t else None


def batch_body(gid, ts, sig):
    """batchexecute 요청 본문(form-urlencoded bytes)."""
    inner = ('["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
             '"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{}",{},"{}"]').format(gid, ts, sig)
    return urllib.parse.urlencode({"f.req": json.dumps([[["Fbv4je", inner, None, "generic"]]])}).encode()


def parse_batch(text):
    """batchexecute 응답 → 원문 URL('' = 해제 실패). 응답 = )]}' 머리 + 빈 줄 + JSON 배열."""
    try:
        chunk = (text or "").split("\n\n", 1)[1]
        rows = json.loads(chunk)
        for row in rows:
            if isinstance(row, list) and len(row) > 2 and row[0] == "wrb.fr" and row[2]:
                u = json.loads(row[2])[1]
                if isinstance(u, str) and _SAFE_URL_RE.fullmatch(u):   # 공백·제어문자·따옴표 섞인 URL 거부(로그 명령 주입·파서 혼동 · 260925 평의회)
                    return u
    except Exception:  # noqa: BLE001
        pass
    return ""


STATS = {"ok": 0, "fail": 0, "why": "", "hard": False}   # 구글 응답 성패 집계(프로세스 누적) — 전부 실패 = 차단 의심(호출부가 경고 · 다른 러너 재시도 발사)
#   why = 마지막 실패 사유(http429·timeout·host:consent.google.com·empty·URLError:gaierror …) — 경고에 실어 차단·동의 페이지·망 지연을 가른다(260925 #354 실측 = 사유 무기록)
#   hard = 확정 차단(429·구글 밖 리다이렉트 = sorry·동의 페이지) — 이 프로세스는 구글을 더 두드리지 않는다(막힌 IP 연타 = 차단 연장 · 헛대기 · 평의회 260925)


def blocked():
    """구글 요청을 했는데 성공이 0건 = 차단·형식 변경 의심(결과 0건과 구분)."""
    return STATS["fail"] > 0 and STATS["ok"] == 0


def _hard_block(why):
    return why.startswith("http429") or "@" in why or why.startswith("host:")


def _http(url, data=None, headers=None, timeout=12):
    if STATS.get("hard"):   # 확정 차단 뒤 = 네트워크 0 · 실패로만 센다(기사별 차단 판정 = 호출부 스냅숏 대조)
        STATS["fail"] += 1
        return ""
    r = _http_raw(url, data, headers, timeout)
    STATS["ok" if r else "fail"] += 1
    if not r and _hard_block(STATS.get("why") or ""):
        STATS["hard"] = True
    return r


def _http_raw(url, data=None, headers=None, timeout=12):
    h = dict(_UA)
    h.update(headers or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=timeout) as r:
            host = urllib.parse.urlparse(r.geturl()).hostname or ""
            if r.status != 200 or host != "news.google.com":
                STATS["why"] = "http%d" % r.status if host == "news.google.com" else "host:" + host
                return ""   # 리다이렉트로 구글 밖(동의 페이지·타 호스트)에 닿으면 버린다 = 이 모듈은 news.google.com 만 말한다
            body = r.read(2_000_000).decode("utf-8", "ignore")
            if not body:
                STATS["why"] = "empty"
            return body
    except urllib.error.HTTPError as e:
        host = urllib.parse.urlparse(e.geturl() or url).hostname or ""
        STATS["why"] = "http%d" % e.code + ("" if host == "news.google.com" else "@" + host)   # google.com/sorry = 429@www.google.com(IP 차단)
        return ""
    except Exception as e:  # noqa: BLE001
        _r = getattr(e, "reason", None)   # URLError = DNS·연결 거부·SSL 을 한 겹 감싼다 → 속 원인 클래스명
        STATS["why"] = ("timeout" if "timed out" in str(e) or isinstance(e, TimeoutError) or isinstance(_r, TimeoutError)
                        else type(e).__name__ + (":" + type(_r).__name__ if isinstance(_r, BaseException) else ""))
        return ""


def decode(link, http=_http):
    """구글 뉴스 링크 → 원문 URL('' = 실패). 요청 2회(ID 페이지 + batchexecute)."""
    gid = article_id(link)
    if not gid:
        return ""
    sig = extract_sig(http("https://news.google.com/rss/articles/" + gid))
    if not sig:
        return ""
    return parse_batch(http("https://news.google.com/_/DotsSplashUi/data/batchexecute",
                            data=batch_body(gid, sig[1], sig[0]),
                            headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}))


def _fm(md_text, key):
    m = re.search(r'^{}:\s*"(.*)"\s*$'.format(re.escape(key)), md_text or "", re.M)
    return (m.group(1) if m else "").strip()


def clean_query(q):
    """검색어 정리 — 괄호·따옴표·말줄임 제거 · 공백 정규화 · 속보 머리 제거(너무 긴 제목은 앞 12어절)."""
    q = q or ""
    for _ in range(3):   # 머리말 여러 개([단독][포토]) 연쇄 제거
        q2 = _HEADTAG_RE.sub("", q)
        if q2 == q:
            break
        q = q2
    q = _PUNCT_RE.sub(" ", q)
    words = q.split()
    return " ".join(words[:12])


def _cap(q, n):
    return " ".join(q.split()[:n])


def build_queries(md_text):
    """기사 md(frontmatter) → 검색어 사다리 [(query, lang)] (중복 제거 · 빈 값 제외 · 순서 = 실측 효과 순 · 모듈 docstring).

    image_query = 요약 모델이 기사를 다 읽고 뽑은 「이 사건의 고유명사 2~4개」 → 같은 사건 기사를 가장 좁게 잡는다.
    image_query_en = 해외 사건일 때만 채워진다(국내면 빈 값) → 채워져 있으면 외신 원본 사진(대개 고해상도)이 1순위."""
    iq = _fm(md_text, "image_query")
    if iq in _EXAMPLE_IQ:
        iq = ""
    iqe = _fm(md_text, "image_query_en")
    title = _fm(md_text, "title_ko") or _fm(md_text, "title")
    ladder = []
    if iqe and re.search(r"[A-Za-z]{2,}", iqe):          # 영문판 검색은 로마자만(비라틴 = US판 0건·관련성 대조 불가 · 실측 4/354건)
        ladder.append((_cap(clean_query(iqe), 6), "en"))
    if iq:
        ladder.append((_cap(clean_query(iq), 4), "ko"))   # 길수록 0건(실측 = 12어절 0건 · 3어절 10건 · 기존 905건 중 590건이 5어절+)
    if title:
        ladder.append((clean_query(title), "ko"))
    if iq and len(clean_query(iq).split()) > 3:
        ladder.append((_cap(clean_query(iq), 3), "ko"))   # 마지막 = 더 넓게(앞 3어절)
    seen, out = set(), []
    for q, lang in ladder:
        k = (q.strip(), lang)
        if q.strip() and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def _blocked(host):
    return any(host == b or host.endswith("." + b) for b in _BLOCKED_HOSTS)


def _host(u):
    try:
        h = (urllib.parse.urlparse(u).hostname or "").lower()
    except ValueError:   # 'http://[abc' 류 = 그 항목만 무시(레인 전체 중단 금지)
        return ""
    for p in ("www.", "m.", "mobile.", "amp."):
        if h.startswith(p):
            h = h[len(p):]
    return h


MAX_AGE_D = float(os.environ.get("GNEWS_MAX_AGE_D", "10") or "10")   # 이보다 오래된 결과 = 다른(옛) 사건일 확률이 높아 제외
MAX_DECODE = 24          # 기사당 해제 시도 상한(요청 2회/건) — 실패가 limit 에 안 잡혀 요청이 늘어지는 것 차단
BUDGET_S = float(os.environ.get("GNEWS_BUDGET_S", "60") or "60")   # 기사당 검색·해제 시간 상한(초) — 넘으면 모은 만큼만


def ref_ts(md_text):
    """기사 기준 시각(frontmatter date YYYY-MM-DD 정오 KST · 없거나 형식 불량 = 0 → 호출부가 현재 시각).
    ⚠️ 나이 필터는 「오늘」이 아니라 「그 기사 날짜」 기준이어야 한다 — 옛 기사를 픽하면(실측 260925 = 2025-09-24 화재 기사)
       오늘 기준으론 같은 사건 보도가 전부 1년 전이라 0건이 된다."""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", _fm(md_text, "date"))
    if not m:
        return 0
    try:
        import datetime as _dt
        d = _dt.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 12, tzinfo=_dt.timezone(_dt.timedelta(hours=9)))
        return d.timestamp()
    except Exception:  # noqa: BLE001
        return 0


def search_urls(queries, exclude=(), limit=10, http=_http, pause=0.25, now_ts=None, self_titles=()):
    """검색어 사다리 → 원문 기사 URL 목록(최대 limit · 매체당 1건 · exclude·속보 제외 · 검색 순서 유지).

    매체당 1건 = 같은 매체 연속 기사는 대개 같은 사진이라 자리만 먹는다(다른 매체 = 다른 각도 사진 확률 ↑).
    관련성 = 결과 제목이 검색어 핵심 어절 공유(relevant) + 발행이 기준 시각(now_ts = 기사 날짜 · 없으면 지금) ±MAX_AGE_D(10일)
      = 같은 사건만(옛 사건 사진 혼입 차단).
    exclude =이미 쓴 원문·같은 사건 타매체(alt_urls)·기존 검색이미지 출처(끝 '/' 무시 비교)."""
    ex = {(u or "").rstrip("/") for u in exclude if u}
    ex_hosts = {_host(u) for u in ex if _host(u)}   # 이미 쓴 매체 = 같은 사진 재사용 확률이 높아 다른 매체부터
    now = time.time() if now_ts is None else now_ts
    t_end = time.time() + BUDGET_S
    out, tried, fails = [], set(), 0
    seen_titles = {norm_title(t) for t in self_titles if t}   # 원문과 같은 제목 = 같은 기사 사본(같은 사진) → 제외
    for q, lang in queries:
        if len(out) >= limit or len(tried) >= MAX_DECODE or time.time() > t_end:
            break
        items = parse_rss(_http_cached(rss_url(q, lang), http))
        for it in items:
            if len(out) >= limit or len(tried) >= MAX_DECODE or time.time() > t_end:
                break
            if it["link"] in tried or _FLASH_RE.search(it["title"]):
                continue
            if it["pub"] and abs(now - it["pub"]) > MAX_AGE_D * 86400:   # 기준 시각 ±MAX_AGE_D(기사 날짜 기준 · 호출부 now_ts)
                continue
            if not relevant(q, it["title"], lang):
                continue
            tried.add(it["link"])
            src_host = _host(it["source"])
            if src_host and (src_host in ex_hosts or _blocked(src_host) or src_host in _PORTAL_HOSTS):
                continue
            nt = norm_title(it["title"])
            if nt and nt in seen_titles:   # 통신사 전재·포털 사본 = 같은 제목 = 같은 사진
                continue
            u = decode(it["link"], http=http)
            if pause:
                time.sleep(pause)
            fails = 0 if u else fails + 1
            if fails >= 3:   # 연속 3회 해제 실패 = 차단·형식 변경 의심 → 더 두드리지 않는다
                return out
            if not u or u.rstrip("/") in ex:
                continue
            h = _host(u)
            if h in ex_hosts or _blocked(h) or h in _PORTAL_HOSTS:
                continue
            if nt:
                seen_titles.add(nt)
            ex_hosts.add(h)
            if src_host:
                ex_hosts.add(src_host)
            ex.add(u.rstrip("/"))
            out.append(u)
    return out


_RSS_CACHE = {}


def _http_cached(url, http):
    if url in _RSS_CACHE:
        return _RSS_CACHE[url]
    r = http(url)
    if r:   # 실패('')는 캐시하지 않는다(같은 프로세스 다음 기사에서 재시도)
        _RSS_CACHE[url] = r
    return r


def find_original(title, media="", http=_http, now_ts=None):
    """원문 URL 찾기(LLM 0 · 260925) — 요약 frontmatter url 이 빈 기사(요약 요청·차단 매체)의 **바로 그 기사** 주소.
    채택 조건(평의회 260925 실측 = 통신사 제목 전재·같은 매체 같은 제목 다른 기사가 흔하다):
      ① 매체명이 있어야 한다(없으면 같은 제목 중 누가 원문인지 모른다 = '')
      ② 결과 제목(끝 「 - 매체」 제거·정규화) == 우리 제목 ③ 결과 매체명 == 우리 매체명(공백 무시 완전 일치 · 부분일치 금지 =
         「연합뉴스TV」↔「연합뉴스」 오채택 차단) ④ 기사 날짜 ±1일 ⑤ 그 조건을 만족하는 결과가 **정확히 1건**(2건+ = 애매 = '')
    애매하면 '' (지어내기 0 · 호출부가 종전 Claude 임무로 폴백). 포털 사본은 원문이 아니라 제외."""
    nt = norm_title(title)
    med = re.sub(r"\s+", "", (media or "")).lower()
    if not nt or len(nt) < 8 or not med:
        return ""
    now = time.time() if now_ts is None else now_ts
    lang = "ko" if re.search(r"[가-힣]", title or "") else "en"   # 영문 제목(외신) = 영문판 검색
    hits = []
    for it in parse_rss(_http_cached(rss_url(clean_query(title), lang), http))[:15]:
        if it["pub"] and abs(now - it["pub"]) > 86400 * 1.5:   # 기사 날짜(정오 KST) ±1.5일 = 발행일 ±1일
            continue
        if norm_title(it["title"]) != nt:
            continue
        if re.sub(r"\s+", "", it.get("sname", "")).lower() != med:
            continue
        if _host(it["source"]) in _PORTAL_HOSTS:
            continue
        hits.append(it)
    if len(hits) != 1:
        return ""
    u = decode(hits[0]["link"], http=http)
    return u if u and _host(u) not in _PORTAL_HOSTS else ""
