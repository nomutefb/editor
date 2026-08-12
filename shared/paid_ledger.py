#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""paid_ledger — 종량제(실지불) 소비 일 합산 원장(평의회 260812 권고6 · LLM 0 · 네트워크 0 · stdlib only).

왜: 구독 축은 claude_meter 원장이 있는데 종량제(Gemini 이미지 등)는 산출물 원장 4종에 흩어져 있어
「하루 몇 장·몇 달러」가 매번 손 재집계였고(LLM 토큰 지도 ③표 = 「산정」 꼬리표), 리사이즈 burst(하루 12발)
같은 폭주가 다음날 숫자로 안 보였다. 이미 존재하는 원장만 합산한다(신규 API 콜 0 · 과금 0).

입력(전부 기계산출물 · 손편집 금지):
  · cards/*/thumbs/gen.json   — 픽 썸네일(Gemini) · 카드 폴더명 날짜(yymmdd-…)로 귀속
  · cards/*/usage.json        — 카드 슛 직영(gen_cards) · 동일 귀속
  · viewer/gen_out/resize.json — 비율 리사이즈 · srcUrl "uploads/<yymmddHHMMSS>-…"에서 날짜 추출
  · viewer/gen_out/free.json   — 뷰어 「이미지 생성」 · ts(KST) + engine(gemini|gpt · 260812부터 기록 · 구건 = unknown)

출력 = metrics/paid-usage.json (기계산출물 · as_of = 관측 최신 날짜 = 결정적 → 데이터 무변동이면 diff 0).
$ 추정 = Gemini $0.067/장(1K) — GPT Image는 단가 축 미등재라 장수만 센다(unknown 엔진은 구판 기본 Gemini로 귀속).
전 경로 fail-soft — 어떤 원장이 깨져도 나머지 축은 산출(rc 항상 0).

사용: python3 shared/paid_ledger.py                # 콘솔 표(최근 14일)
      python3 shared/paid_ledger.py --write metrics/paid-usage.json   # 원장 기록(metrics-rollup 2h 편승)
"""
import argparse
import datetime
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEMINI_USD = 0.067   # 1K 이미지 1콜(shared/models.json gemini_image 축 · CLAUDE.md 실측 표기)
KST = datetime.timezone(datetime.timedelta(hours=9))


def _jload(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return None


def _dir_date(stem):
    # cards/260811-2053-… → 2026-08-11 (yymmdd 접두 밖 형식 = None)
    m = re.match(r"^(\d{6})-", stem)
    if not m:
        return None
    s = m.group(1)
    try:
        return "20{}-{}-{}".format(s[:2], s[2:4], s[4:6])
    except Exception:
        return None


def _iso_date(ts):
    try:
        return datetime.datetime.fromisoformat(str(ts)).astimezone(KST).date().isoformat()
    except Exception:
        return None


def collect(days=14):
    cut = (datetime.datetime.now(KST) - datetime.timedelta(days=days)).date().isoformat()
    day = {}

    def bump(d, k, n=1):
        if not d or d < cut:
            return
        row = day.setdefault(d, {"thumb": 0, "cardshoot": 0, "resize": 0,
                                 "genfree_gemini": 0, "genfree_gpt": 0, "genfree_unknown": 0})
        row[k] = row.get(k, 0) + n

    for p in glob.glob(str(ROOT / "cards" / "*" / "thumbs" / "gen.json")):
        stem = Path(p).parent.parent.name
        items = _jload(p)
        if isinstance(items, list) and items:
            bump(_dir_date(stem), "thumb", len(items))
    for p in glob.glob(str(ROOT / "cards" / "*" / "usage.json")):
        stem = Path(p).parent.name
        items = _jload(p)
        n = len(items) if isinstance(items, list) else (1 if isinstance(items, dict) and items else 0)
        if n:
            bump(_dir_date(stem), "cardshoot", n)
    rz = _jload(ROOT / "viewer" / "gen_out" / "resize.json")
    if isinstance(rz, list):
        for it in rz:
            m = re.search(r"(\d{12})", str((it or {}).get("srcUrl") or "") + str((it or {}).get("url") or ""))
            d = None
            if m:
                s = m.group(1)
                d = "20{}-{}-{}".format(s[:2], s[2:4], s[4:6])
            bump(d, "resize", 1)
    fr = _jload(ROOT / "viewer" / "gen_out" / "free.json")
    if isinstance(fr, list):
        for it in fr:
            d = _iso_date((it or {}).get("ts"))
            eng = str((it or {}).get("engine") or "").strip().lower()
            k = "genfree_gpt" if eng == "gpt" else ("genfree_gemini" if eng == "gemini" else "genfree_unknown")
            bump(d, k, 1)

    out_days = {}
    for d in sorted(day):
        r = day[d]
        gem = r["thumb"] + r["cardshoot"] + r["resize"] + r["genfree_gemini"] + r["genfree_unknown"]   # unknown = 구판 기본 Gemini 귀속(가정 명시)
        r["gemini_calls"] = gem
        r["est_usd"] = round(gem * GEMINI_USD, 3)
        out_days[d] = r
    tot = {"gemini_calls": sum(r["gemini_calls"] for r in out_days.values()),
           "est_usd": round(sum(r["est_usd"] for r in out_days.values()), 3),
           "gpt_images": sum(r["genfree_gpt"] for r in out_days.values())}
    return {"as_of": (max(out_days) if out_days else ""), "window_d": days, "days": out_days, "totals": tot,
            "_": "기계산출물(손편집 금지) — shared/paid_ledger.py 합산 · Gemini $0.067/장 · GPT Image = 장수만(단가 미등재) · STT/Lyria/RVC = 별도 축(원장 없음)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--write", metavar="PATH")
    a = ap.parse_args()
    agg = collect(a.days)
    if a.write:
        p = ROOT / a.write
        p.parent.mkdir(parents=True, exist_ok=True)
        new = json.dumps(agg, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        old = ""
        try:
            old = p.read_text(encoding="utf-8")
        except Exception:
            pass
        if new != old:
            p.write_text(new, encoding="utf-8")
            print("paid_ledger: {} 기록(최근 {}일 Gemini {}콜 ≈ ${})".format(a.write, a.days, agg["totals"]["gemini_calls"], agg["totals"]["est_usd"]))
        else:
            print("paid_ledger: 변동 없음")
        return
    print("=== 종량제 일 합산(최근 {}일) ===".format(a.days))
    for d, r in agg["days"].items():
        print("{}  썸네일 {:3d} · 카드슛 {:2d} · 리사이즈 {:2d} · 생성 g{}/G{}/?{}  → Gemini {}콜 ≈ ${}".format(
            d, r["thumb"], r["cardshoot"], r["resize"], r["genfree_gemini"], r["genfree_gpt"], r["genfree_unknown"],
            r["gemini_calls"], r["est_usd"]))
    print("합계: Gemini {}콜 ≈ ${} · GPT Image {}장".format(agg["totals"]["gemini_calls"], agg["totals"]["est_usd"], agg["totals"]["gpt_images"]))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 — 최상위 fail-soft(합산 실패가 롤업 커밋을 못 깨뜨림)
        print("::warning::paid_ledger 예외(스킵): {}".format(e))
