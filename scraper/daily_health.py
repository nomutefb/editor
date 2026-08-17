#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 일일 점검 — 수집함 파이프라인 ①수집건강 ②알고리즘 신호 ③롤백 검토를 한 화면에.
#   운영자가 '섹션 할일/상태' 물을 때(일일 1회) 메인이 먼저 돌려 보고 → docs/curation-algorithm.md §7/§8과 대조.
#   정본 루틴 = CLAUDE.md §🧠 "일일 점검". 읽기 전용(candidates.json 안 건드림).
# 사용: python3 scraper/daily_health.py
import json
import subprocess
import datetime as dt
from collections import Counter
from datetime import timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAND = ROOT / "viewer" / "candidates.json"
SUBS = ROOT / "push" / "subscriptions.json"
SCRIPTS = ROOT / ".github" / "scripts"
KST = timezone(timedelta(hours=9))
CHECKPOINT = "checkpoint/algo-260720-gate-grade-open"   # 최신 알고리즘 분기 라벨(롤백 기준 — 게이트 grade 거부권 폐지 · 원복 = git revert 31544487[+stamp 충돌 대비])


def age_h(s, now):
    try:
        t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if not t.tzinfo:
            t = t.replace(tzinfo=timezone.utc)
        return (now - t).total_seconds() / 3600
    except Exception:
        return None


def count(script):
    try:
        r = subprocess.run(["python3", str(SCRIPTS / script), "--count"],
                           capture_output=True, text=True, timeout=40)
        return int((r.stdout or "").strip())
    except Exception:
        return None


def git(*args):
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args],
                              capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def _get_tokenizer():
    """독점률용 토큰화 — knews_scraper 정본 우선, 실행 환경에 feedparser 없으면 폴백 미러(social_burst 선례).
    ⚠️ 미러는 knews tokenize/same_topic(overlap≥3 OR jaccard≥0.5)와 동기 유지(후속 = tokenize SSOT 모듈화 §7)."""
    try:
        import sys
        sys.path.insert(0, str(ROOT / "scraper"))
        from knews_scraper import tokenize, same_topic
        return tokenize, same_topic
    except Exception:
        import re
        stop = {"속보", "단독", "종합", "포토", "영상", "인터뷰", "오늘", "내일", "오전", "오후",
                "기자", "그래픽", "사진", "코멘트", "전망", "관련", "현장", "이것", "그것",
                "공식", "전체", "주요", "기사"}

        def tokenize(title):
            t = re.sub(r"\[[^\]]*\]", " ", title or "")
            t = re.sub(r"<[^>]+>", " ", t)
            return {x for x in re.findall(r"[가-힣]{2,}|[A-Za-z]{2,}|[0-9]{2,}", t) if x not in stop}

        def same_topic(ta, tb):
            shared = ta & tb
            if not shared:
                return False
            if all(t.isdigit() for t in shared):   # 공유가 전부 숫자 = 정형 코너(만평·운세·날씨)의 날짜만 같은 것 = 다른 사건(정본 knews_scraper.same_topic 동기 · 260811)
                return False
            inter = len(shared)
            if inter >= 3:
                return True
            return inter / len(ta | tb) >= 0.5

        return tokenize, same_topic


def _cum_enter(x):
    """누적 칼럼 진입 자격 미러 — viewer/index.html 누적 술어(cross≥8 OR isBreaking OR followEnters)의
    파이썬 사본(파이썬이 viewer를 못 읽어서 · 값만 기계 대조 = check_follow_enters_parity 하드게이트).
    ⚠️ 근사 1: fpScore 강지문 완화 갈래(rc≥3 + 지문≥2.0)는 fp_dict 의존이라 미러 제외 = 과소계상(보수
       방향 · 구판 3벌과 동일한 근사라 계기판 기저값 연속성 유지).
    ⚠️ 근사 2: viewer 는 applyAutoGroups/mergeDecorate 로 group_id 형제를 **접고 cross 를 단순 합산**한 뒤
       이 술어를 돌린다(주석 정본 = "union 아닌 합"). 여기 입력은 병합 전 원자료라 합산분만큼 과소계상이다
       — 260805 실측 사고: 「평택 미군기지 무단침입」이 원자료 cross 6 이라 '묻힘'으로 세어졌으나 화면에선
       조선판 6 + 뉴시스판 2 = **8 로 CROSS_MIN 단독 통과해 이미 노출 중**이었다(누적 30위 · 렌더 캡처 실증).
       계기판을 보고 진입선을 손대기 전에 반드시 실물 렌더로 대조하라(원자료 재현만으로 판단 = 오진).
    ⚠️ 손복사 금지 — 이 함수 하나만 쓴다. 구판은 같은 술어가 3벌(_dominance·긴급부스트 신선창·묻힘 계측)
       손복사돼 있어 뷰어만 고치면 조용히 갈렸다(260805 8인 평의회 실측 = 패리티 게이트 0이던 사각)."""
    g = x.get("grade")
    brk = bool(x.get("breaking")) and (g is None or (g or 0) >= 2)
    rc = x.get("report_count") or 0
    fol = (x.get("cross") or 0) >= 4 and rc >= 6
    return (x.get("cross") or 0) >= 8 or brk or fol


def screen_merge(cands):
    """화면 병합 재현 — 뷰어 applyAutoGroups+mergeDecorate 미러(같은 group_id 형제를 앵커로 접고
    cross 는 **단순 합산**[정본 주석 = "union 아닌 합"]·breaking 은 OR·grade/report_count 는 max).
    ⚠️ 신설 사유(260811) = `_cum_enter` 근사 2("병합 전 원자료라 과소계상")를 **알림 발화 축에서** 해소한다.
       구판 buried_alert 는 그 한계를 본문에 「실물 렌더로 대조하세요」라는 **숙제**로 적어 보냈다 — 즉
       알림이 스스로 답할 수 있는 값을 안 내고 매 회차 사람(또는 다음 세션)에게 같은 실측을 처음부터
       다시 시켰고, 리포트 조치 칸도 「코드로 원인 판단 필요」로 고정됐다. 관측이 알림 **밖**에 있으면
       다음 세션이 추측으로 메운다(스레드 `[1차 실측]`·틱톡 `_e1`·요약실패 `_fk=code` 동축).
       계산은 **이미 손에 든 후보 파일만** 쓴다 = 추가 요청·네트워크·LLM 0.
    ⚠️ 낱말 기반 병합 금지(260625 안산↔청주 선례) — group_judge 가 '같은 실제 사건' YES 확정한
       group_id 만 접는다. 제목이 비슷하다는 이유로 접으면 다른 사건이 조용히 사라진다.
    ⚠️ 잔여 과소계상 = 수동 병합(applyMerges)은 운영자 기기 저장소라 파이썬이 못 읽는다 = 미러 밖.
    ⚠️ 랭킹 댐핑(_rankCross)은 미러 안 한다 — 진입 자격 게이트는 raw 합산값을 쓴다(정본 주석)."""
    fam = {}
    for i, x in enumerate(cands):
        g = x.get("group_id")
        if g:
            fam.setdefault(g, []).append(i)
    if not fam:
        return list(cands)
    drop, deco = set(), {}
    for gid, idxs in fam.items():
        if len(idxs) < 2:
            continue
        ai = next((i for i in idxs if cands[i].get("url") == gid), None)
        if ai is None:
            ai = sorted(idxs, key=lambda i: cands[i].get("cross") or 0, reverse=True)[0]
        anchor, mem = cands[ai], [cands[i] for i in idxs if i != ai]
        grades = [g for g in [anchor.get("grade")] + [m.get("grade") for m in mem] if g is not None]
        deco[ai] = {**anchor,
                    "cross": (anchor.get("cross") or 0) + sum((m.get("cross") or 0) for m in mem),
                    "breaking": bool(anchor.get("breaking")) or any(m.get("breaking") for m in mem),
                    "grade": max(grades) if grades else anchor.get("grade"),
                    "report_count": max([anchor.get("report_count") or 0]
                                        + [(m.get("report_count") or 0) for m in mem]),
                    "_mergeCount": len(mem)}
        drop.update(i for i in idxs if i != ai)
    return [deco.get(i, x) for i, x in enumerate(cands) if i not in drop]


def buried_counts(cands, now, intl_only=False):
    """묻힘(4h+ 인데 누적 칼럼 미진입) 집계 — (grade3 목록, grade2 건수).
    §1 "중요한 게 묻히면 안 됨"의 자동감시 실체. intl_only=True 면 260703 기지값과 이어지는 국제 스코프,
    False 면 전 카테고리(국내 포함 = 260805에 봉합한 계측 사각). 나이 = 발행 우선·수집 폴백(_dominance 동일)."""
    buried, b2 = [], 0
    for x in cands:
        if intl_only and not ((x.get("cat") == "국제") or bool(x.get("title_ko"))):
            continue
        a = age_h(x.get("published"), now)
        if a is None or a < 0:
            a = age_h(x.get("first_seen"), now)
        if a is None or a < 4 or _cum_enter(x):
            continue
        if x.get("grade") == 3:
            buried.append(x)
        elif x.get("grade") == 2:
            b2 += 1
    return buried, b2


def buried_alert():
    """묻힘 자동감시(운영자 260805 승인 "계측 자동화까지") — watchdog.yml 30분 주기가 호출.
    발단 = 이 파일이 §1 유일 자동감시를 자처하면서 ⓐ 워크플로 미등재 = **수동 전용**(호출 0건 실측)
    ⓑ 국제 스코프 필터 = 국내 사건 계측 밖. 둘 다 사람 눈이 유일한 검출기라는 뜻이었다.
    발화 = 전 카테고리 grade3(대형) 묻힘이 BURIED_G3_WARN 이상 — grade2(기저 76)는 상시라 알림 소음이
    되므로 본문 참고치로만 싣는다. 해소 = 자동 clear. 킬스위치 = BURIED_ALERT=0.
    ⚠️ 알림 id는 **건수 접미 회전**(buried-g3-N) — 고정 id면 뷰어 unread가 id축이라 메시지함을 한 번
    열면 영영 재점등이 안 된다(레포 관례 = brk-misfire-N·sys:quake:+time)."""
    import os
    import sys
    if os.environ.get("BURIED_ALERT") == "0":
        print("· 묻힘 감시 스킵(BURIED_ALERT=0)"); return 0
    warn_at = int(os.environ.get("BURIED_G3_WARN", "5"))
    try:
        cands = json.loads(CAND.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"::warning::묻힘 감시 스킵(candidates 읽기 실패): {e}"); return 0   # fail-soft
    now = dt.datetime.now(KST)
    raw3, _ = buried_counts(cands, now, intl_only=False)                # 원자료(병합 전) = 계기판 기저값 연속성용
    g3, g2 = buried_counts(screen_merge(cands), now, intl_only=False)   # 화면 재현 = 발화 판정 축(260811)
    # ⚠️⚠️ 260818 분리 계상 — 발화선이 **규칙 개정을 안 따라와** 매 회차 헛경고를 냈다.
    #   실측 = 260818 03:02 발화분 g3 17건 중 문화 3건이 「'성시경 열애설' 미요시 아야카」·「루시 최상엽
    #   결혼 발표」·「임원희 핑크빛 기류」였고, RUBRIC 원문을 열어보니 **전건 규칙대로 [3]**이다
    #   (gate_judge.py 「연예 예외」 = 최정상급 유명인의 열애·결별·결혼·이혼 = [3] · 「⚠ 열애·결별은
    #   «설» 단계도 [3]」 = 운영자 260817 확정). 즉 오채점이 아니라 **그날 운영자가 직접 올린 등급**이다.
    #   ⚠ 문제는 비교 기준이다 — 본문 기저값 「260805 = g3 3」은 260810 지위변동·260817 열애설 조항
    #   **이전** 숫자라, 조항이 열린 뒤 늘어난 연예 대형이 매일 「급증」으로 보고된다(개정의 자연 결과를
    #   결함으로 읽는다). 게다가 이 건들은 **구조적으로 화면에 못 올라간다** — 진입 자격이 등급이 아니라
    #   cross(받아쓴 매체 수)라 실측 cross 2~3인 연예 열애·결혼은 진입선 8을 영구 미달한다. 즉 조치 대상이
    #   아닌 항목이 발화선을 밀어올려 **진짜 묻힌 재난·국제 사건을 가린다**(260805 기저 3 → 발화선 5를
    #   연예 3건만으로도 절반 넘게 채운다).
    #   ⇒ grade2 를 「상시라 소음이 되므로 본문 참고치로만」 내리는 기존 관용구를 그대로 계승해(창작 0)
    #     연예 예외분을 **발화 판정에서 빼고 본문에는 그대로 싣는다** = 숨김 0·정보 손실 0.
    #   ⚠ 가르는 축 = cat=="문화"(연예 예외 조항이 [3]을 주는 유일한 카테고리)다. gossip 도장으로 가르면
    #     안 된다 — 실측 3건 중 「핑크빛 기류」가 그 정규식에 안 걸려 2/3만 잡히고(GOSSIP_RE 어휘 밖),
    #     「연예 지위 변동」([3] · 전속계약·그룹 해체)은 사생활 어휘가 아니라 아예 대상 밖이다.
    cul = [x for x in g3 if (x.get("cat") or "") == "문화"]             # 연예 예외 조항 [3] = cross 구조적 미달
    core = [x for x in g3 if (x.get("cat") or "") != "문화"]            # 발화 판정 축 = 조치 가능한 묻힘
    print(f"· 묻힘(전 카테고리 4h+ 누적 미진입): grade3 {len(core)}건"
          f"(원자료 {len(raw3)}건 · 연예 예외 {len(cul)}건 별도) · grade2 {g2}건 (발화선 g3≥{warn_at})")
    ids = [f"buried-g3-{n}" for n in range(0, 60)]                     # 회전 id 후보 = 이전 회차분 청소용
    for i in ids:                                                      # 구 건수 알림 제거(중복 점등 방지)
        if i != f"buried-g3-{len(core)}":
            subprocess.run([sys.executable, str(ROOT / "shared" / "msg.py"), "clear", i],
                           capture_output=True)
    if len(core) < warn_at:
        return 0
    lines = [f"묻힌 대형(grade3) {len(core)}건 — 4시간이 지났는데 누적 칼럼에 못 들어간 사건입니다."
             f" (같은 시점 grade2 묻힘 {g2}건 · 260805 기저 = g3 3·g2 78 ⚠️ 그 기저는 260810 지위변동·"
             f"260817 열애설 조항 **이전** 값이라 연예 예외분과는 비교 축이 다르다 = 그래서 아래처럼 갈랐다)", "",
             f"✅ 화면 병합을 재현한 뒤의 숫자입니다(원자료 {len(raw3)}건 → 같은 사건 묶기 반영 {len(core) + len(cul)}건"
             f" → 연예 예외 {len(cul)}건 분리 후 {len(core)}건)."
             " 아래 건들은 갈라진 형제를 합산해도 진입선에 미달 = 지금 화면에 실제로 없습니다."
             " 남은 오차 = 네 기기에만 있는 수동 병합(코드가 못 읽음).", ""]
    # 같은 사건 묶기(group_id)가 아직 안 붙은 건 = screen_merge 가 **구조적으로 못 접는 조각**이다.
    #   그 조각은 같은 사건의 본 덩어리가 이미 화면에 있어도 혼자 작은 cross 로 남아 '묻힘'에 잡힌다
    #   → 목록이 그만큼 부풀고, 그 숫자를 믿고 진입선을 내리면 실제로는 안 묻힌 사건까지 통과시킨다.
    #   ⚠ 실측 260812 = 묻힘 8건 중 5건이 묶기 미부착이었고 그중 콜롬비아 지진 3건은 **같은 사건이
    #     cross 13 으로 이미 화면에 있었다**(같은 지진 관련 후보 10건 중 6건만 group_id 보유).
    #   ⚠ 여기서 낱말로 묶지는 않는다(screen_merge 주석 「낱말 기반 병합 금지 · 260625 안산↔청주 선례」
    #     동축) — 묶기 **유무라는 사실만** 싣고 판정은 사람이 한다. 붙이는 건 표시뿐이라 사라지는 항목 0.
    nogrp = [x for x in core if not x.get("group_id")]
    for x in core[:8]:
        _mc = x.get("_mergeCount")
        lines.append(f"· {(x.get('title') or '')[:52]}"
                     f" (cr{x.get('cross') or 0}·rc{x.get('report_count') or 0}·{x.get('cat') or '?'}"
                     + (f"·형제{_mc}건 합산" if _mc else "")
                     + ("" if x.get("group_id") else "·묶기없음") + ")")
    # 연예 예외분 = 발화 판정에서 빼되 **본문에는 그대로 싣는다**(숨김 0) — 조치 축이 다르다는 것만 명시.
    if cul:
        lines += ["", f"[연예 예외 {len(cul)}건 · 발화 판정에서 제외 = 조치 대상 아님]"]
        for x in cul[:6]:
            lines.append(f"· {(x.get('title') or '')[:52]}"
                         f" (cr{x.get('cross') or 0}·rc{x.get('report_count') or 0}·문화)")
        lines += ["  ↑ RUBRIC 「연예 예외」 조항이 [3]을 주는 건들이다(최정상급 유명인의 열애·결별·결혼·"
                  "이혼·범죄 = [3] · 열애·결별은 «설» 단계도 [3] = 운영자 260817). **오채점이 아니다.**",
                  "  진입 자격은 등급이 아니라 cross(받아쓴 매체 수)라서 매체가 적게 받아쓴 연예 건은"
                  " 등급이 최고여도 진입선 8을 구조적으로 못 넘는다 = 코드로 고칠 자리가 없다.",
                  "  이 건들을 화면에 올리고 싶으면 진입선이 아니라 **연예 전용 진입 경로**를 여는 별건"
                  " 판단이 필요하다(운영자 축 · 지금 발화선을 내리면 진짜 묻힌 재난·국제가 같이 헐거워진다)."]
    lines += ["", "진입 자격 = cross≥8 OR 긴급 OR followEnters(cross≥4 ∧ [rc≥6 OR rc≥5+grade≥2 OR rc≥3+강지문]).",
              "위 건들은 셋 다 미달이라 화면에서 사라진 상태입니다.",
              "",
              # ⚠️ 구판(260811)은 여기에 「5건 중 1건(연예 소속사 사명 변경)이 대형 오채점이었다」를
              #   **하드코딩**해 매 회차 내보냈다. 260812 재검증 결과 그 단정은 **틀렸다** — RUBRIC 의
              #   「연예 지위 변동」 조항(최정상급 연예인·그룹의 소속사 이탈·전속계약 = [3] · 운영자 260810
              #   확정)에 정면으로 해당하고, 회귀 정답지에도 같은 형태가 expect=3 으로 박제돼 있다
              #   (grade_regress_cases.json 「트와이스 정연 … 바로엔터와 전속계약 [공식]」 · 대조군 =
              #   「손흥민 LA FC 이적」 expect=0 = 스포츠 구단 이동은 별개).
              #   → 과거 1회의 판정을 영구 문구로 박으면 **다음 세션이 그걸 사실로 읽고 엉뚱한 축을 판다**
              #   (실제로 260812 세션이 그 문구를 믿고 오채점이라 보고했다가 RUBRIC 원문을 열고 정정했다).
              #   ⇒ 단정은 걷어내고, **매 회차 기계가 실제로 잰 값**(묶기 미부착 건수)만 싣는다.
              (f"⚠️ 이 중 {len(nogrp)}건은 같은 사건 묶기가 아직 안 붙었습니다(위 「묶기없음」 표시)."
               " 묶기가 없으면 화면 병합이 구조적으로 불가능해서, 같은 사건의 본 덩어리가 이미 화면에"
               " 올라가 있어도 조각만 따로 이 목록에 남습니다 — 그만큼 부풀어 보입니다."
               " 먼저 그 건들이 이미 화면에 있는 사건의 조각인지 보고, 조각이면 묻힘이 아니라"
               " 같은 사건 묶기(group_judge) 축입니다." if nogrp else
               "⚠️ 전건 같은 사건 묶기가 붙어 있습니다 = 조각으로 부푼 건 없습니다."),
              "⚠️ 숫자만 보고 진입선을 내리지 마세요 — 등급이 어긋난 건이 섞여도 발화선이 그만큼 쉽게"
              " 넘습니다. 각 건의 등급이 맞는지 RUBRIC 원문(.github/scripts/gate_judge.py)으로 대조하고,"
              " 실제로 어긋났으면 채점 축(grade RUBRIC)으로 가세요.",
              "확인 = python3 scraper/daily_health.py · 임계 정본 = docs/curation-algorithm.md §★"]
    subprocess.run([sys.executable, str(ROOT / "shared" / "msg.py"), "set",
                    f"buried-g3-{len(core)}", "\n".join(lines), "warn"], capture_output=True)
    print(f"::warning::묻힌 grade3 {len(core)}건(연예 예외 {len(cul)}건 제외 · 발화선 {warn_at}) — 알림 점등")
    return 0


def _dominance(cands, now):
    """독점률 = 누적칼럼 근사 상위30 중 최대 단일사건 점유%(도배 재발 감지 · 260702 fable패널 수정안).
    풀 = 누적자격 미러(나이≥4h AND [cross≥8 OR 긴급 OR followEnters]) · 정렬 = cross^1.3×timeAcc(13·3.0).
    뷰어 scScore 근사(gradeW·긴급부스트 생략 — 실측 교집합 27/30·평시 3%). 상수는 §★ 정본과 짝(변경 시 갱신).
    반환 (점유%, 건수, 대표제목) 또는 None(풀<15 = 심야 표본 부족·판정 유보)."""
    pool = []
    for c in cands:
        a = age_h(c.get("published"), now)
        if a is None or a < 0:                      # 발행 없음/미래 오기록 → 수집시각 폴백
            a = age_h(c.get("first_seen"), now)
        if a is None or a < 4:
            continue
        if _cum_enter(c):                           # 진입 자격 = 단일 정본(260805 · 손복사 3벌 → 1벌)
            pool.append((c, a))
    if len(pool) < 15:
        return None
    scored = sorted(pool, key=lambda x: ((x[0].get("cross") or 0) ** 1.3) / (1 + (x[1] / 13) ** 3.0),
                    reverse=True)[:30]
    top = [c for c, _ in scored]
    tokenize, same_topic = _get_tokenizer()
    toks = [tokenize(c.get("title") or "") for c in top]
    parent = list(range(len(top)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(len(top)):
        for j in range(i + 1, len(top)):
            if toks[i] and toks[j] and same_topic(toks[i], toks[j]):
                parent[find(j)] = find(i)
    groups = Counter(find(i) for i in range(len(top)))
    root, size = groups.most_common(1)[0]
    return size / len(top) * 100, size, (top[root].get("title") or "")


def main():
    now = dt.datetime.now(timezone.utc)
    nowk = now.astimezone(KST)
    try:
        c = json.loads(CAND.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ candidates.json 로드 실패: {e}")
        return
    print(f"═══ 일일 점검 · {nowk:%Y-%m-%d %H:%M} KST · 후보풀 {len(c)}건 ═══\n")

    # ─────────── ① 수집 건강 ───────────
    ages = [age_h(x.get("first_seen"), now) for x in c]
    valid = [a for a in ages if a is not None]
    newest = min(valid) if valid else None
    fresh4 = sum(1 for a in valid if a < 4)
    fresh24 = sum(1 for a in valid if a < 24)
    print("① 수집 건강")
    if newest is None:
        print("  ⚠️ 수집시각(first_seen) 불명 — 스크랩 점검 필요")
    else:
        f = "✅" if newest < 2 else ("⚠️" if newest < 6 else "❌")
        print(f"  {f} 최신 수집 {newest:.1f}h 전 · 최근4h {fresh4}건 · 최근24h {fresh24}건"
              + ("  (←2h 넘으면 스크랩 지연 의심)" if newest >= 2 else ""))
    nb, ng = count("breaking_judge.py"), count("gate_judge.py")
    if nb is not None and ng is not None:
        f = "✅" if (nb + ng) < 120 else "⚠️"
        print(f"  {f} 미판정 backlog: 속보 {nb} · 경중 {ng} (>120 누적이면 판정 적체 의심)")
    else:
        print("  ⚠️ backlog 카운트 실패(judge 스크립트 점검)")
    try:
        subs = json.loads(SUBS.read_text(encoding="utf-8"))
        print(f"  · 웹푸시 구독자 {len(subs) if isinstance(subs, list) else '?'}명")
    except Exception:
        print("  · 웹푸시 구독자 0명(또는 미생성)")
    # RSS 피드 건강 원장(scraper/obs/feed_health.json 안정본 — 죽은피드 구성 변화시 scrape가 갱신 · 무음 드리프트 방지 260702)
    try:
        fh = json.loads((ROOT / "scraper" / "obs" / "feed_health.json").read_text(encoding="utf-8"))
        # 원소 dict 정규화 — 부분 손상 시 요약줄 출력 후 순회서 터져 '생존'+'원장없음' 이중출력 모순 방지(평의회 260702)
        deadf = [x for x in (fh.get("dead_feeds") or []) if isinstance(x, dict)]
        zomb = [x for x in (fh.get("zombie_feeds") or []) if isinstance(x, dict)]
        okn = fh.get("ok") or 0   # null도 0 표시(리터럴 None 방지) — 임계·표시 기준은 리스트 길이로 단일화
        f = "✅" if len(deadf) <= 5 else "⚠️"
        print(f"  {f} RSS 피드 생존 {okn}/{okn + len(deadf)} (죽음 {len(deadf)})"
              + ("  (←죽음 6↑ = feeds.csv 정리 검토)" if len(deadf) > 5 else ""))
        for x in deadf[:5]:
            print(f"      ✗ {x.get('publisher', '?')} {x.get('title', '')}")
        if len(deadf) > 5:
            print(f"      … 외 {len(deadf) - 5}개 (scraper/obs/feed_health.json)")
        if zomb:   # 응답은 오는데 갱신 멈춘 피드(JTBC 2024-10 멈춤 실측 케이스) — 주간 니치 피드는 일시 오탐 가능
            print(f"  🧟 좀비 피드(응답 OK·24h 발행 0) {len(zomb)}개: "
                  + " · ".join(f"{x.get('publisher', '?')} {x.get('title', '')}" for x in zomb[:4])
                  + (" …" if len(zomb) > 4 else ""))
        # orphan 피드 경보(260703 분신술 §7④): 생존(비dead·비zombie)인데 최근 7일 '대표(rep) 후보' 0
        #  = 무성과 피드가 '생존 151' healthy 집계에 은폐되던 것 표면화. ⚠️ '수집 0' 아님 — 멤버로 cross
        #  기여는 가능(KED글로벌 = followEnters 4번째 매체 pivotal → 제거 금지 · §8 260703). 기지(baseline)는 정보줄·신규만 ⚠️.
        try:
            import csv
            pubs = Counter()
            with (ROOT / "scraper" / "feeds.csv").open(encoding="utf-8") as fp:
                for row in csv.DictReader(fp):
                    p = (row.get("publisher") or "").strip()
                    if p:
                        pubs[p] += 1
            bad = Counter((x.get("publisher") or "").strip() for x in deadf + zomb)
            alive_pubs = {p for p, n in pubs.items() if bad.get(p, 0) < n}   # 피드 1개라도 생존하면 alive
            reps7 = Counter((x.get("media") or "").strip() for x in c
                            if (age_h(x.get("first_seen"), now) or 999) < 168)
            orphan = sorted(p for p in alive_pubs if reps7.get(p, 0) == 0)
            KNOWN_ORPHAN = {"KED글로벌", "NYT코리아"}   # baseline(§8 260703 실측 — 신규 등장분만 경보)
            if orphan:
                new_o = [p for p in orphan if p not in KNOWN_ORPHAN]
                flag = "⚠️" if new_o else "·"
                print(f"  {flag} orphan 피드(생존·7일 대표후보 0) {len(orphan)}곳: " + " · ".join(orphan[:6])
                      + (" …" if len(orphan) > 6 else "")
                      + ("  ← 신규 orphan = 수집되는데 후보 전무(클러스터·피드 점검)" if new_o
                         else "  (기지 — 멤버 cross 기여형·제거 금지 §8 260703)"))
        except Exception as e:
            print(f"  · orphan 계산 실패(비치명): {e}")
    except Exception:
        print("  · 피드 건강 원장 없음(다음 scrape 런부터 생성)")

    # ─────────── ② 알고리즘 신호 ───────────
    gd = Counter(x.get("grade") for x in c)
    brk = [x for x in c if x.get("breaking")]
    brk24 = [x for x in brk if (age_h(x.get("first_seen"), now) or 99) < 24]
    bc = sum(1 for x in c if x.get("breaking_candidate"))
    # 승격 구제분(저burst grade3 신선) = compare_collected.promoted_guess와 동일 정의
    promo = [x for x in c if (x.get("grade") or 0) >= 3 and x.get("breaking_candidate")
             and (x.get("burst") or 0) < 3 and "[속보]" not in (x.get("title") or "")
             and "[긴급]" not in (x.get("title") or "")]
    urg = [x for x in brk if (x.get("grade") or 0) >= 2 and (age_h(x.get("first_seen"), now) or 99) < 4]
    print("\n② 알고리즘 신호")
    print(f"  · grade 분포 {{0:{gd.get(0,0)} 1:{gd.get(1,0)} 2:{gd.get(2,0)} 3:{gd.get(3,0)} 미채점:{gd.get(None,0)}}}")
    print(f"  · breaking 확정 {len(brk)}(24h내 {len(brk24)}) · breaking_candidate {bc} · ⬆️저burst승격 {len(promo)}")
    f = "✅" if len(urg) < 8 else "⚠️"
    print(f"  {f} 현재 🚨긴급자격(breaking&grade≥2&<4h) {len(urg)}건"
          + ("  (←8↑면 긴급 과다 의심)" if len(urg) >= 8 else ""))
    # ⚡이슈 배지 계기판(260702 정적 10 확정·fable 4인 — 캘린더 재측정 폐지의 대가로 지불하는 상시 감시 1줄 · §8 260702)
    #  근사 = viewer issCross의 badgeJunk(정형컷 정규식 4종) 미반영(3본째 미러 회피·±3건) — cross·grade·grade3우회·나이창만.
    #  나이 = max(발행, first_seen) 근사(scBadgeType 동일 원칙). 상한 경보 = 재인플레(남발 재발) · 하한 0 = 과조임/수집장애 의심.
    def _iss_age(x):
        a1, a2 = age_h(x.get("published"), now), age_h(x.get("first_seen"), now)
        cand = [v for v in (a1, a2) if v is not None]
        return max(cand) if cand else None
    def _iss_ok(x):
        g, cr = x.get("grade"), (x.get("cross") or 0)
        return (g is None or g >= 2) and (cr >= 10 or (g == 3 and cr >= 8))
    issq = [x for x in c if _iss_ok(x) and (_iss_age(x) or 99) >= 4 and (_iss_age(x) or 99) < 24]
    resv = [x for x in c if (x.get("grade") is None or (x.get("grade") or 0) >= 2) and x.get("grade") != 3
            and 8 <= (x.get("cross") or 0) <= 9 and (_iss_age(x) or 99) >= 4 and (_iss_age(x) or 99) < 24]
    f = "⚠️" if (len(issq) >= 30 or len(issq) == 0) else "✅"
    print(f"  {f} ⚡이슈배지 자격(근사·badgeJunk 미반영 ±3) {len(issq)}건 · cr8~9 저수지 {len(resv)}건"
          + ("  (←30↑ = 재인플레 의심 → §8 260702 실측환산 절차로 임계 재조정)" if len(issq) >= 30 else "")
          + ("  (←0 = 과조임/수집장애 의심)" if len(issq) == 0 else "  (기준 260702=13~20 · 저수지 급증 = 다음 인플레 전조)"))
    # OUT 아웃라이어 감쇠하한 계기판(260706 §8 — §1 보수성: '완화'엔 상시 측정+상한 경보가 짝 · 배지 계기판 선례)
    #  근사 = viewer 파이프 *순서* 재현: scDedup(동일제목·12h내 우세 1장) → group_id 병합·_rankCross 댐핑.
    #  ⚠️ scDedup 생략 금지(260706 심야 정정): 빼먹으면 동일제목 파편이 합산에 살아남아 과보고(cr44 아티팩트 — 실파이프는 cr30·g1 = 무자격 · §8 정정).
    #  badgeJunk(정형컷)·수동병합(localStorage)·검색동결은 미반영(±1). 기준 = 0~5 정상(도입 스냅샷 실측 2 — 장윤기·정보통신망법) · ≥6 = 과발동 조사(§8 260706) · 강건 z(중앙값+MAD)·풀<15 OFF = viewer 동값.
    try:
        def _oa(x):   # 나이(h) 근사 — published 우선·없으면 first_seen(scTs 요지)
            v = age_h(x.get("published"), now)
            return v if v is not None else age_h(x.get("first_seen"), now)
        _rep, cd = {}, []
        for x in c:   # scDedup 재현: 동일 정규화 제목 AND 나이차 <12h = 우세(cross→rc) 1장만
            k = "".join((x.get("title") or "").split()).lower()
            if not k:
                cd.append(x)
                continue
            pi = _rep.get(k)
            if pi is not None and abs((_oa(x) or 999) - (_oa(cd[pi]) or 999)) < 12:
                if ((x.get("cross") or 0), (x.get("report_count") or 0)) > ((cd[pi].get("cross") or 0), (cd[pi].get("report_count") or 0)):
                    cd[pi] = x
                continue
            _rep[k] = len(cd)
            cd.append(x)
        grp = {}
        for x in cd:
            gid = x.get("group_id")
            if gid:
                grp.setdefault(gid, []).append(x)
        merged, dropped = {}, set()
        for gid, cards in grp.items():
            if len(cards) < 2:
                continue
            anchor = next((x for x in cards if x.get("url") == gid), None) or max(cards, key=lambda x: x.get("cross") or 0)
            summed = sum(x.get("cross") or 0 for x in cards)
            base = anchor.get("cross") or 0
            cap = base * 1.5   # MERGE_DAMP_RATIO 1.5·GAIN 0.75 = viewer mergeDecorate 동값
            rank = summed if summed <= cap else cap + (summed - cap) * 0.75
            grades = [x.get("grade") for x in cards if x.get("grade") is not None]
            merged[id(anchor)] = {**anchor, "cross": summed, "_rank": rank,
                                  "report_count": max((x.get("report_count") or 0) for x in cards),
                                  "grade": max(grades) if grades else anchor.get("grade")}
            dropped.update(id(x) for x in cards if x is not anchor)
        pool = [merged.get(id(x), x) for x in cd if id(x) not in dropped]
        xs = sorted(v for v in ((x.get("_rank") or x.get("cross") or 0) for x in pool) if v >= 8)
        def _med(a):
            m = len(a) // 2
            return a[m] if len(a) % 2 else (a[m - 1] + a[m]) / 2
        if len(xs) < 15:
            print("  · OUT 감쇠하한: 통계 풀 <15 (콜드스타트) — 완화 OFF 상태")
        else:
            med = _med(xs)
            sd = max(1.4826 * _med(sorted(abs(v - med) for v in xs)), 2)
            outs = [x for x in pool
                    if (_iss_age(x) or 99) < 24 and (x.get("report_count") or 0) >= 6 and _iss_ok(x)
                    and ((x.get("_rank") or x.get("cross") or 0) - med) / sd >= 2.5]
            f = "✅" if len(outs) < 6 else "⚠️"
            print(f"  {f} OUT 감쇠하한 발동(근사·badgeJunk/수동병합 미반영) {len(outs)}건 (med {med:.1f}·σr {sd:.2f})"
                  + ("  (←6↑ = 과발동 → §8 260706 임계 재검토)" if len(outs) >= 6 else "  (기준 0~5 · 도입 스냅샷 실측 2)"))
            for x in outs[:3]:
                print(f"      · z{(((x.get('_rank') or x.get('cross') or 0) - med) / sd):.1f} cr{x.get('cross')} rc{x.get('report_count')} {str(x.get('title') or '')[:36]}")
    except Exception as e:
        print(f"  · OUT 계기판 계산 실패(비치명): {e}")
    # 긴급부스트 신선창 계기판(260717 §8 — 24h 풀 ×3.0 폐지 → 1~6h 이징 전환의 실전 궤적 축적 · OUT 계기판 선례)
    #  근사 = scScore 6항 중 dedup·병합(_rankCross)·픽/확인·OUT하한 미반영(±) — cross^1.3·timeAcc·연속보도·경중·신곡선부스트·ageMul만 재현.
    #  부스트 창 <6h·이징 g12 = viewer BOOST_RAMP_END_H·BOOST_EASE_G 동값(§★ — 곡선 재조정 시 여기도 동기). 나이 = max(발행,first_seen).
    #  기준 = '12h+ 긴급 top5 잔존' 0(신선창 전환 취지 — 운영자 3회 육안 포착 패턴의 기계화) · ≥1 = 곡선 무력화/타항 부양 의심 → §8 260717 재점검.
    try:
        import math
        def _ba(x):   # 발행 우선 나이(timeAcc 축·scTs 요지)
            v = age_h(x.get("published"), now)
            return v if v is not None else age_h(x.get("first_seen"), now)
        def _brk_ok(x):
            g = x.get("grade")
            return bool(x.get("breaking")) and (g is None or g >= 2)
        def _scr(x):   # 누적 scScore 근사(신곡선 부스트 포함)
            cr = x.get("cross") or 0
            rk = _iss_age(x) or 99
            ta = 1 / (1 + (max(_ba(x) or 99, 0) / 13) ** 3.0)
            fol = 1 + 0.5 * math.log2(1 + (x.get("report_count") or 0))
            g = x.get("grade")
            gw = 1.0 if g is None else {0: 0.5, 1: 0.7, 2: 1.0, 3: 1.8}.get(g, 1.0)
            bb = 1.0
            if _brk_ok(x) and rk < 6:
                if rk < 1:
                    bb = 3.0
                else:
                    s = lambda v: 1 / (1 + math.exp(-v))
                    t = (rk - 1) / 5
                    bb = 1 + 2 * (s(12 * (.5 - t)) - s(-6)) / (s(6) - s(-6))
            am = 0.12 + 0.88 / (1 + math.exp((rk - 13) / 3.8))
            return cr ** 1.3 * ta * fol * gw * bb * am
        cum = [x for x in c if (_ba(x) or 0) >= 4 and _cum_enter(x)]   # 진입 자격 = 단일 정본(260805)
        brks = [x for x in cum if _brk_ok(x)]
        fresh = [x for x in brks if (_iss_age(x) or 99) < 6]
        top5 = sorted(cum, key=_scr, reverse=True)[:5]
        linger = [x for x in top5 if _brk_ok(x) and (_iss_age(x) or 0) >= 12]
        f = "⚠️" if linger else "✅"
        print(f"  {f} 긴급부스트 신선창: 누적 breaking {len(brks)}건 · 부스트 수혜(<6h) {len(fresh)}건 · 12h+ top5 잔존(근사) {len(linger)}건"
              + ("  (←잔존 = 신곡선 무력화/타항 부양 의심 → §8 260717 재점검)" if linger
                 else "  (기준 잔존 0 · 260717 신선창 전환)"))
        for x in linger[:2]:
            print(f"      · {(_iss_age(x) or 0):.1f}h cr{x.get('cross')} rc{x.get('report_count')} {str(x.get('title') or '')[:36]}")
    except Exception as e:
        print(f"  · 부스트 계기판 계산 실패(비치명): {e}")
    # 독점률(도배 재발 감지 — 6/28형 '단일사건 상단 도배'를 숫자로 · ≥30%면 §7 접기(fold)안 검토 신호)
    try:
        dom = _dominance(c, now)
        if dom is None:
            print("  · 독점률: 누적자격 풀 <15 (심야 표본 부족) — 판정 유보")
        else:
            pct, size, title = dom
            flag = "⚠️" if pct >= 30 else "·"
            print(f"  {flag} 독점률(누적 상위30 최대 단일사건): {pct:.0f}%({size}건)"
                  + (f"  ← 도배 의심 · §7 접기안 검토 — {title[:28]}" if pct >= 30 else "  (기준 3~13% 정상 · 6/28형 도배 = 75%)"))
    except Exception as e:
        print(f"  · 독점률 계산 실패(비치명): {e}")
    # 묻힘 계측(외신·국제 · 260703 분신술 §7①): AI확정 대형(grade3)인데 4h+ 에서 누적 3경로(cross≥8/긴급/
    #  followEnters) 전부 미충족 = 두 칼럼 미노출. §1 "중요한 게 묻히면 안 됨" 유일 자동감시 — breaking 문체
    #  가드 등 개선의 before/after 토대(임계·자동조치 없음 = 순수 계측 · 정본 §8 260703). 나이 = 발행 우선·수집 폴백(_dominance 동일).
    try:
        buried, b2 = buried_counts(c, now, intl_only=True)
        print(f"  · 묻힘(외신·국제 4h+ 누적 미진입): grade3 {len(buried)}건 · grade2 {b2}건"
              + "  (기준 260703 g3=19 — 개선 효과·급증 감시용 게이지)")
        for x in buried[:3]:
            print(f"      ◦ {(x.get('title_ko') or x.get('title') or '')[:38]} (cr{x.get('cross') or 0}·rc{x.get('report_count') or 0})")
        # 전 카테고리 줄(260805 8인 평의회 통합관 발견) — 위 줄은 _intl(cat=='국제' or title_ko) 스코프라
        #   국내 사건이 **계측 자체의 사각**이었다. 실측 대조: 국제만 보면 grade2 15건인데 전 카테고리는 78건
        #   = 63건이 지금까지 안 세어졌고, 발단이 된 「평택 미군기지 무단침입」(cat='사회'·title_ko=None)이
        #   바로 그 사각에 살았다 = "§1 유일 자동감시"를 자처하면서 국내를 못 보던 축. 국제 줄은 260703
        #   기지값(g3=19) 연속성 때문에 유지하고, 전 카테고리를 아래 한 줄로 병기한다.
        ab, a2 = buried_counts(c, now, intl_only=False)
        print(f"  · 묻힘(전 카테고리 4h+ 누적 미진입): grade3 {len(ab)}건 · grade2 {a2}건"
              + "  (260805 기저 = g3 3·g2 78 · ⚠️ 병합 전 원자료 기준이라 과소계상[_cum_enter 근사2] — 이 숫자만 보고 진입선을 손대지 말 것 · 자동감시 = watchdog 30분)")
        for x in ab[:3]:
            print(f"      ◦ {(x.get('title') or '')[:38]} (cr{x.get('cross') or 0}·rc{x.get('report_count') or 0}·{x.get('cat') or '?'})")
    except Exception as e:
        print(f"  · 묻힘 계측 실패(비치명): {e}")
    print(f"  → 심층 비교: python3 scraper/compare_collected.py  (어제↔오늘 낮 승격·긴급 분포)")

    # ─────────── ③ 롤백 검토 ───────────
    print("\n③ 롤백 검토")
    print(f"  · 알고리즘 분기 라벨 = {CHECKPOINT} (검증완 기준점)")
    git("fetch", "origin", "main", "-q")
    log = git("log", "--oneline", "-15", "origin/main")
    kws = ("긴급", "수집함", "큐레이션", "breaking", "grade", "승격", "푸시", "candidates",
           "scrape", "rubric", "랭킹", "배지", "누적", "신규")
    hits = [ln for ln in log.splitlines() if any(k in ln for k in kws)]
    print(f"  · 최근 큐레이션 관련 커밋(origin/main, 최대 15 중):")
    for ln in hits[:8]:
        print(f"      {ln}")
    if not hits:
        print("      (최근 15커밋에 큐레이션 변경 없음)")
    print(f"  · 롤백 방법: git revert <커밋> 또는 git diff {CHECKPOINT}..origin/main 으로 분기 후 변경 검토")
    print(f"             · _versions/ 백업 폴더에서 개별 파일 복원")
    print("\n[판단] ①②에 ⚠️/❌ 있으면 원인 추적 → 알고리즘 변경 탓이면 ③으로 롤백 검토."
          " 깨끗하면 '수집·알고리즘 정상, 롤백 불요' 보고.")


if __name__ == "__main__":
    import sys as _sys
    if "--buried-alert" in _sys.argv[1:]:   # watchdog 30분 편승(무인 · 계측만 · 260805)
        raise SystemExit(buried_alert())
    main()
