#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 확산 신호(lv) → 수집함 반영 — to_candidates 직후 한 스텝(scrape.yml · scripts/phone_scrape.sh · scripts/pc_lane.sh 형제 전건).
#   사용: python3 scraper/live_seed.py [articles.json경로]
#
# 하는 일(정본 신호 = scraper/live_signal.py):
#  ① 입장 — t2↑ 이름에 맞는 실후보가 없는데 이번 회차 묶음 중 한 매체뿐(cross 1 · 태그 없음)이라 못 들어온 대표가 있으면
#     단독 1보와 같은 규칙(solo 표식 · 발행 6h 정리 · 긴급 확정분 보존)으로 들인다.
#  ② 이관 — 씨앗과 같은 이름의 실후보가 우리 피드에 들어오면 씨앗을 지우고 상태를 넘긴다(event_key = 푸시 원장 첫 키 승계로
#     씨앗 때 나간 긴급이 다시 안 나간다 · breaking·도장·경중·first_seen(이른 쪽)·lv 이관).
#  ③ 첨부 — 이름(토큰)마다 가장 잘 맞는 후보 **하나**에 lv = {k,t,f,c,x,g,n,gn,a} 를 싣는다(제목·메이저 픽·lb·이번 회차 묶음 멤버 제목 대조
#     = 대표 제목이 「유명 유튜버」처럼 익명이어도 멤버 제목의 실명으로 잡힌다 · A7). 판정기는 이 값으로 〔확산 강|중|약〕 꼬리표를 붙인다.
#     ⚠ 첨부 = t2↑ 전부 + t1 중 트렌드 갈래(X·G·N)가 있는 것만(커뮤니티 한 갈래만 = 잡음 90%↑ · 붙이지 않는다).
#     ⚠ [강](t3)은 한 번 붙으면 엔트리에서 **내리지 않는다**(동결) — 내리면 도장이 바뀌어 [강] 없이 재판정 → 이미 나간 긴급이 뒤집힌다.
#  ④ 씨앗(seed:"gn") — t3 가 구글 뉴스로 확인됐는데 우리 피드에 그 이름 기사가 아직 없으면 구글 뉴스의 가장 이른 기사로 후보를 만든다
#     (제목 = 그 이름이 들어간 가장 이른 헤드라인 · 매체 = 그 매체 · url = 원문 해제 성공 시 원문, 실패 시 구글 뉴스 링크).
# 바이트 예산 = to_candidates.MAX_BYTES(초과분 = 꼬리부터 · lv·씨앗 엔트리는 보호) · lv 는 있는 엔트리에만(키 자체 없음 = 예산).
# 실패 = 경고만(수집을 못 깬다 · 워크플로가 `|| echo` 로 감싼다) · 롤백 = env LIVE_SIGNAL=0(이 스텝 전체 무동작).
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_signal as L   # noqa: E402
import to_candidates as T   # noqa: E402  입장 엔트리 모양·카테고리·단독 규칙 값의 정본(사본 0)

ROOT = Path(__file__).resolve().parent.parent
CAND = ROOT / "viewer" / "candidates.json"
EVENTS = ROOT / "scraper" / "obs" / "events.jsonl"   # 사건 첫 등장 원장(snapshot.py · 14일) = 수집함에서 잘려 나간 옛 보도의 기억
LV_MATCH_H = 12        # 첨부 대상 = 발행(없으면 수집) 12h 안 후보(묵은 기사에 꼬리표 금지 · ⏱ 12h 게이트와 같은 선)
TRENDS = set("XGN")


def _age_h(c, now):
    for k in ("published", "first_seen"):
        t = L._ts(c.get(k))
        if t:
            return (now - t) / 3600
    return None


def _fresh(c, now, h=LV_MATCH_H):
    a = _age_h(c, now)
    return a is not None and -10 <= a < h


def load_events(now, path=EVENTS, back_h=L.NOVEL_BACK_H + L.STRONG_KEEP_H):   # 무장 24h 전까지 = 확인(무장 6h 안)·씨앗([강] 24h 안) 어느 시점에도 창 전체
    """novel 판정용 최근 사건 = [{first_seen, title}] — 수집함(상한 800·바이트 예산)은 하루 전 보도를 이미 잘라냈을 수 있어
    「묵은 사건의 재점화」를 새 사건으로 오인한다(리플레이 실측 = 「승리」 CCTV 보도가 잘려 나간 뒤 스포츠 「승리」로 재무장).
    원장이 없거나 깨진 줄 = 건너뜀(fail-soft)."""
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                t = L._ts(r.get("f"))
                if t and now - back_h * 3600 <= t <= now and r.get("t"):
                    out.append({"first_seen": r["f"], "title": r["t"]})
    except OSError:
        pass
    return out


def texts(c, mt):
    """대조 제목 = (자기 제목들, 이번 회차 묶음 멤버 제목들)."""
    lb = c.get("lb") if isinstance(c.get("lb"), dict) else {}
    own = [c.get("title"), (c.get("breaking_pick") or {}).get("title"), lb.get("t"), c.get("title_ko")]
    mem = [mt[u] for u in (c.get("cluster_members") or []) if u in mt]
    return [x for x in own if x], mem


class Matcher:
    """후보 제목 전처리 캐시(엔트리당 1회) — 이름 수 × 후보 수 대조를 가볍게. level = 2 자기 제목 · 1 멤버 제목만(익명 대표) · 0 없음."""

    def __init__(self, mt):
        self.mt, self.memo = mt, {}

    def level(self, key, c):
        p = self.memo.get(id(c))
        if p is None:
            own, mem = texts(c, self.mt)
            p = self.memo[id(c)] = ([L.prep(t) for t in own], [L.prep(t) for t in mem], c)   # c 를 쥐어 id 재사용 차단
        k = L.norm_key(key)
        if any(L.hitp(k, x) for x in p[0]):
            return 2
        if any(L.hitp(k, x) for x in p[1]):
            return 1
        return 0


def level(key, c, mt):
    """2 = 자기 제목에 이름 · 1 = 멤버 제목에만(익명 대표) · 0 = 없음(단건 호출용 · 반복 대조는 Matcher)."""
    return Matcher(mt).level(key, c)


def supersede(seed, real):
    """씨앗 → 실후보 상태 이관(제자리 수정). 반환 = real."""
    ek, own = real.get("event_key"), real.get("url")
    if not ek or ek == own or (seed.get("breaking") and not real.get("breaking")):
        real["event_key"] = seed.get("event_key") or seed.get("url")   # 푸시 원장 첫 키(push_send.dedup_keys) = 씨앗 때 나간 긴급의 재발송 차단
    #   ⚠ 이미 다른 씨앗 키를 승계한 실후보는 덮지 않는다(긴급으로 나간 씨앗 키가 우선) — 두 씨앗이 한 실후보로 이관될 때
    #     나중 씨앗(NO) 키가 먼저 나간 씨앗 키를 지워 재판정 YES 에 2발이 나가던 구멍(평의회3 260929 재현)
    if seed.get("breaking") and not real.get("breaking"):
        real["breaking"] = True
        if seed.get("breaking_rubric"):
            real["breaking_rubric"] = seed["breaking_rubric"]    # 제목 지문이 달라 판정기가 실제목으로 1회 재판정(도장 = 규칙+제목)
    sg, rg = seed.get("grade"), real.get("grade")
    if sg is not None and rg is None:
        real["grade"] = sg                                      # 이름이 박힌 씨앗 제목의 채점(표시 공백 방지) — 도장(grade_rubric)은 안 옮긴다 =
        #   gate_judge 가 실후보 제목으로 1회 재채점(이름만 같은 다른 소식에 경중 3이 굳던 것 · 평의회260929-2 #5)
    elif sg is not None and rg is not None and sg > rg:
        real["grade"] = sg
    ts, tr = L._ts(seed.get("first_seen")), L._ts(real.get("first_seen"))
    if ts and (not tr or ts < tr):
        real["first_seen"] = seed["first_seen"]                 # 사건을 처음 본 시각 = 더 이른 쪽(푸시 4h 창·재판정 창 기준)
    if L.lv_tier(seed) > L.lv_tier(real):
        real["lv"] = seed["lv"]
    return real


def _related(k, ep, k2, ep2):
    """두 이름이 포함 관계인가 = 짧은 쪽(3자↑ 이름꼴)이 긴 쪽 정규화형 안에 그대로 있음(「사회인」⊂「사회인야구」).
    ⚠ live_signal.hit 의 조사 꼬리 규칙은 「야구」를 조사로 안 봐서 못 잡는다 — 씨앗 억제 전용(보수 = 씨앗을 덜 만든다)이라 단순 포함으로 판정."""
    a, b = (k, k2) if len(k) <= len(k2) else (k2, k)
    return a != b and L._contains_ok(a) and a in b


def _pick(ms, ep):
    """이름 하나에 맞는 후보들 중 첨부 대상 = (자기 제목 적중, 본류(cross≥3), 지난번 첨부 유지, 실후보 우선, cross, 최신 발행).
    ⚠ 본류가 유지 가점보다 앞 — 한 매체 단독(웹드라마 기사 등)이 [강]을 계속 쥐고 다매체 본류가 못 받던 것(평의회260929-2 #7 재현 = 11:31)."""
    u0 = (ep or {}).get("u")
    return max(ms, key=lambda lc: (lc[0], (lc[1].get("cross") or 0) >= 3, lc[1].get("url") == u0, not lc[1].get("seed"),
                                   lc[1].get("cross") or 0, str(lc[1].get("published") or "")))[1]


_SEED_KEEP = ("breaking", "breaking_rubric", "grade", "grade_rubric")   # 씨앗 장부(st["sd"])에 적어 두는 판정·채점 결과


def _keep_strong(old, lv):
    """동결된 [강] 증거 + 이번 회차 증거 = 항목별 더 센 쪽(곳수·검색량·언론 = 큰 값 · 순위 = 작은 값 · 갈래 = 합집합) · 단계 = [강] · 무장 시각 = 처음 것."""
    d = dict(lv, t=L.TIER_STRONG, a=old.get("a") or lv.get("a"))
    for f in ("c", "g", "gn"):
        v = max(old.get(f) or 0, lv.get(f) or 0)
        if v:
            d[f] = v
    for f in ("x", "n"):
        v = [x for x in (old.get(f), lv.get(f)) if x]
        if v:
            d[f] = min(v)
    fam = set(old.get("f") or "") | set(lv.get("f") or "")
    if fam:
        d["f"] = "".join(x for x in L.FAM if x in fam)
    return d


def _seed_entry(key, ep, g, now):
    e = g.get("e") or {}
    url = g.get("ru") or e.get("l") or ""
    if not url or not e.get("t"):
        return None
    nowiso = L.iso(now)
    pub = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(e["p"])) if e.get("p") else ""
    title, media = e["t"], e.get("m") or ""
    return {"id": url, "url": url, "title": title, "media": media, "cat": T.cat_of("", title, media),
            "cross": 1, "published": pub, "burst": 0, "arts": 1, "breaking_candidate": True,
            "breaking_pick": {"url": url, "media": media, "title": title}, "cluster_members": [],
            "first_seen": nowiso, "last_seen": nowiso, "seen_count": 1, "last_report": nowiso, "report_count": 0,
            "event_key": url, "solo": 1, "seed": "gn"}


def _resolve(g, dec, live=True):
    """씨앗 url = 구글 뉴스 링크 → 원문(회차당 1회 · 최대 GN_DEC_TRY회 · 실패 = 구글 뉴스 링크 그대로 · 다음 회차 재시도).
    live = 이 프로세스가 구글을 두드려도 되나(킬스위치·확정 차단 = 시도 안 함 · 횟수도 안 깎는다)."""
    if g.get("ru") or (g.get("rt") or 0) >= L.GN_DEC_TRY or not (g.get("e") or {}).get("l") or not dec or not live:
        return
    g["rt"] = (g.get("rt") or 0) + 1
    try:
        u = dec(g["e"]["l"])
    except Exception:  # noqa: BLE001
        u = ""
    G = L._gn()
    if u and G is not None and G._host(u) not in G._PORTAL_HOSTS:
        g["ru"] = u


def _reurl(c, g):
    """구글 뉴스 링크로 만든 씨앗 = 원문 해제가 나중에 성공하면 링크만 원문으로(event_key·id = 첫 키 유지 · 푸시 원장 불변)."""
    ru = g.get("ru")
    if not ru or c.get("url") == ru or c.get("url") != (g.get("e") or {}).get("l"):
        return False
    c["url"] = ru
    if isinstance(c.get("breaking_pick"), dict):
        c["breaking_pick"]["url"] = ru
    return True


def _admit(k, arts, mt, urls, covered, sec_by_url, st, now):
    """이번 회차 한 매체 대표 중 이름이 맞는 것 1건 → 단독 입장 엔트리(없으면 None) · 자기 제목 적중 우선 → 이른 발행."""
    best = None
    for a in arts:
        if not (isinstance(a, dict) and a.get("is_cluster_rep") and a.get("link")):
            continue
        u = a["link"]
        if (a.get("cross_score") or 0) >= T.MIN_CROSS or u in urls or u in covered:
            continue                     # 다매체 대표 = to_candidates 몫 · 이미 수집함에 있는 기사·다매체 후보 멤버(불변식 ⓐ) = 제외
        sa = T._solo_age_h(a.get("published"), None, T.datetime.fromtimestamp(now, T.KST))
        if sa is None or sa >= T.SOLO_MAX_H or T.is_excluded_title(a.get("title") or ""):
            continue
        own = L.hit(k, a.get("title")) or L.hit(k, (a.get("breaking_pick") or {}).get("title"))
        if not (own or any(L.hit(k, mt.get(m)) for m in a.get("cluster_members") or [])):
            continue
        rk = (own, -(L._ts(a.get("published")) or now))
        if best is None or rk > best[0]:
            best = (rk, a)
    if not best:
        return None
    e = T.build_entry(best[1], sec_by_url, solo=True)
    nowiso = L.iso(now)
    e.update({"first_seen": nowiso, "last_seen": nowiso, "seen_count": 1, "last_report": nowiso,
              "report_count": 0, "event_key": e["url"], "lv": L.lv_of(st, k, now)})
    return e


def run(cands, arts, snap, st, now, gn_fetch=None, gn_decode=None, net=True, events=()):
    """한 회차 반영(순수 · 네트워크 = net=False 면 0 · 테스트는 gn_fetch/gn_decode 주입). 반환 = (cands, 통계 dict)."""
    S = {"att": 0, "adm": 0, "seed": 0, "sup": 0, "gnq": 0, "t": [0, 0, 0, 0]}
    eps = L.update(st, snap, now)
    mt = {a.get("link"): a.get("title") for a in arts if isinstance(a, dict) and a.get("link") and a.get("title")}
    mx = Matcher(mt)
    cands = list(cands)
    seed_keys = {L.norm_key((c.get("lv") or {}).get("k")) for c in cands if c.get("seed") and isinstance(c.get("lv"), dict)}
    keys = [k for k in eps if L.tier(eps[k], now) >= 1] + [k for k in seed_keys if k and k not in eps]
    live = [c for c in cands if _fresh(c, now)]
    M = {}
    for k in keys:
        ms = [(lv, c) for c in live for lv in (mx.level(k, c),) if lv]
        if ms:
            M[k] = ms
    real = lambda k: [(lv, c) for lv, c in M.get(k, []) if not c.get("seed")]   # noqa: E731
    # 우리 수집함 확인(무장·미확인만) — novel 판정은 나이 무관 전 후보 + 사건 원장 대조(묵은 사건 재점화 차단)
    if net:                              # 구글 뉴스 먼저 — 그 novel 판정이 아래 수집함 확인의 거부권(같은 회차에 쓴다)
        S["gnq"] = L.gn_poll(st, L.gn_candidates(st, now), now, fetch=gn_fetch)
    for k in keys:
        ep = eps.get(k)
        if ep and ep.get("a") and not ep.get("cf") and real(k):
            if ((st.get("gn") or {}).get(k) or {}).get("nov") == 0:
                continue                 # 구글 뉴스가 「무장 전 보도 있음」 = 묵은 사건 재점화 — 다매체 묶음만 남는 우리 기록으로는 못 보는 선행 보도(평의회260929-2 #7 = 'o' 7건 중 6건)
            older = [c for c in cands if not _fresh(c, now) and mx.level(k, c)] + [e for e in events if L.hit(k, e["title"])]
            L.confirm_ours(ep, [c for _, c in real(k)], now, older)
    # ① 입장 — t2↑ 인데 맞는 실후보가 없고 이번 회차 한 매체 대표가 있으면 단독 1보 규칙으로 들인다(씨앗이 있어도 = 아래 ②가 이관)
    urls = {c.get("url") for c in cands}
    covered = set()
    for c in cands:
        if not T.is_solo(c):
            covered.update(c.get("cluster_members") or [])
    sec_by_url = {a.get("link"): T.cat_ko(a.get("category")) for a in arts if isinstance(a, dict)}
    for k in keys:
        ep = eps.get(k)
        if L.tier(ep, now) < 2 or real(k):
            continue
        e = _admit(k, arts, mt, urls, covered, sec_by_url, st, now)
        if e:
            cands.insert(0, e)
            urls.add(e["url"])
            M.setdefault(k, []).append((2, e))
            S["adm"] += 1
    # ② 이관 — 씨앗과 같은 이름의 실후보가 생겼으면 씨앗을 넘기고 지운다(되살아난 씨앗 = 장부 sup 로 같은 곳에 다시 이관)
    drop, sup = set(), st.setdefault("sup", {})
    by_url = {c.get("url"): c for c in cands}
    for s in [c for c in cands if c.get("seed")]:
        k = L.norm_key((s.get("lv") or {}).get("k"))
        rs = real(k)
        tgt = _pick(rs, eps.get(k)) if rs else None
        if tgt is None and isinstance(sup.get(s.get("url")), dict):
            tgt = by_url.get(sup[s["url"]].get("u"))
        if tgt is not None and tgt is not s and not tgt.get("seed"):
            supersede(s, tgt)
            drop.add(id(s))
            sup[s["url"]] = {"u": tgt.get("url"), "at": int(now)}
            if k and not any(c is tgt for _, c in M.get(k, [])):
                M.setdefault(k, []).append((1, tgt))   # 장부로 이관된 실후보 = 이 이름의 후보(같은 회차 씨앗 재생성 차단)
            S["sup"] += 1
    if drop:
        cands = [c for c in cands if id(c) not in drop]
        M = {k: [(lv, c) for lv, c in ms if id(c) not in drop] for k, ms in M.items()}
        M = {k: ms for k, ms in M.items() if ms}
    st["sup"] = {u: v for u, v in sup.items() if isinstance(v, dict) and now - (v.get("at") or 0) < L.KEEP_H * 3600}
    # 이관 장부 역참조 — 씨앗을 넘겨받은 실후보가 한 회차 빠졌다가(단독 좌석·상한 컷·옛 사본 착지) 같은 기사로 다시 들어오면
    #   event_key 가 자기 url 로 새로 박혀 씨앗과의 연결이 끊긴다(평의회3 260929 재현 = 2발) → 장부의 씨앗 키를 다시 잇는다
    back = {v.get("u"): su for su, v in st["sup"].items() if v.get("u")}
    for c in cands:
        su = back.get(c.get("url"))
        if su and not c.get("seed") and (not c.get("event_key") or c.get("event_key") == c.get("url")):
            c["event_key"] = su
    # ③ 첨부 — 이름마다 한 후보 · 후보마다 가장 센 이름 하나
    offer = {}
    for k in keys:
        ep = eps.get(k)
        t = L.tier(ep, now)
        if not t or k not in M:
            continue
        if t == 1 and not (set(L.active(ep, now)) & TRENDS):
            continue                     # 커뮤니티 한 갈래만 = 붙이지 않는다(단일 원천 잡음)
        c = _pick(M[k], ep)
        lv = L.lv_of(st, k, now)
        rank = (lv["t"], len(lv.get("f") or ""), lv.get("c") or 0, len(k))
        if id(c) not in offer or rank > offer[id(c)][0]:
            offer[id(c)] = (rank, k, lv)
    for c in cands:
        old = c.get("lv") if isinstance(c.get("lv"), dict) else None
        o = offer.get(id(c))
        if o:
            _, k, lv = o
            if old and L.lv_tier(c) >= L.TIER_STRONG and lv["t"] < L.TIER_STRONG:
                # [강] 동결(도장 불변) — 같은 이름이면 더 센 수치만 받는다(식은 수치로 꼬리표가 약해져 재판정 때 [강] 근거가 빈약해지는 것 차단) ·
                #   다른 이름의 [중]·[약]은 [강] 증거를 덮지 않는다
                lv = _keep_strong(old, lv) if L.norm_key(old.get("k")) == k else old
            if lv != old:
                c["lv"] = lv
                S["att"] += 1
            eps[k]["u"] = c.get("url")
        elif old and L.lv_tier(c) < L.TIER_STRONG:
            c.pop("lv", None)            # [중]·[약] = 신호가 꺼지면 내린다(도장 무관 · 판정 영향 0)
    # ④ 씨앗 — t3(구글 뉴스 확인)인데 우리 피드에 그 이름 기사가 없다
    G = L._gn() if net else None
    dec = gn_decode or ((lambda link: G.decode(link)) if G is not None else None)
    glive = bool(gn_decode) or (G is not None and L.gn_live(G) and L.GN_MAX_Q > 0)   # pc·폰(가정 IP · LIVE_GN_MAX_Q=0) = 해제도 안 한다
    for c in cands:                      # 이미 있는 씨앗 = 판정 상태를 장부에 적고(아래 재생성 규칙) · 구글 뉴스 링크면 원문 해제 재시도(상한까지)
        if c.get("seed") != "gn" or not isinstance(c.get("lv"), dict):
            continue
        k = L.norm_key(c["lv"].get("k"))
        sd = (st.get("sd") or {}).get(k)
        if isinstance(sd, dict) and sd.get("u") == c.get("url"):
            sd.update({f: c[f] for f in _SEED_KEEP if c.get(f) is not None})
        g = (st.get("gn") or {}).get(k) or {}
        if g and c.get("url") == (g.get("e") or {}).get("l"):
            _resolve(g, dec, glive)
            if _reurl(c, g):
                if isinstance((st.get("sd") or {}).get(k), dict):
                    st["sd"][k]["u"] = c["url"]
                if k in eps:
                    eps[k]["u"] = c["url"]
                urls.add(c["url"])
                S["reurl"] = S.get("reurl", 0) + 1
    for k in keys:
        ep = eps.get(k)
        if L.tier(ep, now) < 3 or ep.get("cs") != "g" or k in M:
            continue
        if any(k2 != k and M.get(k2) and _related(k, eps.get(k), k2, eps.get(k2)) for k2 in M):
            continue                     # 포함 관계 이름(「사회인」⊂「사회인야구」)에 후보(실후보·씨앗)가 이미 있다 = 같은 사건 · 씨앗 중복 차단
            #                              (260929 리플레이 실측 · 씨앗끼리도 = 「닛몰캐쉬」·「닛몰캐쉬 데이트폭력」 둘 다 [강]이면 씨앗 2개 = 2발 · 평의회3)
        if not L.novel_ours(ep, [c for c in cands if mx.level(k, c)] + [x for x in events if L.hit(k, x["title"])]):
            continue                     # 우리 수집함·사건 원장에 무장 3~24h 전 같은 이름 보도 = 묵은 사건 재점화(구글 결과만 보던 씨앗 경로 · 평의회3)
        g = (st.get("gn") or {}).get(k) or {}
        e0 = g.get("e") or {}
        if not e0.get("p") or now - e0["p"] >= T.SOLO_MAX_H * 3600:
            continue                     # 가장 이른 보도가 6h 넘음 = 단독 규칙상 곧 정리될 씨앗(만들지 않는다)
        _resolve(g, dec, glive)
        e = _seed_entry(k, ep, g, now)
        if not e or e["url"] in urls or e["url"] in covered:
            continue                     # 같은 기사가 이미 수집함에 있다(제목에 이름이 없던 것) = 씨앗 불필요
        if e["url"] in (st.get("sup") or {}):
            continue                     # 이미 실후보로 이관된 씨앗 = 다시 만들지 않는다(실후보가 단독 좌석에서 잠시 빠져도 · 깜빡임·재판정 차단 · #7 재현 11:01)
        sd = (st.get("sd") or {}).get(k) or {}
        if sd.get("u") == e["url"]:
            if sd.get("breaking_rubric") and not sd.get("breaking"):
                continue                 # 판정 NO 로 끝난 씨앗이 지금 없다 = 정리됨([단독] 경중 미달) · 다시 만들면 도장이 리셋돼 15분마다 재판정(한 번 YES = 발송 · 평의회3)
            e["first_seen"] = L.iso(sd.get("at") or now)   # 레인 덮어쓰기로 빠진 씨앗 = 처음 만든 시각·판정·채점 그대로 되살린다(재판정·재채점 콜 0 · 푸시 4h 창 불변 · 평의회260929-2 #5)
            e.update({f: sd[f] for f in _SEED_KEEP if sd.get(f) is not None})
        e["lv"] = L.lv_of(st, k, now)
        cands.insert(0, e)
        urls.add(e["url"])
        M.setdefault(k, []).append((2, e))   # 같은 회차 포함 관계 이름의 둘째 씨앗 차단(위 _related 검사가 본다)
        if sd.get("u") != e["url"]:
            st.setdefault("sd", {})[k] = {"u": e["url"], "at": int(now)}
        ep["u"] = e["url"]
        S["seed"] += 1
    # 판정·채점 대상 유지 — 한 매체뿐인 lv 엔트리(입장·씨앗)는 to_candidates 캐리 정리가 1차 후보 플래그를 내리므로 매 회차 다시 켠다
    #   ⚠ 채점 전(경중 없음)·긴급·경중 2↑만 — 경중 0·1 로 채점된 NO 는 켜지 않는다(260924 «경중 0·1 채점 즉시 신규서 내림» · 평의회260929-2 #8)
    for c in cands:
        if c.get("solo") and L.lv_tier(c) >= 2 and (c.get("cross") or 0) < 2 and _fresh(c, now, T.SOLO_JUDGED_H) \
                and (c.get("grade") is None or c.get("breaking") or (c.get("grade") or 0) >= 2):
            c["breaking_candidate"] = True
    for ep in eps.values():
        S["t"][L.tier(ep, now)] += 1
    return cands, S


def fit_budget(cands, max_bytes):
    """바이트 하드예산(to_candidates 와 같은 선) — 초과분은 꼬리부터 · lv·씨앗 엔트리는 보호."""
    blob = json.dumps(cands, ensure_ascii=False)
    cut = 0
    while len(blob.encode("utf-8")) > max_bytes:
        over = len(blob.encode("utf-8")) - max_bytes
        gone = 0
        for j in range(len(cands) - 1, -1, -1):   # 꼬리부터 초과분만큼 한 번에(재직렬화 1회 · 보호 엔트리 건너뜀)
            if gone >= over:
                break
            if cands[j].get("lv") or cands[j].get("seed"):
                continue
            gone += len(json.dumps(cands[j], ensure_ascii=False).encode("utf-8")) + 2
            del cands[j]
            cut += 1
        if not gone:
            break
        blob = json.dumps(cands, ensure_ascii=False)
    return blob, cut


def main():
    if "--bootstrap-git" in sys.argv:    # 콜드 스타트 보강(배포 때 1회 · 만성어 계수만 · L.bootstrap_git)
        st = L.load_state()
        n = L.bootstrap_git(st, time.time())
        L.save_state(st)
        print(f"만성어 계수 보강: tbs 스냅샷 {n}개(최근 {L.CHRONIC_H}h git 이력)")
        return 0
    if not L.ON:
        print("확산 신호 OFF(LIVE_SIGNAL=0) — 생략")
        return 0
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scraper" / "out" / "articles.json"
    raw = CAND.read_text(encoding="utf-8") if CAND.exists() else "[]"
    try:
        cands = json.loads(raw)
    except Exception as e:  # noqa: BLE001
        print(f"::warning::live_seed: candidates.json 파싱 실패 — 생략: {e}")
        return 0
    arts = T.load_json(src, [])
    st = L.load_state()
    now = time.time()
    cands, S = run(cands, arts if isinstance(arts, list) else [], L.load_snapshots(), st, now, events=load_events(now))
    blob, cut = fit_budget(cands, max(T.MAX_BYTES, len(raw.encode("utf-8"))))   # 이 스텝이 늘린 만큼만 되돌린다(입력이 이미 넘었으면 = 다음 수집 회차 to_candidates 몫)
    if blob != raw:
        import tempfile
        fd, tmp = tempfile.mkstemp(dir=str(CAND.parent), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(blob)
        os.replace(tmp, CAND)
    if not L.STATE_RO:
        L.save_state(st)                 # 폰·PC(LIVE_STATE_RO=1) = 저장 안 함 → 착지본의 상태 = 체크아웃 그대로 = 러너 것이 산다
    t = S["t"]
    print(f"확산: 이름 {sum(t)}(약 {t[1]} · 중 {t[2]} · 강 {t[3]}) · 첨부 갱신 {S['att']} · 입장 {S['adm']} · 씨앗 {S['seed']} · "
          f"이관 {S['sup']} · 구글뉴스 {S['gnq']}회 · 예산 트림 {cut}")
    for k, ep in sorted((st.get("k") or {}).items(), key=lambda kv: -L.tier(kv[1], now)):
        if L.tier(ep, now) >= 2:
            print("  " + L.tail(L.lv_of(st, k, now)) + (f" → {ep.get('u')}" if ep.get("u") else ""))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001 — 확산 신호는 수집을 못 깬다
        print(f"::warning::live_seed 실패(비치명 · 수집함 무변경): {type(e).__name__}: {e}")
        sys.exit(0)
