#!/usr/bin/env python3
"""트렌드 카드 이미지 백필 — 구글 급상승 꼬리(비공식 API산 = picture 결측) 키워드에 관련 뉴스이미지 매칭
(운영자 260718 Q126 · more_images.py 미러 · "뉴스 요약의 이미지 받아오는 지점 재사용").

파이프: ① sns_trends.json 구글 급상승 picture 결측분 키워드 수집 → ② **무키 뉴스검색(LLM 0)** = 네이버 뉴스검색
(n.news.naver.com 기사 링크 · 1주 필터 → 전체) → 다음 뉴스검색(v.daum.net · ID 앞 14자리 = 발행시각 · 7일 내) 순으로
키워드별 후보 URL 최대 4개 → ③ thumb_gen og:image 추출 + _is_logo_card 컷(로고/'G' 브랜딩 차단) + R2 재호스팅
→ ④ picture 주입 → ⑤ sns_trends.json 재기록.

비용 = LLM 0(운영자 260909 «트렌드 저거는 llm 필요없는 일로» — 구판 = Sonnet WebSearch 배치 1콜 · 실측 7일 227콜·콜당 50만tok·
하루 $27 = 남은 구독 토큰의 49% · 키워드→기사 URL 은 판단이 아니라 검색이라 LLM 이 필요 없었다). 러너 실측: 네이버·다음 검색 HTML
전부 서버 렌더(200) · n.news.naver.com og:image 는 추출기 승격(800→1400)까지 통과 · 구글 뉴스 RSS 는 리다이렉트 ID 라 서버 해제 불가 ·
Bing RSS 는 msn.com 재호스팅뿐(og 0) = 둘 다 제외. 게이트(TREND_IMG=1 · 기본 ON).
안전 = 전부 fail-soft(무매칭·오류 = picture "" 유지 = 뷰어 로고 타일 폴백 · rc 항상 0 = 수집 커밋 비차단)."""
import os
import sys
import re
import json
import hashlib
import datetime as _dt
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import thumb_gen as tg   # __main__ 가드 有 = import 안전. fetch_article_images·http_image·r2_upload·_is_logo_card·_norm_key·R2_ON 재사용.

OUT = os.path.join("viewer", "sns_trends.json")
MAX_TARGETS = max(1, min(20, int(os.environ.get("TREND_IMG_MAX", "14") or "14")))   # 결측 대상 상한(꼬리 노출대 커버·LLM 예산 보호)
KST = _dt.timezone(_dt.timedelta(hours=9))
FAIL_TTL_H = max(0.0, float(os.environ.get("TREND_IMG_FAIL_TTL_H", "2") or "2"))   # 실패 키워드 재검색 유예(평의회 260812 권고3ⓒ · 0 = 유예 없음)


# ── 무키 뉴스검색 리졸버(LLM 0 · 운영자 260909) — 파서는 순수 함수(tests/test_trend_images.py 오프라인 회귀) ──
_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
       "Accept-Language": "ko-KR,ko;q=0.9"}
URLS_PER_KW = max(1, min(8, int(os.environ.get("TREND_IMG_URLS", "4") or "4")))   # 키워드당 후보 URL 상한(첫 성공에서 멈춤 = 대개 1~2 fetch)
DAUM_MAX_AGE_H = 24 * 7   # 다음 = ID 발행시각으로 7일 컷(급상승 키워드 = 최근 기사여야 사진이 사건과 맞는다)
_NAVER_RE = re.compile(r'https://n\.news\.naver\.com/mnews/article/\d+/\d+')
_DAUM_RE = re.compile(r'https?://v\.daum\.net/v/(\d{14})\d*')


def _http_text(url, timeout=12):
    """검색 페이지 GET → 본문 문자열(실패·비200 = "" · 호출부 fail-soft)."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=timeout) as r:
            if r.status != 200:
                return ""
            return r.read().decode("utf-8", "ignore")
    except Exception:  # noqa: BLE001
        return ""


def naver_news_urls(html):
    """네이버 뉴스검색 HTML → n.news.naver.com 기사 URL(검색 순서 유지 · 중복 제거).
    n.news.naver.com 만 잡는 이유 = 서버 렌더 + og:image 원본급(imgnews.pstatic.net · 추출기 승격 통과 실측 260909)."""
    return list(dict.fromkeys(_NAVER_RE.findall(html or "")))


def daum_news_urls(html, now_ts=None, max_age_h=DAUM_MAX_AGE_H):
    """다음 뉴스검색 HTML → v.daum.net 기사 URL(검색 순서 유지 · 중복 제거 · ID 앞 14자리 = KST 발행시각 → max_age_h 컷).
    시각 파싱 실패 = 통과(fail-open · 화질 컷이 뒤에서 거른다)."""
    now_ts = time.time() if now_ts is None else now_ts
    out, seen = [], set()
    for m in _DAUM_RE.finditer(html or ""):
        u = m.group(0)
        if u in seen:
            continue
        seen.add(u)
        try:
            pub = _dt.datetime.strptime(m.group(1), "%Y%m%d%H%M%S").replace(tzinfo=KST).timestamp()
            if (now_ts - pub) / 3600 > max_age_h:
                continue
        except Exception:  # noqa: BLE001
            pass
        out.append(u)
    return out


def resolve_news_urls(query, fetch=_http_text, limit=None):
    """키워드 → 대표 기사 후보 URL 목록(최대 limit · 네이버 1주 → 네이버 전체 → 다음 7일 순 · 중복 제거).
    검색 자체가 실패해도 예외 없이 빈 목록(호출부가 실패 유예 도장)."""
    limit = URLS_PER_KW if limit is None else limit
    q = urllib.parse.quote(query)
    out = []
    for u in (f"https://search.naver.com/search.naver?where=news&query={q}&sort=0&nso=so:r,p:1w,a:all",
              f"https://search.naver.com/search.naver?where=news&query={q}"):
        out += naver_news_urls(fetch(u))
        if len(dict.fromkeys(out)) >= limit:
            break
    if len(dict.fromkeys(out)) < limit:
        out += daum_news_urls(fetch(f"https://search.daum.net/search?w=news&q={q}"))
    return list(dict.fromkeys(out))[:limit]


def _fail_fresh(ts, now_iso):
    """실패 도장 ts가 유예(TTL) 안인가 — 안이면 이번 배치에서 재검색 제외(네거티브 캐시).
    구판은 실패 키워드를 무유예 재시도해 같은 키워드가 트렌드 체류시간 내내 회차마다 재검색됐다(평의회 260812 실측
    = 이론 필요 콜 3~8/일 vs 실측 59~75/일 = 낭비 85%+). 파싱 불가 = 유예 없음(재시도 허용 = fail-open)."""
    try:
        if not ts:
            return False
        return (_dt.datetime.fromisoformat(now_iso) - _dt.datetime.fromisoformat(str(ts))).total_seconds() < FAIL_TTL_H * 3600
    except Exception:
        return False


def _gate_on():
    return os.environ.get("TREND_IMG", "0").strip().lower() in ("1", "true", "yes", "on")


def main():
    if not _gate_on():
        print("TREND_IMG 게이트 OFF — 트렌드 이미지 백필 스킵(cron 기본)")
        return
    if not tg.R2_ON:
        print("::warning::R2 미설정 — 트렌드 이미지 백필 스킵(핫링크 회피 위해 R2 재호스팅 필수)")
        return
    try:
        d = json.load(open(OUT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print("::warning::sns_trends.json 로드 실패(스킵): {}".format(e))
        return

    # ── 재검색 절단 상태(평의회 260812 권고3ⓐⓒ) — 파일 안 "_trend_img" = {tried: 수집분 마커, fail: {키워드: 실패시각}} ──
    #   ⓐ 같은 수집분(updated)엔 LLM 1회만 — 신선도 스킵 런의 중복 발사(0811 실측 = 7분 간격 2콜 $3.03이 같은
    #   15키워드 재검색·백필 0) 차단. 상태는 수집 리빌드가 보존(sns_trends.py data 조립 carry) · 기계산출물 손편집 금지.
    st = d.get("_trend_img") if isinstance(d.get("_trend_img"), dict) else {}
    upd = str(d.get("updated") or "")
    if upd and st.get("tried") == upd:
        print("같은 수집분({}) 이미 시도됨 — LLM 스킵(권고3ⓐ · 새 수집분 도착 시 1회 재시도)".format(upd[:19]))
        return
    now_iso = _dt.datetime.now(KST).isoformat(timespec="seconds")

    gt = d.get("gtrends") or []
    # 대상 = picture 결측 + 검색어 有(주로 11~25위 API산). 이미 커버 있는 항목은 무접촉.
    targets = [g for g in gt if isinstance(g, dict) and not (g.get("picture") or "").strip() and (g.get("query") or "").strip()]
    # 실패 유예(TTL) 필터(권고3ⓒ) — 직전 시도에서 못 채운 키워드는 유예 동안 재검색 제외.
    _fails = st.get("fail") if isinstance(st.get("fail"), dict) else {}
    _ttl_cut = [g for g in targets if _fail_fresh(_fails.get((g.get("query") or "").strip()), now_iso)]
    if _ttl_cut:
        print("실패 유예 제외 {}건({}h): {}".format(len(_ttl_cut), FAIL_TTL_H, ", ".join((g.get("query") or "?") for g in _ttl_cut[:8])))
        targets = [g for g in targets if g not in _ttl_cut]
    targets = targets[:MAX_TARGETS]
    if not targets:
        print("결측 이미지 0 — 변경 없음")
        return

    queries = [g["query"].strip() for g in targets]
    qmap = {q: g for q, g in zip(queries, targets)}   # 마지막 동일 검색어 우선(중복 드묾)

    def _persist_state(fail_stamp_queries=()):
        # 시도 마커 + 실패 유예 도장(권고3ⓐⓒ) — 채움 0이어도 상태를 남겨야 같은 수집분 재발사·실패 재검색이 끊긴다.
        #   호출 자체가 실패한 경우(fail_stamp_queries 빈 튜플)는 키워드 탓이 아니므로 유예를 안 찍고 이 수집분만 봉인.
        st["tried"] = upd
        _keep = {q: ts for q, ts in ((st.get("fail") or {}) if isinstance(st.get("fail"), dict) else {}).items() if _fail_fresh(ts, now_iso)}
        for _q in fail_stamp_queries:
            _g0 = qmap.get(_q)
            if _g0 is None or not ((_g0.get("picture") or "").strip()):
                _keep[_q] = now_iso
        st["fail"] = _keep
        d["_trend_img"] = st
        json.dump(d, open(OUT, "w", encoding="utf-8", errors="replace"), ensure_ascii=False, indent=1)   # indent=1 = sns_trends.py 기록 포맷 미러(재포맷 차단)

    print("무키 뉴스검색(LLM 0) — 트렌드 키워드 {}개 → 기사 URL 후보(키워드당 ≤{})".format(len(queries), URLS_PER_KW), flush=True)
    pairs = []   # (검색어, [후보 URL…]) — 검색 실패·0건은 뒤에서 실패 유예 도장
    for q in queries:
        try:
            urls = resolve_news_urls(q)
        except Exception as e:  # noqa: BLE001
            urls = []
            print("  ⏭ 검색 실패({}): {}".format(q, str(e)[:80]))
        if urls:
            pairs.append((q, urls))
        else:
            print("  ⏭ 기사 0({})".format(q))

    if not pairs:
        print("URL 0 — 변경 없음(시도분 실패 유예 도장)")
        _persist_state(queries)
        return

    filled = 0
    for q, urls in pairs:
        g = qmap.get(q)
        if not g or (g.get("picture") or "").strip():
            continue
        cand = []
        for url in urls:   # 후보를 차례로 — og:image 가 나오는 첫 기사에서 멈춤(대개 1~2 fetch)
            try:
                cand = tg.fetch_article_images(None, image_sources=[url], want=1)   # og:image 추출(과금 0 · art_url=None → image_sources만)
            except Exception as e:  # noqa: BLE001
                print("  ⏭ fetch 실패({}): {}".format(q, str(e)[:80]))
                cand = []
            if cand:
                break
        for c in cand:
            src = c.get("src", "")
            if not src:
                continue
            try:
                b, ctype, ext = tg.http_image(src)
            except Exception:  # noqa: BLE001
                b = None
            if not b:
                continue
            if tg._is_logo_card(b):   # 매체 로고/브랜딩 카드(솔리드+텍스트) = 픽셀 컷(운영자 260622 · 'G' 타일류 차단)
                print("  ⏭ 로고/브랜딩 컷: {}".format(q))
                continue
            h = hashlib.sha1((src or "").encode("utf-8")).hexdigest()[:10]
            final = None
            try:
                final = tg.r2_upload(b, "trend/{}.{}".format(h, ext), ctype)
            except Exception as e:  # noqa: BLE001
                print("  ⏭ R2 업로드 실패({}): {}".format(q, str(e)[:80]))
            if final:
                g["picture"] = final
                if not g.get("news"):   # 카드 클릭 링크 보강(비었을 때만)
                    g["news"] = [{"title": "", "url": c.get("link") or url, "source": ""}]
                filled += 1
                print("  ✅ {} → {}".format(q, final), flush=True)
                break

    _persist_state(queries)   # 미채움 키워드 = 실패 유예 도장 · 채움분은 picture 실림(파일 기록은 이 한 곳)
    if filled:
        print("✅ 트렌드 이미지 {}개 백필 → {}".format(filled, OUT), flush=True)
    else:
        print("백필 0(로고컷·사진無·차단·중복) — 실패 유예 도장(재검색은 {}h 뒤)".format(FAIL_TTL_H))

    # 산출물 워치독(운영자 260730 "재발 안하려면?") — 이 스텝이 파이프의 마지막 커버 채움 지점이라
    # **최종 사용자 화면 상태**를 여기서 판정한다(코드 경로가 아니라 결과물을 감시 = 260729~30 '조용한 0' 재발 차단).
    # 대상 = 뷰어 TOP 스택 노출대 gt[:25](ggMap th 원천) · 임계 40% = 실측 근거: 정상 구간 4~6건(16~24% · 260730)
    # vs 사고 구간 15건(60% · 260729 gnews 미시도 사고) 사이 중간선 → 사고는 잡고 정상 변동엔 안 운다.
    _band = gt[:25]
    _miss = [g for g in _band if isinstance(g, dict) and not (g.get("picture") or "").strip()]
    _rate = (len(_miss) * 100 // max(1, len(_band)))
    _line = "gtrends 커버 최종: {}/{} 채움 · 결측 {}건({}%)".format(len(_band) - len(_miss), len(_band), len(_miss), _rate)
    if _rate >= 40:
        print("::warning::{} — 임계 40% 초과(백필 경로 열화 의심 · 결측 키워드: {})".format(
            _line, ", ".join((g.get("query") or "?") for g in _miss[:8])))
    else:
        print(_line)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001  — 최상위 fail-soft(어떤 예외도 수집 커밋 비차단 · rc 0)
        print("::warning::trend_images 예외(스킵): {}".format(e))
    sys.exit(0)
