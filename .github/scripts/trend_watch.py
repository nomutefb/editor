#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""trend_watch.py — 급상승(핫 키워드) 알림 감시 + 웹푸시(운영자 260818 «급상승 = 구글 검색 1.5만회 이상으로
하자 · 그정도만 해도 안놓칠듯»).

⚠️⚠️ **키워드 알림(kw_watch.py)과 완전히 다른 물건이다**(운영자 260818 «별개인거 알지? 헷갈리지 않게 잘
   코드에 반영해줘»). 둘 다 이름에 「키워드」가 들어가고 같은 실검 데이터를 봐서 헷갈리기 쉽다.
     · **키워드 알림(kw_watch · 종류 kw · 보라)** = 운영자가 **직접 등록해둔 말**이 뜨는지 지켜본다
       = 「내가 찍어둔 걸 놓치지 않기 위한 것」. 대상 = 등록어 몇 개.
     · **이 파일(급상승 · 종류 trend · 초록)** = 등록한 적 없는데 **세상에서 갑자기 뜨는 말**을 알린다
       = 「내가 모르는 걸 발견하기 위한 것」. 대상 = 구글 급상승 전체.
   두 감시기는 원장도 따로 쓴다(push/kw_sent.json ↔ push/trend_sent.json) = 서로의 발송을 못 막는다.

무엇을(판정 = 검색량 한 축):
  · 원문 = viewer/sns_trends.json 의 `gtrends`(급상승 + 딸린 뉴스) ∪ `gtrends_pool`(24h 급상승 풀).
    두 자리 다 구글이 준 **검색량 추정치**(`vol`)를 들고 있다(실측 = 200 ~ 50,000 단위).
  · 발사선 = `vol >= TREND_MIN_VOL`(기본 15000 = 운영자 지정 «1.5만회 이상»).
  · 같은 말이 두 자리에 다 있으면 **큰 값 하나로 친다**(정규화 키로 중복 제거 = 한 말에 알림 2통 금지).

어떻게(부작용 최소 — kw_watch 계약 100% 계승):
  · 발송 = push_send.py --notify 재사용(중복 구현 0 · 구독자·VAPID·죽은구독 정리 전부 그쪽 계약).
  · dedup 원장 = push/trend_sent.json {정규화키: {first, vol, q}} · TTL 24h(그 뒤 같은 말이 또 뜨면 새 건).
  · ⚠️ **첫 회차 소급 차단** — 원장이 비어 있으면(= 이 기능이 방금 켜졌다) 지금 자격을 가진 말이 통째로
    발사된다. 첫 회차는 **발송 0 · 도장만** 찍고 다음 회차부터 새로 뜬 말만 쏜다(이슈 푸시와 같은 축).
  · 하루 상한 TREND_DAY_CAP(기본 12) = 폭주 가드.
  · fail-soft — 파일 없음·파싱 실패·발송 실패가 수집 파이프를 못 죽인다(항상 rc=0).

env: VAPID_PRIVATE_KEY·VAPID_SUBJECT(push_send.py가 소비) · TREND_MIN_VOL · TREND_DAY_CAP ·
     TREND_PUSH=0(끄기) · TREND_PUSH_DRY=1(실발송 없이 판정만 출력).
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SNS = ROOT / "viewer" / "sns_trends.json"
LEDGER = ROOT / "push" / "trend_sent.json"
PUSH = ROOT / ".github" / "scripts" / "push_send.py"

MIN_VOL = int(os.environ.get("TREND_MIN_VOL", "15000"))   # 운영자 260818 지정 = 구글 검색 1.5만회
# ⚠ 260819 실측 = 관측 창을 4시간으로 좁힌 뒤 그 창의 최대 검색량이 2,000이었다(같은 시각 24시간 창은 100,000).
#   그래서 이 문턱은 **좀처럼 안 걸린다** — 그게 계약이다(운영자 260819 «4시간 이내 1.5만 실제로 찍히면 그게 맞음»).
#   즉 「알림이 며칠째 0건」은 고장이 아니라 정상이고, 4시간 안에 진짜로 1.5만이 찍힌 말만 나간다.
#   ⚠ 다음 세션이 이걸 사고로 오진해 문턱을 임의로 낮추지 마라(값 변경 = 운영자 판단 · 레버 = TREND_MIN_VOL).
DAY_CAP = int(os.environ.get("TREND_DAY_CAP", "12"))      # 하루 상한(폭주 가드 · 260818 실측 = 1.5만↑ 중복제거 5건)
TTL_S = 24 * 3600                                          # 원장 수명(kw_watch 24h 창과 같은 값)
# ⚠ 첫 회차 도장은 **짧게 산다**(운영자 260819 «저녁에 한번 오긴했는데 그 이후에도 한번 기준치를 초과한거같은데 안찍혔어»).
#   실사고 = 260818 23:07 첫 회차에 자격 9건이 「도장만 찍고 발송 0」으로 처리됐는데, 그 도장이 일반 도장과 같은
#   24h 수명을 받아 **그 9건이 하루 내내 침묵**했다 — 그중 「현금 5만회」·「박수홍 5만회」는 다음 날 아침까지
#   화면에 자격을 유지한 채 알림이 한 통도 안 갔다(실측 = 06:36 회차 로그 「자격 8건 · 발송 1건」 = 나머지 7건이 그 도장에 막힘).
#   ⚠ 소급 폭탄 차단(첫 회차에 과거 누적분이 쏟아지는 것)은 **처음 켠 그 순간**만 필요한데 구판은 그 차단을 24h 유지했다.
#   → 첫 회차 도장에 `seed` 표식을 남기고 그 수명만 1시간으로 줄인다 = 폭탄은 그대로 막고, 1시간 뒤에도 여전히
#     자격을 유지하는 말(= 진짜로 계속 뜨는 말)은 정상 발송으로 넘어간다.
SEED_TTL_S = int(os.environ.get("TREND_SEED_TTL_S", "3600"))   # 첫 회차 도장 수명(기본 1h = 수집 주기 15분의 4회차)
RUN_CAP = int(os.environ.get("TREND_RUN_CAP", "3"))            # 회차당 발송 상한 — 한 번에 알림이 무더기로 오는 것 차단(구판은 회차 상한이 없어 한 회차에 자격분이 통째로 나갈 수 있었다)
# ⚠ 교차 가점(운영자 260819 «시그널이랑 블루스카이 겹치면 그 구글 실검 4시간 기준 1.5만을 잡는 그 변수 요소에
#   곱셈 가점을 해주셈 *1.2 그리고 블루스카이는 겹치면 *1.5임»).
#   같은 말이 다른 플랫폼에도 떠 있으면 그건 한 곳에서만 뜬 말보다 무겁다 → **검색량 자체를 올리는 게 아니라
#   1.5만을 재는 그 값에만** 곱한다(알림에 찍히는 숫자는 구글이 준 원값 그대로 = 거짓말 안 한다).
#   겹침 대상 = **지금 화면에 떠 있는 그 목록**(운영자 «각 플랫폼에 시간 기준이 있어야하니까 · 지금 보여지는
#   top10이랑 겹친다고 생각하면되») = 각 소스 상위 10위까지. 지난 목록은 안 본다 = 시간 기준이 저절로 생긴다.
#   ⚠ 가점은 **소스마다 한 번씩만**(운영자 «고유명사가 다른 형태도 2개씩 겹칠 수 있는데 그럴때는 가점은
#   시그널 가점, 블루스카이 가점 다 각각 1회씩만 가능») = 집합 포함 여부라 구조적으로 1회.
BOOST_SIG = float(os.environ.get("TREND_BOOST_SIG", "1.2"))    # 시그널 실시간 검색어 TOP10에도 있으면
BOOST_BSKY = float(os.environ.get("TREND_BOOST_BSKY", "1.5"))  # 블루스카이 실시간 트렌드 TOP10에도 있으면
XTOP_N = int(os.environ.get("TREND_XTOP_N", "10"))             # 「지금 보여지는 top10」 = 화면 상한과 같은 값
ON = (os.environ.get("TREND_PUSH", "1").strip() != "0")
DRY = (os.environ.get("TREND_PUSH_DRY") or "").strip() == "1"


def jload(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return d


def key(s):
    """중복 제거 키 — 소문자·공백 정규화(kw_watch norm 계승). 같은 말이 두 소스에 있어도 한 건."""
    return re.sub(r"\s+", " ", str(s or "").lower()).strip()


def ckey(s):
    """겹침 대조용 키 — 공백을 **지운다**(「리브 골프」 ↔ 「리브골프」가 같은 말로 잡히게)."""
    return re.sub(r"\s+", "", str(s or "").lower()).strip()


def xtop(items, *fields):
    """지금 화면에 떠 있는 그 목록 = 상위 XTOP_N 개의 겹침 키 집합(지난 목록은 안 본다)."""
    out = set()
    for x in (items or [])[:XTOP_N]:
        if not isinstance(x, dict):
            continue
        for f in fields:
            k = ckey(x.get(f))
            if k:
                out.add(k)
                break
    return out


def overlaps(k, pool):
    """겹침 판정 — 같은 말이거나, 한쪽이 다른 쪽을 통째로 품으면 겹친 것으로 본다.
    ⚠ 3글자 미만은 품기 판정을 안 한다(「현금」이 「현금영수증」에 걸리는 식의 오탐 차단 · 뷰어 대세 판정과 같은 축)."""
    if not k or not pool:
        return False
    if k in pool:
        return True
    if len(k) < 3:
        return False
    return any(len(p) >= 3 and (k in p or p in k) for p in pool)


def hot():
    """{키: (표시어, 검색량, 판정값, 겹친 곳)} — 두 소스 합집합, 같은 말은 **큰 검색량**으로.
    ⚠ 컷은 **가점을 얹은 뒤**에 잰다 — 먼저 자르면 겹쳐서 올라올 말이 컷 앞에서 죽는다(가점이 무의미해진다)."""
    t = jload(SNS, {}) or {}
    sig = xtop(t.get("signal"), "query", "q", "kw")
    bsky = xtop(t.get("bsky_trends"), "query", "q", "topic")
    raw = {}
    def put(q, v):
        k = key(q)
        if not k:
            return
        try:
            v = int(v or 0)
        except Exception:  # noqa: BLE001
            return
        if k not in raw or v > raw[k][1]:
            raw[k] = (str(q).strip(), v)
    for x in t.get("gtrends") or []:
        if isinstance(x, dict):
            put(x.get("query"), x.get("vol"))
    for x in t.get("gtrends_pool") or []:
        if isinstance(x, dict):
            put(x.get("q"), x.get("vol"))
    out = {}
    for k, (q, v) in raw.items():
        ck, where = ckey(q), []
        eff = float(v)
        if overlaps(ck, sig):
            eff *= BOOST_SIG
            where.append("시그널")
        if overlaps(ck, bsky):
            eff *= BOOST_BSKY
            where.append("블루스카이")
        if eff < MIN_VOL:
            continue
        out[k] = (q, v, int(round(eff)), where)
    return out


def send(q, vol, where=None):
    """발송 = push_send.py --notify 재사용(kw_watch send 문법 그대로 · 종류 trend = 초록 지구본).
    ⚠ 숫자는 구글이 준 **원값**을 쓴다(가점은 발사 여부만 정한다) · 겹친 곳은 꼬리에 붙여 왜 왔는지 보이게."""
    tail = (" · " + "·".join(where) + "에도 떠 있어요") if where else ""
    body = f"«{q}» 가 검색 {vol:,}회로 급상승 중이에요{tail}"
    if DRY:
        print(f"  [드라이런] 발송 생략 — {body}")
        return True
    try:
        r = subprocess.run([sys.executable, str(PUSH), "--notify", "📈 급상승", body,
                            "--url", "/#trend", "--tag", "nomute-trend-" + key(q), "--kind", "trend"],   # 묶음표 = **급상승어별 고유**(운영자 260819) — 고정이면 뒤에 뜬 말이 앞엣것을 덮는다
                           capture_output=True, text=True, timeout=180)
        print((r.stdout or "").strip()[-400:])
        if r.returncode != 0:
            print(f"::warning::급상승 푸시 rc={r.returncode} — {(r.stderr or '')[-200:]}", file=sys.stderr)
        return r.returncode == 0
    except Exception as e:  # noqa: BLE001
        print(f"::warning::급상승 푸시 실패(무시): {e}", file=sys.stderr)
        return False


def main():
    if not ON:
        print("급상승 알림 OFF(TREND_PUSH=0) — 감시 생략")
        return
    cur = hot()
    if not cur:
        print(f"검색 {MIN_VOL:,}회 이상 급상승어 없음 — 발송 0")
        return

    led = jload(LEDGER, {})
    if not isinstance(led, dict):
        led = {}
    now = int(time.time())
    led = {k: v for k, v in led.items()
           if isinstance(v, dict) and now - int(v.get("first") or 0) < (SEED_TTL_S if v.get("seed") else TTL_S)}   # TTL 지난 도장은 청소(같은 말 재발견 가능) · 첫 회차 도장(seed)은 1h만 = 침묵 고착 차단
    seeded = bool(led)   # 원장이 비어 있으면 = 방금 켜졌다 = 첫 회차
    fired, stamped = 0, 0

    for k, (q, vol, eff, where) in sorted(cur.items(), key=lambda x: -x[1][2]):   # 정렬 = 가점 얹은 값 순(무거운 것 먼저)
        if k in led:
            continue                      # 이미 이번 창에서 알린 말
        if seeded and fired >= DAY_CAP:
            print(f"급상승 하루 상한 {DAY_CAP} 도달 — 나머지 생략", file=sys.stderr)
            break
        if seeded and fired >= RUN_CAP:
            print(f"급상승 회차 상한 {RUN_CAP} 도달 — 나머지는 다음 회차로(도장도 안 찍는다 = 유실 0)", file=sys.stderr)
            break   # ⚠ 도장을 찍기 **전에** 끊는다 — 찍고 끊으면 그 말이 「알린 적 있음」으로 굳어 영영 안 나간다(위 첫 회차 사고와 같은 축)
        led[k] = {"first": now, "vol": vol, "q": q, **({"eff": eff, "x": where} if where else {})}
        if not seeded:
            led[k]["seed"] = 1   # 첫 회차 = 발송 안 한 도장 = 1시간 뒤 만료(위 SEED_TTL_S 사유)
        stamped += 1
        if not seeded:                    # 첫 회차 = 조용히 도장만(소급 폭탄 차단)
            continue
        fired += 1
        print(f"  📈 «{q}» 검색 {vol:,}회" + (f" ×{eff/max(1,vol):.2f}({'·'.join(where)}) → {eff:,}" if where else "") + " — 푸시")
        send(q, vol)

    if (stamped or fired) and not DRY:     # ⚠ 드라이런은 원장을 안 남긴다(남기면 진짜 첫 발송이 영영 스킵)
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        LEDGER.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
    note = " · 첫 회차라 발송 0(다음 회차부터 새로 뜬 말만)" if not seeded else ""
    print(f"✅ trend_watch: 자격 {len(cur)}건 · 발송 {fired}건 · 도장 {stamped}건{note}{' (드라이런)' if DRY else ''}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 — 감시 실패가 수집 파이프를 못 죽인다
        print(f"::warning::trend_watch 자체 실패(무시): {type(e).__name__} {e}", file=sys.stderr)
