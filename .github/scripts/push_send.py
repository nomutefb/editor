#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 긴급(breaking) 속보 웹푸시 발송 — candidates.json의 새 isBreaking 사건을 구독자에게 pywebpush로.
# dedup = push/sent.json(이미 보낸 키). 죽은 구독(404/410) 자동 정리. 비치명(실패해도 파이프 안 깸).
# env: VAPID_PRIVATE_KEY(raw base64url)·VAPID_PUBLIC_KEY·VAPID_SUBJECT. 인자 --test = 구독자 전원 테스트 1발.
# 정본 설명 = CLAUDE.md §🚨. 푸시 기준(앱푸시긴급) = breaking_judge AND grade≥2(운영자 260818 «내부에서는 자동으로 긴급처리가 되는데 웹앱 푸쉬 알림 [안 온다]» — 🚨배지·자동픽[grade≥2]과 같은 문턱으로 하향 = 내부 긴급처리와 푸시가 같은 사건을 본다 · 구 260622 grade≥3[뷰어 isAlert 동일선상]은 역사 · 실측 260818 = 24h 속보 5건 중 4건이 g=2라 내부 처리만 되고 푸시 0이 «긴급이 안 온다»의 실체) AND cross≥PUSH_MIN AND 최신(<4h).
# ⚠️ 푸시는 되돌릴 수 없다(발송=회수 불가) → 뷰어 점등(가역)보다 *더* 보수적: grade 미채점(None)은 푸시 안 함
#    (뷰어는 None도 점등=즉시·가역) · 다매체 검증 cross≥PUSH_MIN_CROSS 필수 · dedup=event_key+제목해시(중복발송 차단).
import json, os, re, sys, time, base64, hashlib, tempfile, datetime as dt
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent.parent
SUBS = ROOT / "push" / "subscriptions.json"
SENT = ROOT / "push" / "sent.json"
CAND = ROOT / "viewer" / "candidates.json"
NOTIF_ICONS = ROOT / "assets" / "brand" / "notif_dataurl.json"   # 종류별 아이콘 data URL 번들(생성 = shared/build_notif_icons.py)
# ── 소리·진동을 싣는 축(운영자 260819 «브레이브랑 워치 알림 있는거 배선하자») ─────────────────────
# ⚠️ 우리 알림은 여태 **제목·본문·아이콘·묶음표만** 실어 보냈다 = 소리·진동이 전적으로 폰 설정에 달려 있었고,
#    그 채널이 조용하면 알림은 뜨는데 손목까지 안 올라가는 경우가 있다(운영자 «웹 푸시는 오는데 소리나 진동이
#    안 나는건»). 웹 표준이 주는 수단 = `vibrate`(진동 패턴)와 `renotify`(같은 묶음표로 교체될 때 다시 울림).
# ⚠️ **전 종류에 싣는다**(운영자 260819 «진동 모든 건데 다 오게해주셈») — 구판은 긴급·이슈 둘만이었다.
#    그 판단의 근거였던 「이슈가 혼자 긴급 느낌」(260818)은 **색·문구 축**이고, 진동은 「왔다는 걸 알아채는가」
#    축이라 갈래가 다르다 = 색으로 급을 나누고 진동으로는 전부 알린다(운영자 판단).
# ⚠️ 이건 **요청**이지 보장이 아니다 — 안드로이드 알림 채널이 무음·중요도 낮음이면 그쪽이 이긴다(폰 설정 축).
# 되돌리기 = 이 집합을 {"brk","iss"}로 좁히면 종전 동작(구조 무변).
ALERT_KINDS = {"brk", "iss", "make", "sys", "trend", "kw"}
VIBRATE = [200, 100, 200]   # 짧게-쉬고-짧게 = 문자 알림과 같은 결(긴 진동은 손목에서 과하다)
PAYLOAD_MAX = 3900   # 웹푸시 페이로드 실효 한도 4KB — 초과분은 아이콘을 떼고 보낸다(알림 자체가 사라지는 것보다 낫다)
FAST_MAX_H = 4   # 최신 긴급만 푸시(뷰어 토스트와 동일 단일상수 정신)
PUSH_MIN_CROSS = int(os.environ.get("PUSH_MIN_CROSS", "2"))   # 푸시 최소 교차매체(다매체 검증 = 오발송 가드 · MIN_CROSS 바뀌어도 푸시 하한 고정)
PUSH_PUB_MAX_H = float(os.environ.get("PUSH_PUB_MAX_H", "8"))   # 발행 나이 상한 — 24→8h 조임(운영자 260722 · 실측: 재수집 뒷북 3발[발행 19.5~24h·first_seen 방금]이 24h 캡을 통과해 오발송 — 8h = 구주석 '8~12h 조임' 하단 = 관측 오발 전부 차단 + syndication 지연(4h+) 2배 완충). first_seen 전환의 뒷북 완충. ⚠️ 입력 = 현재 rep 기사 발행 나이(사건 나이 아님 · 검4-3)
SENT_TTL_H = float(os.environ.get("PUSH_SENT_TTL_H", "48"))   # 발송 원장 TTL — 무기한이면 '北 미사일 발사'류 템플릿 반복 헤드라인의 *별개 새 사건*이 제목해시 충돌로 영구 오억제(분신술 260710 검증6 · autopick.json 48h 정리와 대칭)
SENT_EV = ROOT / "push" / "sent_events.json"   # 발송 사건 시그니처 [{ts,title,key}] — 사건 단위 dedup(같은 실제 사건의 *다른 후속 기사* 재푸시 차단 · Q437 운영자 260722 "같은 사건이면 한 번만" · autopick_events.json 쌍둥이). 창 = SENT_TTL_H 재사용.
MAX_AI_DEDUP = int(os.environ.get("PUSH_MAX_AI", "8"))   # 런당 AI 사건중복 판정 콜 상한(폭주 가드 · autopick MAX_AI_DEDUP 짝)

# ── ⚡이슈 푸시(운영자 260818 «긴급은 아닌데 매체가 몰리는 건 이슈도 표기를 긴급처럼 노랑으로 푸시를 띄울게 ·
#    매체가 지속적으로 붙으면서 힘이 생긴건데 강조에 대한 알림이 없어서 놓친다 · 조금 늦어도 되는데 많이 늦으면
#    흐름을 뺏긴다 · 일단은 다 받아봄 차라리 많이 와서 안놓치는게 나으니까») ─────────────────────────────
# ⚠️ 긴급(속보 판정)과 **다른 축**이다 — 이건 속보로 안 잡혔는데 매체가 몰린 건이고, 화면 ⚡이슈 배지와 같은 술어다.
# ⚠️ 판정 규칙은 **화면 정본(build-viewer.mjs issEligible·viewer scBadgeType)의 언어 이식 사본**이다(js↔py라 사본이
#    물리적으로 불가피 · restore_paste_url 선례) — 한쪽만 고치면 배지와 푸시가 서로 다른 사건을 말한다.
#    동기 강제 = check_refs.check_issue_push_parity(값 4종·정형컷 3종을 양쪽에서 함께 본다).
ISS_PUSH = (os.environ.get("ISS_PUSH", "1").strip() != "0")   # 킬스위치 — 0이면 이슈 푸시만 끈다(긴급 무접촉)
ISS_CROSS_MIN = int(os.environ.get("ISS_PUSH_CROSS", "10"))   # 매체 하한 = 화면 배지 정본 ISS_CROSS_MIN 사본(값 창작 0)
ISS_G3_CROSS = 8                                              # grade3(대형)만 옛 임계 8 유지 = 정본 동일
# ⚠️ **푸시 문턱은 배지 자격보다 높다**(운영자 260818 «이슈 매체 20을 알림 조건으로 · 이슈중에 15 && 6시간 이내»)
#    — 화면 ⚡배지는 매체 10부터 붙지만(그건 눈으로 훑는 목록이라 넓어도 된다) **폰을 울리는 건 더 좁혀야 한다**.
#    두 갈래 OR = ⓐ 매체 20↑ = 이미 확실히 큰 건(시간 무관) ⓑ 매체 15↑ ∧ 6시간 이내 = 아직 크진 않은데
#    **지금 붙고 있는 중** = 흐름을 뺏기기 전에 알아야 하는 자리(운영자 «많이 늦으면 흐름을 뺏긴다»).
#    ⚠ 배지 자격(매체 10) 자체는 무접촉 = 화면은 종전대로 넓게 본다(푸시만 좁힌 것 = 두 축이 다른 게 의도).
ISS_PUSH_CROSS_HI = int(os.environ.get("ISS_PUSH_CROSS_HI", "20"))    # ⓐ 시간 무관 발사선
ISS_PUSH_CROSS_FAST = int(os.environ.get("ISS_PUSH_CROSS_FAST", "15"))  # ⓑ 신선 발사선(아래 창과 짝)
ISS_PUSH_FAST_H = float(os.environ.get("ISS_PUSH_FAST_H", "6"))       # ⓑ 그 신선 창(6시간)
ISS_MAX_H = float(os.environ.get("ISS_PUSH_MAX_H", "24"))     # 나이 창 = 배지 소멸선 24h 사본(그 뒤는 배지도 안 붙는다)
ISS_DAY_CAP = int(os.environ.get("ISS_PUSH_DAY_CAP", "40"))   # 하루 상한(폭주 가드 · 260818 실측 = 24h창 사건 단위 근사 41건)
# ⚠️ **이슈도 사건 단위로 묶는다**(운영자 260818 «매체 20 이상이 6시간 이내 쌓이는 이슈가 그렇게나 많어?» =
#    정확한 의심 — 첫 판 실측이 17건이었는데 **실제 사건은 3~4개**였다: 「김민석 당대표」 5건 · 「트럼프 한미훈련
#    축소」 6건 · 「거제 폭우」 3건이 *다른 기사*라 키가 전부 달라 각각 살아남았다). 긴급 축은 이미 AI 사건중복
#    심판(_ai_same_event)을 쓰는데 이슈 루프만 그게 없어서 같은 사건이 매체 수만큼 울렸다 = 같은 병의 형제.
#    ⚠ 이슈는 물량이 많아 콜 상한을 따로 둔다(긴급 예산을 잠식하면 진짜 긴급이 심판 없이 나간다).
ISS_MAX_AI = int(os.environ.get("ISS_PUSH_MAX_AI", "12"))


def iss_push_ok(c, a):
    """이 이슈를 **폰으로 울릴지** — 배지 자격(is_issue)을 이미 통과한 건에만 묻는다. a = 나이(시간)."""
    cr = c.get("cross") or 0
    if cr >= ISS_PUSH_CROSS_HI:
        return True                                        # ⓐ 확실히 큰 건 = 시간 무관
    return cr >= ISS_PUSH_CROSS_FAST and a is not None and a < ISS_PUSH_FAST_H   # ⓑ 붙는 중 = 신선할 때만
# 정형잡음 컷 3종 = build-viewer.mjs BJ_* 바이트 이식(시황 정례·연성 머리표·기업 PR — 매체만 많고 사건이 아닌 것)
_BJ_CRASH = re.compile(r"(폭락|급락|폭등|급등|서킷브레이커|사이드카|붕괴|패닉|쇼크)")
_BJ_MKT = re.compile(r"(증시|코스피|코스닥|환율|유가(?!족)|나스닥|다우|뉴욕증시).{0,20}(출발|개장|마감|장중)")
_BJ_HEAD = re.compile(r"^\[(포토|사진|사설|기고|칼럼|만평|증시|시황|특징주)")
_BJ_PR = re.compile(r"^(?!.*(대통령|방사청|국방부|방산|잠수함|전투기|호위함|군함)).*(수주|공급\s*계약|계약\s*체결|지분.{0,6}(취득|매각|확보|인수)|지분율|자사주|합작사|출자)")


def _badge_junk(t):
    t = t or ""
    return bool((_BJ_MKT.search(t) and not _BJ_CRASH.search(t)) or _BJ_HEAD.search(t) or _BJ_PR.search(t))


def is_issue(c):
    """⚡이슈 = 속보 판정은 아닌데 매체가 몰린 건(화면 이슈 배지와 같은 술어)."""
    if c.get("breaking"):
        return False        # 긴급 축이 먼저 = 같은 사건을 두 번 부르지 않는다
    g = c.get("grade")
    if not (g is None or (g or 0) >= 2):
        return False        # 경중 0·1(잡음·경미) 컷 — 미채점(None)은 배지 정본대로 통과
    cr = c.get("cross") or 0
    if not (cr >= ISS_CROSS_MIN or ((g or 0) >= 3 and cr >= ISS_G3_CROSS)):
        return False
    return not _badge_junk(c.get("title") or "")


KST = dt.timezone(dt.timedelta(hours=9))


def _sent_alive(ts, now_ep):
    # 원장 키 유효 여부(TTL 창 내) — 파싱 실패 = 유효 취급(보수 = 중복 발송 차단 쪽 · 구 포맷 값도 안전)
    try:
        t = dt.datetime.fromisoformat(str(ts))
        if t.tzinfo is None:
            t = t.replace(tzinfo=KST)
        return (now_ep - t.timestamp()) / 3600 < SENT_TTL_H
    except Exception:
        return True

def jload(p, d):
    try: return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception: return d

def is_breaking(c):
    # 푸시용(가역 아님·앱푸시긴급) = grade가 *채점되어* ≥2여야 함(운영자 260818 하향 — 🚨배지·자동픽과 같은 문턱 · 헤더 주석에 하향 근거 실측 · None=미채점은 여전히 푸시 보류[비가역 보수 철학 불변] · 오발 가드 cross≥PUSH_MIN_CROSS·4h/8h 창도 불변).
    g = c.get("grade")
    return bool(c.get("breaking")) and g is not None and (g or 0) >= 2

def brk_url(c):
    # 긴급 알림 탭 → 루트가 아니라 *해당 건*으로 딥링크(/?brk=키&bl=메이저링크). 뷰어가 탭 *시점*에 '요약 완료?'를
    # 보고 분기: 완료=요약창 / 미완료=스크랩 기사 중 가장 메이저(breaking_pick)로 이동(웹앱 경유). 운영자 260622.
    #  · key = event_key 우선(별칭 점프에도 안정)·url 폴백 → 뷰어가 candidates 에서 해당 후보를 찾는 매칭키.
    #  · bl  = 대표 매체 픽 url(없으면 최초보도) → 후보 조회 실패(랙·만료) 시에도 메이저 원문 보장(client scLinkUrl 의 서버판).
    key = (c.get("event_key") or c.get("url") or "").strip()
    if not key:
        return "/"
    bp = c.get("breaking_pick") or {}
    bl = (bp.get("url") or c.get("url") or "").strip()
    u = "/?brk=" + quote(key, safe="")
    if bl:
        u += "&bl=" + quote(bl, safe="")
    return u

def disp_title(c):
    # 외신 = 한국어 번역 제목 우선(gate_judge 편승 title_ko · 원문 일치 도장만 유효 — 뷰어 scKoTitle 과 동일 술어 · 260703)
    ko = c.get("title_ko")
    return ko if (ko and c.get("title_ko_of") == c.get("title")) else (c.get("title") or "")

def dedup_keys(c):
    # 같은 사건 중복 발송 차단 — event_key(별칭 점프에도 안정) + 제목해시(event_key=url 디폴트라 url 점프 시
    # 갈리는 구멍 보완: 같은 헤드라인이면 url 달라도 같은 키) + group_id(사건 묶기 도장 — 같은 사건의 *다른
    # 후속 기사*도 같은 키 = 사건 단위 dedup 결정층 · Q437 · 단 대형 사건은 group_judge MAX_SIZE=8 초과로
    # 미도장이 구조적이라[쿠팡 27건 실측] 아래 AI 사건중복이 주력, 이 키는 보조). 하나라도 sent에 있으면 스킵.
    ks = []
    ek = c.get("event_key") or c.get("id") or c.get("url")
    if ek: ks.append(str(ek))
    t = re.sub(r"\s+", "", c.get("title") or "")
    if t: ks.append("t:" + hashlib.md5(t.encode("utf-8")).hexdigest()[:16])
    g = c.get("group_id")
    if g and str(g) not in ks: ks.append(str(g))
    return ks


def _ai_same_event(title, recent_titles):
    """발송 직전 AI 사건중복 단독 심판 — title이 recent_titles(최근 발송 사건) 중 *같은 실제 사건*이면 그 index,
    아니면 None. 프롬프트·엄격 파싱 = auto_pick_breaking._ai_same 정본 그대로(카드 평의회 260625 검증 판정유형 —
    렉시컬 임계는 템플릿형 다른사건 false-merge 선례로 금지). AI 실패·토큰없음·산문 = None(=다른 사건=발송 진행:
    진짜 별개 긴급 누락[false-merge]보다 중복 1발이 안전 — autopick과 동일 방향)."""
    if not recent_titles:
        return None
    try:
        sys.path.insert(0, str(ROOT / "shared"))
        from claude_py import run_claude
    except Exception:
        return None
    listing = "\n".join(f"{i}\t{str(t or '').replace(chr(9), ' ').replace(chr(10), ' ')}" for i, t in enumerate(recent_titles))
    prompt = (
        "너는 한국 뉴스 속보 중복 판정자다. '대상 사건'이 아래 '이미 다룬 사건들' 중 하나와 "
        "**동일한 실제 사건**(같은 사고·재난·사건의 다른 기사/후속/속보·대응 발표)인지 판정하라.\n"
        "- 같은 실제 사건 = 그 번호 (예: 같은 지진의 다른 기사, 같은 충돌사고 속보+대통령 대응)\n"
        "- **장소·주체·일시가 다르면 유형(화재·지진·폭발·추돌)이 같아도 다른 사건 = NONE** "
        "(안산 공장폭발 ≠ 청주 공장폭발 · 일본 지진 ≠ 베네수엘라 지진 · 코스피 ≠ 코스닥).\n"
        "- 조금이라도 애매하면 NONE(중복 아님으로 = 진짜 별개 긴급 누락 방지).\n"
        f"대상: {str(title or '').replace(chr(10), ' ')}\n이미 다룬 사건들:\n{listing}\n\n"
        "출력은 정확히 토큰 하나 — 동일하면 그 번호(예: 2), 없으면 NONE. 다른 글자·설명·기호 금지."
    )
    # --safe-mode(평의회 260812 권고2) — autopick과 동축: 자기완결 프롬프트·출력 1토큰 판정이 CLAUDE.md를 콜마다
    #   재적재(콜당 캐시쓰기 ~5만tok = 비용의 99%)하던 축 절단. judge 3종 260701 카나리아(−97.2%) 문법 이식 ·
    #   --bare 아님 · 롤백 = env PUSH_DEDUP_SAFE=0 1줄.
    _safe = [] if os.environ.get("PUSH_DEDUP_SAFE", "1").strip() == "0" else ["--safe-mode"]
    p, rc, err = run_claude(
        ["claude", "-p", "--model", os.environ.get("PUSH_DEDUP_MODEL", "claude-opus-5"), "--effort", "high"] + _safe +
        ["--disallowedTools", "Write,Edit,NotebookEdit,Bash,Task,WebFetch,WebSearch,Read,Glob,Grep",
         "--max-turns", "1"],
        prompt, timeout=120, source="pushdedup")
    if p is None or rc != 0:
        print(f"  ⚠ 푸시 사건중복 AI 실패(rc={rc}) — 다른 사건 간주(발송 진행·false-merge 회피)", file=sys.stderr)
        return None
    out = (p.stdout or "").strip()
    if not re.fullmatch(r"#?\s*\d+", out):   # '번호 단독'만 인정(산문 속 임의 숫자 오인 차단 · autopick 검증 평의회 5·10)
        return None
    idx = int(re.search(r"\d+", out).group())
    return idx if 0 <= idx < len(recent_titles) else None

def age_h(c):
    # 나이 = first_seen(갓 감지) 우선·published 폴백 — published 우선(구)은 syndication 지연·스탬프 오류로
    # breaking 후보 43%가 도착 시점 이미 4h+ = 푸시 영구 누락(자동픽 age_h와 동일 축 · §7 260619 보류 →
    # 운영자 260710 '푸시 누락 고치기' 승인으로 전환). 진짜 뒷북 = breaking_judge('방금 터진'만 YES) 의미 게이트
    # + grade≥3 + 아래 발행 상한(PUSH_PUB_MAX_H)이 거름.
    s = c.get("first_seen") or c.get("published") or ""
    for f in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            t = dt.datetime.strptime(s.replace("Z", "+0000")[:25 if "+" in s else 19], f)
            if t.tzinfo is None: t = t.replace(tzinfo=dt.timezone.utc)
            return (time.time() - t.timestamp()) / 3600
        except Exception: pass
    return None

def pub_age_h(c):
    # 발행 나이(published 단독·없으면 None) — 극단 뒷북 상한 가드 전용(발행 24h+ = 배지도 없는 묵은 건 = 푸시 불가).
    s = c.get("published") or ""
    for f in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            t = dt.datetime.strptime(s.replace("Z", "+0000")[:25 if "+" in s else 19], f)
            if t.tzinfo is None: t = t.replace(tzinfo=dt.timezone.utc)
            return (time.time() - t.timestamp()) / 3600
        except Exception: pass
    return None

def _flush_ledgers(sent_keys, suppressed_keys, sent_evs, prior_events):
    """발송 원장(sent.json = 키 dedup) + 사건 시그니처(sent_events.json = AI 사건중복 비교대상) 일괄 갱신.
    suppressed_keys(AI '같은 사건' 억제 키)도 원장 도장 = 다음 런 AI 0콜 키-스킵. 전부 48h TTL 정리."""
    if not (sent_keys or suppressed_keys or sent_evs):
        return
    now_iso = dt.datetime.now(KST).isoformat(timespec="seconds")
    raw = jload(SENT, {})
    if isinstance(raw, list):
        raw = {k: now_iso for k in raw}   # 구 포맷 마이그레이션 — 기존 키 = 지금 도장(48h 뒤 자연 만료)
    for k in list(sent_keys) + list(suppressed_keys):
        raw[k] = now_iso
    _now_ep = time.time()
    raw = {k: v for k, v in raw.items() if _sent_alive(v, _now_ep)}
    SENT.parent.mkdir(parents=True, exist_ok=True)
    SENT.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    if sent_evs:
        evs = [e for e in prior_events if _sent_alive((e or {}).get("ts"), _now_ep)] + list(sent_evs)
        SENT_EV.write_text(json.dumps(evs, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")


def vapid_pem(raw_b64url):
    # raw 32바이트 스칼라(web-push 표준) → PKCS8 PEM(파일). pywebpush 버전 무관 안전 입력.
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    raw = base64.urlsafe_b64decode(raw_b64url + "=" * (-len(raw_b64url) % 4))
    key = ec.derive_private_key(int.from_bytes(raw, "big"), ec.SECP256R1())
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.NoEncryption()).decode()
    tf = tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False)
    tf.write(pem); tf.close()
    return tf.name

LIVE_BASE = (os.environ.get("LIVE_BASE") or "https://edit.nomute.kr").rstrip("/")   # 알림 딥링크의 절대 기준 = 정본 화면(도메인 교체 시 레버 1개 · live_smoke --base 관용구 계승)


def abs_url(u):
    """알림 딥링크를 **절대 주소로** 굳힌다(260816 실사고 봉합 · CONTRACT: check_push_abs_url).

    ⚠ 진범 = 상대경로 + 폰 SW의 origin. `sw.js notificationclick`이 `new URL(raw, self.location.origin)`으로
    주소를 만드는데, 그 origin은 **그 구독이 등록된 화면**이다. 계정 이관(260816) 전에 등록된 구독은 전부
    옛 화면 것이라(실측 = 5대 전건 26-06-19~26-07-21 등록 = 이관 26일 전), `/?a=…`·`/thumb.html?done=…`
    같은 상대경로가 **옛 화면 주소에 붙어** 알림을 눌러도 옛 화면으로 갔다(운영자 260816 「알림이 다 구 주소로
    가는거 같은데」 = 정확한 관측).
    ⚠ **옛 화면 SW는 고칠 수 없다** — 그 화면은 새 저장소 커밋을 배포받지 않으므로 뷰어·SW를 아무리 고쳐도
    이미 폰에 깔린 그 SW가 그대로 산다. 따라서 **서버가 절대 주소를 실어 보내는 것**만이 유효한 수단이다
    (절대 주소면 `new URL(raw, origin)`에서 base가 무시된다 = 어느 화면 SW가 받아도 정본 화면으로 간다).
    ⚠ 짝 = 구독 재등록(운영자가 새 화면에서 알림 껐다 켜기)은 근본책이지만 사람 손이고, 그전에도 알림이
    제 화면으로 가야 한다 = 이 함수가 그 사이를 메운다(재등록 후에도 무해 = 같은 주소).
    이미 절대 주소면 그대로 둔다(스킴 보유 판정 = 미래에 절대 주소로 쏘는 호출부와 충돌 0)."""
    u = str(u or "/")
    if u.startswith("http://") or u.startswith("https://"):
        return u
    return LIVE_BASE + (u if u.startswith("/") else "/" + u)


def notif_icon(kind, theme):
    """종류 → 알림 아이콘 **data URL**. URL 대신 이미지를 통째로 실어보내는 이유(실측 260727):
    payload에 아이콘 *주소*를 주면 폰이 그 이미지를 받아오지 못해(Access 벽/미배포 404) 안드로이드가
    사이트 첫 글자 'A' 폴백을 그린다. data URL = 네트워크 요청 0 = 그 벽과 무관하게 항상 그려진다.
    ⚠ 서버는 폰의 라이트/다크 테마를 모른다 → 기본은 다크판(sig · 앱 자체가 다크 UI). 미지 종류 = None(=SW 기본판)."""
    if not kind:
        return None
    try:
        b = json.loads(NOTIF_ICONS.read_text(encoding="utf-8"))
    except Exception:
        return None
    return (b.get(kind) or {}).get(theme or "sig")


def main():
    test = "--test" in sys.argv
    suppressed_keys, sent_events = [], []   # 사건 dedup 상태 — 테스트·--notify 경로에서도 참조되므로 선초기화
    notify = None
    notify_url = "/"
    notify_tag = "nomute-make"
    notify_kind = ""   # 알림 종류(운영자 260727 "알림 종류별로 카테고라이징해서 로고를 다르게") — SW가 kind→아이콘 매핑. 정본 종류 = viewer/sw.js NOTIF_ICON
    notify_icon = ""   # 아이콘 URL 직접 지정(최우선) — **구 SW 호환 검증용**. 정식 발송 경로는 비우고 kind만 보낸다(비워야 SW가 라이트/다크 테마짝을 스스로 고른다).
    if "--kind" in sys.argv:
        m = sys.argv.index("--kind")
        if len(sys.argv) > m + 1 and sys.argv[m + 1]:
            notify_kind = sys.argv[m + 1]
    notify_theme = "sig"
    if "--icon-theme" in sys.argv:   # sig = 다크 알림판(기본) / blue = 라이트 알림판
        m = sys.argv.index("--icon-theme")
        if len(sys.argv) > m + 1 and sys.argv[m + 1]:
            notify_theme = "blue" if sys.argv[m + 1].lower() in ("blue", "light") else "sig"
    if "--icon" in sys.argv:
        m = sys.argv.index("--icon")
        if len(sys.argv) > m + 1 and sys.argv[m + 1]:
            notify_icon = sys.argv[m + 1]
    if not notify_icon and notify_kind:            # 명시 지정이 없으면 종류별 data URL 자동 적재
        notify_icon = notif_icon(notify_kind, notify_theme) or ""
    if "--url" in sys.argv:                           # 알림 탭 시 이동할 경로(제작완료=제작 화면으로) · 미지정이면 "/"
        j = sys.argv.index("--url")
        if len(sys.argv) > j + 1:
            notify_url = sys.argv[j + 1] or "/"
    if "--tag" in sys.argv:                            # 알림 tag — 같은 tag=교체. 건별 고유 tag면 여러 알림 쌓임(요약완료=건별 누적)
        k = sys.argv.index("--tag")
        if len(sys.argv) > k + 1 and sys.argv[k + 1]:
            notify_tag = sys.argv[k + 1]
    if "--notify" in sys.argv:                       # 임의 알림(제작완료 등) — 구독자 전원(=프로필 ON) · dedup 미기록
        i = sys.argv.index("--notify")
        notify = (sys.argv[i + 1] if len(sys.argv) > i + 1 else "🖼 News",
                  sys.argv[i + 2] if len(sys.argv) > i + 2 else "")
    subs = jload(SUBS, [])
    if not isinstance(subs, list) or not subs:
        print("구독자 없음 — 발송 생략"); return
    priv = os.environ.get("VAPID_PRIVATE_KEY", "").strip()
    subj = os.environ.get("VAPID_SUBJECT", "mailto:muteno@pm.me").strip()
    if not priv:
        print("VAPID_PRIVATE_KEY 없음 — 생략"); return
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        print("pywebpush 미설치 — 생략"); return

    if test:
        msgs = [{"keys": [f"test-{int(time.time())}"], "title": "🔔 노뮤트 테스트",
                 "body": "웹푸시 연결 정상! 긴급 속보가 이렇게 와.", "url": "/", "tag": "nomute-breaking",
                 "kind": notify_kind or "test", "icon": notify_icon}]
    elif notify:
        # 제작완료/요약완료 등 = 전용 tag(긴급 속보와 안 덮어씀) · url=대상 화면(notify_url) · tag=notify_tag(건별 고유면 누적)
        msgs = [{"keys": [f"notify-{int(time.time())}"], "title": notify[0], "body": notify[1], "url": notify_url, "tag": notify_tag,
                 "kind": notify_kind, "icon": notify_icon}]
    else:
        cands = jload(CAND, [])
        _raw = jload(SENT, {})
        if isinstance(_raw, list):
            sent = set(_raw)   # 구 포맷(list·TTL 없음) = 전부 유효 취급(발송 시 dict로 마이그레이션)
        else:
            _now_ep = time.time()
            sent = {k for k, v in _raw.items() if _sent_alive(v, _now_ep)}   # TTL 만료 키 = 억제 해제(반복 헤드라인 새 사건 재푸시 가능)
        # 사건 단위 dedup 준비 — 최근 발송 사건 시그니처(48h 창 · autopick_events 쌍둥이)
        _now_ep2 = time.time()
        _ev_raw = jload(SENT_EV, [])
        sent_events = [e for e in _ev_raw if isinstance(e, dict) and _sent_alive((e or {}).get("ts"), _now_ep2)] if isinstance(_ev_raw, list) else []
        ai_calls = 0
        msgs = []
        for c in cands:
            if not is_breaking(c):
                continue
            if (c.get("cross") or 0) < PUSH_MIN_CROSS:   # 다매체 검증 미달 = 오발송 가드(푸시는 회수 불가)
                continue
            a = age_h(c)
            if a is None or a < 0 or a >= FAST_MAX_H:   # a<0 = 미래스탬프(소스 TZ 오기록) → 음수나이가 4h창 통과해 비가역 오발송하던 구멍 차단(뷰어 scTs 미래가드와 짝)
                continue
            pa = pub_age_h(c)
            if pa is None or pa < 0 or pa >= PUSH_PUB_MAX_H:   # 발행 8h+ = 뒷북 차단 · pa<0 = 미래 published(소스 TZ 오기록) = 신뢰 불가 → 보류(평의회1 260722 — age_h 음수가드와 대칭·비가역 오발 차단) · published 없음/파싱실패 = 보류(grade None 보류와 동일 보수 철학 — None 관대면 캡이 통째 꺼짐 · 검4-3 260710). ⚠️ 한계 정직: 이 캡의 입력 = *현재 rep 기사* 발행 나이(rep 점프 시 최신 후속 기사 기준)지 사건 최초 발행 나이가 아님 — 사건나이 프록시·승계 실패 first_seen 리셋 보완은 §7 후속 큐.
                continue
            ks = dedup_keys(c)
            if not ks or any(k in sent for k in ks):     # event_key·제목해시·group_id 중 하나라도 보냄 = 스킵(중복 차단)
                continue
            # 사건 단위 dedup(Q437 · 운영자 260722 "같은 사건이면 한 번만") — 키가 다 달라도(다른 후속 기사)
            # 최근 발송 사건과 *같은 실제 사건*이면 억제. AI 단독 심판(fail-open=발송 · 콜 상한) — 쿠팡 화재
            # 3연발(기사키 상이·group_id 미도장) 클래스가 표적. 억제 키는 원장 도장 = 이후 런 AI 0콜 스킵.
            if sent_events and ai_calls < MAX_AI_DEDUP:
                ai_calls += 1
                # ⚠ 비교 대상은 **긴급 발송분만**(k != "iss") — 이슈 발송분까지 넣으면 이슈로 먼저 알린 사건이
                #   나중에 속보로 승격됐을 때 "이미 다룬 사건"으로 억제돼 **진짜 긴급을 놓친다**(비싼 방향의 오류).
                dup = _ai_same_event(c.get("title") or "", [e.get("title", "") for e in sent_events if e.get("k") != "iss"])
                if dup is not None:
                    print(f"  ⊘ 사건중복 억제(AI): {(c.get('title') or '')[:34]} ≈ {str(sent_events[dup].get('title', ''))[:28]}", file=sys.stderr)
                    suppressed_keys.extend(ks)
                    continue
            msgs.append({"keys": ks, "ev_title": c.get("title") or "", "title": "News", "body": ("(긴급) " + disp_title(c))[:120], "url": brk_url(c), "tag": "nomute-breaking", "kind": "brk", "icon": notif_icon("brk", "sig") or ""})   # 제목="News"(고정·OS 볼드) · 본문="(긴급) 헤드라인"(외신=번역 제목) · url=해당 건 딥링크(요약완료=요약창/미완료=메이저링크 · 운영자 260622)
        # ── ⚡이슈 발송(긴급 루프 뒤 = 긴급이 우선) ────────────────────────────────────────
        # ⚠️ 원장 키에 "iss:" 접두를 붙여 긴급 키와 **분리**한다 — 접두가 없으면 이슈로 먼저 나간 사건이
        #    나중에 속보로 승격돼도 "이미 보냄"에 막혀 진짜 긴급을 놓친다(반대 방향은 아래 원본 키 검사가 막는다).
        if ISS_PUSH:
            iss_n, iss_ai = 0, 0
            # ⚠️ **첫 회차 소급 차단** — 원장에 이슈 키가 하나도 없으면(= 이 기능이 방금 켜졌다) 지금 자격을 가진
            #    과거분이 통째로 발사된다(260818 실측 = 24h창 50건 = 폰에 40통이 한 번에). 운영자 «다 받아봄»은
            #    「앞으로 안 놓치겠다」는 뜻이지 「어제 것을 소급으로 받겠다」가 아니다 → 첫 회차는 **발송 0 · 도장만**
            #    찍고, 다음 회차부터 새로 자격을 얻은 건만 쏜다(자동픽 일캡·kw 첫발견 관례와 같은 방향).
            iss_seeded = any(str(k).startswith("iss:") for k in sent)
            for c in cands:
                if iss_seeded and iss_n >= ISS_DAY_CAP:   # 상한은 **발송분에만** — 첫 회차 도장은 전건 찍어야 다음 회차가 조용하다
                    print(f"이슈 하루 상한 {ISS_DAY_CAP} 도달 — 나머지 생략", file=sys.stderr)
                    break
                if not is_issue(c):
                    continue
                a = age_h(c)
                if a is None or a < 0 or a >= ISS_MAX_H:   # 미래스탬프·배지 소멸선 밖 = 제외(긴급 축과 같은 가드)
                    continue
                if not iss_push_ok(c, a):                  # 배지는 붙어도 폰까지 울릴 급인지는 별도 문턱(운영자 260818)
                    continue
                base = dedup_keys(c)
                if not base:
                    continue
                if any(k in sent for k in base):   # 이 사건이 **긴급으로 이미 나갔다** = 이슈로 또 부르지 않는다
                    continue
                ks = ["iss:" + k for k in base]
                if any(k in sent for k in ks):
                    continue
                if not iss_seeded:                 # 첫 회차 = 조용히 원장에만 도장(발송 0)
                    suppressed_keys.extend(ks)
                    iss_n += 1
                    continue
                # 사건 단위 묶기 — 이미 이번 런에서 보낸 이슈·긴급과 **같은 실제 사건**이면 억제(운영자 260818).
                #   비교 대상 = 최근 발송 사건 시그니처(48h) + 이번 런에서 방금 담은 이슈 제목.
                #   실패·토큰 없음 = 발송 진행(false-merge 회피 = 긴급 축과 같은 방향).
                _cand_t = c.get("title") or ""
                _pool = [e.get("title", "") for e in sent_events] + [m.get("ev_title") or m["body"] for m in msgs if m.get("kind") == "iss"]   # 이쪽은 전 축 비교 = 긴급으로 이미 알린 사건이면 이슈로 안 부른다
                if _pool and iss_ai < ISS_MAX_AI:
                    iss_ai += 1
                    _d = _ai_same_event(_cand_t, _pool)
                    if _d is not None:
                        print(f"  ⊘ 이슈 사건중복 억제(AI): {_cand_t[:34]} ≈ {str(_pool[_d])[:28]}", file=sys.stderr)
                        suppressed_keys.extend(ks)
                        continue
                msgs.append({"keys": ks, "ev_title": _cand_t, "title": "News", "body": ("(이슈) " + disp_title(c))[:120],
                             "url": brk_url(c), "tag": "nomute-issue", "kind": "iss",
                             "icon": notif_icon("iss", "sig") or ""})   # 노랑 지구본 = 화면 ⚡이슈 배지와 같은 색(운영자 260818)
                iss_n += 1

        if not msgs:
            if suppressed_keys:   # 발송 0건이어도 억제 도장은 기록(다음 런 AI 재호출 0 — 조용한 반복 콜 차단)
                _flush_ledgers([], suppressed_keys, [], sent_events)
                print(f"사건중복 억제 {len(suppressed_keys)}키 도장 — 발송 0")
            print("새 긴급 없음 — 발송 생략"); return

    pem_path = vapid_pem(priv)
    dead, sent_keys, sent_evs = set(), [], []
    for m in msgs:
        pl = {"title": m["title"], "body": m["body"], "url": abs_url(m["url"]), "tag": m.get("tag", "nomute-breaking")}
        if m.get("kind"): pl["kind"] = m["kind"]     # SW가 종류→아이콘 매핑(신 SW) · 미지정 = 브랜드 기본
        if (m.get("kind") or "brk") in ALERT_KINDS:  # 전 종류 소리·진동(위 계약) — 구 SW는 모르는 키를 무시하므로 회귀 0 · 종류 미지정(구 발송 경로)도 포함
            pl["vibrate"] = VIBRATE
            pl["renotify"] = True                    # 같은 묶음표로 교체돼도 다시 울린다(뒤 긴급을 조용히 덮는 것 차단)
        if m.get("icon"): pl["icon"] = m["icon"]     # 직접 지정 = 최우선(구 SW 호환 검증 경로 · 정식 발송은 비움 = 테마짝 유지)
        payload = json.dumps(pl, ensure_ascii=False)
        if len(payload.encode("utf-8")) > PAYLOAD_MAX and pl.pop("icon", None):   # 한도 초과 = 아이콘만 포기(알림은 반드시 뜬다)
            payload = json.dumps(pl, ensure_ascii=False)
            print(f"  ⚠ 페이로드 한도 초과 — 아이콘 생략하고 발송({m.get('kind') or '기본'})", file=sys.stderr)
        ok_any = False
        for s in subs:
            ep = (s or {}).get("endpoint")
            if not ep:
                continue
            if (s or {}).get("off"):   # 화면에서 끈 기기 = 발송 제외(운영자 260819 «비활성화 시키면 그쪽에는 푸시를 안하는거로») · 구독은 목록에 남는다(다시 켜면 그대로 복귀)
                continue
            try:
                webpush(subscription_info=s, data=payload, vapid_private_key=pem_path, vapid_claims={"sub": subj})
                ok_any = True
            except WebPushException as e:
                code = getattr(getattr(e, "response", None), "status_code", None)
                if code in (404, 410):
                    dead.add(ep)
                print(f"push 실패({code}): {ep[:60]}", file=sys.stderr)
            except Exception as e:
                print(f"push 오류: {e}", file=sys.stderr)
        if ok_any:
            sent_keys.extend(m["keys"])   # event_key+제목해시(+group_id) 다 기록 = 다음 런에 어느 쪽으로 와도 dedup
            if m.get("ev_title") is not None:   # 긴급 발송만 사건 시그니처 기록(테스트·--notify 는 ev_title 없음)
                sent_evs.append({"ts": dt.datetime.now(KST).isoformat(timespec="seconds"), "title": m["ev_title"],
                                 "key": (m["keys"] or [""])[0], "k": m.get("kind") or "brk"})   # k = 축 표시(brk·iss) — 위 긴급 심판이 이슈분을 걸러내는 근거

    if dead:   # 죽은 구독 정리
        subs2 = [s for s in subs if (s or {}).get("endpoint") not in dead]
        SUBS.write_text(json.dumps(subs2, ensure_ascii=False), encoding="utf-8")
        print(f"죽은 구독 {len(dead)} 정리")
    if not test and not notify:   # 발송·억제 원장 갱신(테스트·임의알림은 미기록) — dict{키: 발송시각 KST} + 사건 시그니처 + 48h TTL 정리
        _flush_ledgers(sent_keys, suppressed_keys, sent_evs, sent_events)
    print(f"발송: {len(sent_keys)}/{len(msgs)} 사건{f' · 사건중복 억제 {len(suppressed_keys)}키' if suppressed_keys else ''} · 구독 {len(subs)}{' [TEST]' if test else ''}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"push_send 경고(무시·비치명): {e}", file=sys.stderr)
