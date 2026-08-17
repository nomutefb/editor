#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 유튜브 쿠키 생사 감시 — 「죽은 걸 운영자가 눌러봐야 아는」 축을 없앤다(운영자 260804 승인 "응 원장도 해주고").
#
# 왜: YT_T_COOKIES는 **수명이 유한하다**(유튜브가 열린 탭에서 쿠키를 수시 회전 · 실측 260804 = 03:14엔 인증
#   통과하던 쿠키가 06:36엔 사망). 그런데 죽어도 아무 신호가 없어서, 운영자가 유튜브를 받아보다 실패해야
#   비로소 알았다(= 필요한 순간에 못 쓴다). 정기로 재보고 죽으면 **미리** 알린다.
#
# 체인: watchdog 격 크론(yt-cookie-health.yml) → **이 스크립트** → ① whoami 실행(판정 정본 재사용 · 로직 복제 0)
#       → ② 원장 push/yt_cookie_health.json 누적 → ③ 연속 사망 시 shared/msg.py → 뷰어 알림메시지.
#
# 설계 원칙(전부 이 레포의 기존 사고에서 배운 것):
#  ① **판정 로직을 복제하지 않는다.** yt_cookie_whoami.py를 subprocess로 부르고 그 출력을 읽는다 —
#     두 벌이 되면 한쪽만 고쳐져 조용히 갈린다(brk_misfire → msg.py 호출 관례와 같은 축).
#  ② **알림 id는 회전한다**(`yt-cookie-dead-<연속회차>`). 고정 id면 뷰어 unread 판정이 id 축이라
#     메시지함을 **한 번 열면 영영 재점등이 안 된다**(brk_misfire 주석의 실측 교훈 그대로).
#  ③ **2회 연속부터 발화.** 1회성 네트워크 딸꾹질(홈 fetch 실패·일시 5xx)과 진짜 사망을 가른다
#     (insta 커버 결손 `none_streak` 2회 선례 동값). 12시간 주기 × 2 = 하루 안에 잡힌다.
#  ④ **살아나면 자동 해소**(clear + streak 0) — 사람이 알림을 지울 일이 없다.
#  ⑤ **fail-soft**: 어떤 예외도 rc=0. 감시기가 워크플로를 죽이면 원장이 못 쌓인다.
# 과금 0 — LLM 미사용. 원장 = 기계산출물(손편집 금지 · 값 변경 = 이 코드를 고쳐 재실행).
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent.parent.parent
WHOAMI = ROOT / ".github" / "scripts" / "yt_cookie_whoami.py"
LEDGER = ROOT / "push" / "yt_cookie_health.json"   # 원장(기계산출물)
MSG_PY = ROOT / "shared" / "msg.py"
MSG_ID_BASE = "yt-cookie-dead"
DEAD_MIN = 2      # 이 횟수 연속 사망부터 발화(1회성 딸꾹질 제외)
ACCT_DOUBT = 5    # 이 횟수 연속 사망부터 「계정 축 의심」 안내 동반(재발급을 이미 해봤을 회차 = 자동 검사 하루 2회 × 2.5일)

# 조치문 규약(👉 문단 · scraper/watchdog.py `PHONE_TODO` 문법 100% 계승 · 창작 0) — 알림 리포트의 조치주체
#   분류(viewer/index.html `_rptWho`)는 **👉 문단이 있어야** '운영자가 할 일'로 가른다. 없으면 폴백이 '클로드가
#   볼 일'이라, 코드로는 한 글자도 못 고치는 이 건(= GitHub Secrets 교체)이 클로드 칸에 앉는다.
#   ⚠ 260808 실측 = 리포트 3건이 전부 '클로드 3 · 운영자 0'인데 실제 코드 축은 1건뿐이었다. 같은 병이 260728에
#     이미 진단돼 `wd-phone` 한 종만 고쳐졌고(watchdog.py 188행 주석), 이 생산자는 그때 안 따라왔다.
# ⚠ 갈 칸 이름은 **틀({kan})로 비워두고** 죽었다고 판정된 칸을 그 자리에 끼운다 — 여기에 손으로 적었더니
#   배선과 반대 칸을 지시했다(260812 실사고 · kan() 주석 참조). 이름은 워크플로가 알려준 값만 쓴다.
# ⚠⚠ 조치문은 **사유 축으로 갈라 쓴다**(260817 실사고 봉합 · 운영자 «오탐인지 진짠지 확인해줘»).
#   구판은 이 한 벌이 사유 4종(①②③④) 어느 것이든 「유튜브가 쿠키를 무효 처리한 상태라」고 **고정으로** 말했다.
#   260816~17 실사고의 사유는 `② 파싱: 실패`(= 그 칸에 든 글이 쿠키 파일 모양이 아님 · 값은 비어 있지 않다)라
#   그 문장이 **거짓**이었고, 운영자를 「유튜브·계정이 막았다」는 엉뚱한 축으로 보냈다 — 실제 조치는
#   「같은 쿠키를 파일 모양 그대로 다시 붙여넣기」인데 처방은 「유튜브가 막았으니 어쩔 수 없다」로 읽힌다.
#   = CLAUDE.md 「실패 사유가 화면까지 온다」와 같은 축(사유는 정직 표기됐는데 **처방이 거짓말을 했다**).
#   술어 = why 안의 `② 파싱:` 유무 — probe() 가 이미 그 문자열로 사망을 판정한다(사전·정규식 사본 0).
# ⚠ 두 벌 다 `👉` 문단을 유지한다 — 없으면 조치주체가 '클로드가 볼 일'로 폴백한다(위 규약).
COOKIE_TODO = ("\n\n👉 네가 할 일: 위 3동작으로 쿠키를 새로 뽑아 GitHub Secrets 의 {kan} 를 갈아 줘. "
               "코드로는 못 고치는 축이야(유튜브가 쿠키를 무효 처리한 상태라 재시도·폴백이 다 같은 벽에 막혀).")
COOKIE_TODO_FMT = ("\n\n👉 네가 할 일: GitHub Secrets 의 {kan} 를 다시 채워 줘 — 지금 든 값이 "
                   "쿠키 파일 모양이 아니야(값이 비어 있는 건 아니고, 첫 줄에 있어야 하는 "
                   "「Netscape HTTP Cookie File」 머리글이 없어서 읽는 쪽이 파일로 인정하지 않아). "
                   # ⚠ 별표 강조를 쓰지 않는다 — 알림 본문은 순수 텍스트로 렌더돼서 `**` 가 화면에 그대로 뜬다
                   #   (실측 260817 = 전/후 캡처에서 확인). 강조는 「」 괄호로만(같은 파일 관용구).
                   "확장이 내려준 .txt 를 편집기로 열어 첫 줄부터 끝까지 통째로 복사해 붙여야 해"
                   "(표 복사·JSON 내보내기·일부 줄만 붙이기는 이 형식이 아니야). "
                   "이번 건은 유튜브·계정 축과 무관해 — 우리 쪽은 그 칸에 든 글을 그대로 읽을 뿐이라 "
                   "코드로는 못 고쳐.")
KEEP = 90         # 원장 보존 회차(12시간 주기 = 약 45일)


def msg(*args):
    subprocess.run([sys.executable, str(MSG_PY)] + list(args), check=False)


# 계정 슬롯 — ⚠ 260817 예비 슬롯 폐지(운영자 「예비칸 안쓰게 배선 다시」) = **1칸 운영**.
#   구판(260810 "구글 계정 2개로 돌리게 하자 하나가 죽는거일수도있으니까")은 ("2","YT_COOKIES_2") 를 같이 들고
#   「살아있는 슬롯이 하나라도 있으면 사망 아님」으로 판정했다 — 그 축이 실제로 한 일 = 260812~13에 1번이 죽은
#   동안 예비가 받기를 살렸고, 계정 이관에서 예비가 안 따라오자 그 완충이 사라져 전면 정지했다.
#   운영자 판단 = 두 칸을 굴리는 대신 한 칸을 제대로 유지한다. 되살리기 = 이 목록에 슬롯 1줄 추가
#   + 워크플로에 `YT_COOKIES_2`·`YT_COOKIES_2_NAME` 2줄 복원(그 외 로직은 슬롯 수에 무관하게 돈다).
SLOTS = [("1", "YT_COOKIES")]


def kan(var):
    """운영자가 실제로 여는 **저장소 칸 이름**(워크플로가 <슬롯>_NAME 으로 알려준다).

    ⚠ 260812 실사고 봉합 — 이 함수가 없던 판은 알림 본문에 칸 이름을 **손으로 적어** 두 곳이 갈렸다:
      워크플로 배선은 `YT_COOKIES(1번) ← YT_T2_COOKIES` / `YT_COOKIES_2(2번) ← YT_T_COOKIES` 인데,
      알림 문구는 `1번→YT_T_COOKIES · 2번→YT_T2_COOKIES` 라 **정확히 반대**를 지시했다. 실측(260812 11:24)
      = 건강검진 알림은 「2번 죽음 → YT_T2_COOKIES 를 갈아라」인데, 같은 시각 받기 레일 진단은
      「YT_T2_COOKIES = 살아있음 · YT_T_COOKIES = 죽음」 — 두 시스템이 같은 상태를 정반대로 말했다.
      결과 = 운영자가 **살아있는 칸을 갈고** 죽은 칸은 그대로 둬서 경고가 영영 안 꺼진다.
    → 이름을 코드에 적지 않고 **워크플로가 준 값을 그대로 쓴다**(= 갈릴 여지가 구조적으로 소멸).
      문법 정본 = `.github/scripts/ytdlp_try.sh` 의 `<슬롯>_NAME`(운영자 260812 «대명사 쓰지 말고 명시»).
      ⚠ 같은 지시가 그때 받기 레일 8종에만 적용되고 이 감시기는 안 따라왔다 = 「같은 병의 형제를 놓친」 축.
    """
    return (os.environ.get(f"{var}_NAME") or "").strip() or var


def probe(var="YT_COOKIES"):
    """whoami 1회 실행 → (ok, why, acct). 판정 정본은 whoami 쪽 단독(여기선 읽기만)."""
    try:
        r = subprocess.run([sys.executable, str(WHOAMI)], capture_output=True, text=True,
                           timeout=180, env=dict(os.environ, REVEAL="", YT_CK_VAR=var))
    except Exception as e:
        return None, f"감시기 실행 실패({type(e).__name__})", ""   # None = 판정 불가(연속 카운터 건드리지 않음)
    out = (r.stdout or "") + (r.stderr or "")
    acct = ""
    m = re.search(r"⑤ 계정: 채널명=(\S+) · 핸들=(\S+)", out)
    if m:
        # ⚠ whoami는 못 찾은 자리를 「(없음)」으로 찍는다 — 그대로 실으면 알림에 「· 계정 (없음)」이라는
        #   거짓 문구가 뜬다(실측 260812 원장 acct="(없음)" = 핸들 파싱만 실패한 회차). 채널명으로 대체.
        acct = next((g for g in (m.group(2), m.group(1)) if g != "(없음)"), "")
    if r.returncode == 0:
        return True, "", acct
    # 실패 사유 = whoami가 이미 사람 말로 찍는다 → 첫 ::error:: 줄을 그대로 계승(문구 재창작 0)
    e = re.search(r"::error::(.+)", out)
    why = (e.group(1) if e else "쿠키 점검 실패").strip()
    # 사망 확정 = 쿠키 **자체**가 원인인 판정 4종(whoami의 ①②③④ bail 지점 그대로).
    #   ⚠ ①②를 뺐다가 로컬 시험에서 「시크릿 비어있음」이 '판정 불가'로 새는 걸 잡았다 —
    #     시크릿 공백·형식 깨짐은 네트워크 딸꾹질이 아니라 **가장 확실한 사망**이라 반드시 세야 한다.
    #   ⚠ 판정은 **why(= 그 실행이 실제로 멈춘 ::error:: 한 줄)만** 본다. out 전체를 보면 성공 구간의
    #     「① 시크릿: 있음」까지 걸려, ⑤ 파싱 실패(rc=2 = 진짜 '판정 불가')가 사망으로 오분류된다.
    for sig in ("① 시크릿:", "② 파싱:", "③ 진단:", "④ LOGGED_IN: false", "로그인 상태가 아님"):
        if sig in why:
            return False, why, acct
    return None, why, acct   # 그 밖(홈 fetch 실패·응답 구조 변경)만 '판정 불가' = 사망으로 안 센다(오경보 차단)


def load():
    try:
        d = json.loads(LEDGER.read_text(encoding="utf-8"))
        if isinstance(d, dict) and isinstance(d.get("runs"), list):
            return d
    except Exception:
        pass
    return {"_meta": {"dead_streak": 0, "alert_id": "", "last_ok": "", "last_run": ""}, "runs": []}


def main():
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    # 슬롯별 판정 — 1번은 항상 잰다(비어 있어도 사망) · 2번은 값이 있을 때만(미설정 = 1계정 운영 = 정상)
    # ⚠ 키 = 슬롯 번호가 아니라 **저장소 칸 이름**(kan) — 알림이 「2번」 같은 대명사로 말하면 운영자가
    #   어느 칸을 갈지 알 수 없고, 번호↔이름 대응을 손으로 적는 순간 갈린다(위 kan() 주석의 260812 실사고).
    slots = [(kan(v), v) for t, v in SLOTS if t == "1" or os.environ.get(v, "").strip()]
    res = {t: probe(v) for t, v in slots}
    alive = [t for t, (o, _, _) in res.items() if o is True]
    dead = [t for t, (o, _, _) in res.items() if o is False]
    # 하나라도 살아 있으면 받기는 된다 = 사망 아님. 전부 죽어야 사망. 그 밖(판정 불가 섞임) = 카운터 유지.
    ok = True if alive else (False if dead else None)
    why = " / ".join(f"{t}: {res[t][1]}" for t in dead) or next(iter(res.values()), (None, "", ""))[1]
    acct = next((res[t][2] for t in alive or list(res) if res[t][2]), "")
    slotmap = {t: ("살아있음" if res[t][0] is True else "죽음" if res[t][0] is False else "판정불가")
               for t in res}
    led = load()
    meta = led.setdefault("_meta", {})
    meta["slots"] = slotmap
    led["runs"].append({"t": now, "ok": ok, "why": why[:200], "acct": acct, "slots": slotmap})
    led["runs"] = led["runs"][-KEEP:]
    meta["last_run"] = now

    if ok is True:
        meta["dead_streak"] = 0
        meta["last_ok"] = now
        if acct:
            meta["acct"] = acct
        if meta.get("alert_id"):
            msg("clear", meta["alert_id"])   # 살아나면 자동 해소(사람이 지울 일 0)
            meta["alert_id"] = ""
        # ⚠ 「한쪽만 죽음」 반쪽 경고 = 260817 예비 슬롯 폐지와 함께 제거(복원 = git 역사).
        #   1칸 운영에서는 이 자리가 **도달 불가**다 — 슬롯이 하나뿐이면 살아있음과 죽음이 동시에 성립할 수 없다.
        #   ⚠ 다만 원장에 지난 회차의 half_id 가 남아 있을 수 있어 **한 번은 걷어 준다**(안 걷으면 그 알림이
        #     화면에 영구 잔류한다 = 폐지가 만드는 유령 · 없는 id 를 clear 하는 건 무해 = msg.py no-op).
        if meta.get("half_id"):
            msg("clear", meta["half_id"])
            meta["half_id"] = ""
        print(f"[쿠키] 정상 · 계정={acct or '(미표기)'} · 연속사망 0 · 슬롯 {slotmap}")
    elif ok is False:
        meta["dead_streak"] = int(meta.get("dead_streak") or 0) + 1
        n = meta["dead_streak"]
        print(f"[쿠키] 사망 · 연속 {n}회 · {why[:80]}")
        if n >= DEAD_MIN:
            mid = f"{MSG_ID_BASE}-{n}"   # 건수 접미 회전(고정 id = 한 번 열면 영구 실명 · brk_misfire 교훈)
            prev = meta.get("alert_id")
            if prev and prev != mid:
                msg("clear", prev)
            body = (f"유튜브 받기용 쿠키가 죽었어요(연속 {n}회 · 마지막 정상 {meta.get('last_ok') or '기록 없음'}"
                    + (f" · 계정 {meta.get('acct')}" if meta.get("acct") else "") + ").\n"
                    f"사유: {why[:120]}\n"
                    # ⚠ 칸 상태는 **항상** 쓴다(구판은 `len(slotmap) > 1` 조건이라 1칸 운영에서 통째로 안 보였다 —
                    #   260817 예비 슬롯 폐지로 1칸이 상시가 됐으니 그 조건이 곧 영구 침묵이 된다).
                    #   어느 칸을 갈지는 아래 처방문이 말하지만, 「지금 이 칸이 죽었다」를 상태로 한 줄 못박아 둔다.
                    + ("칸 상태: " + " · ".join(f"{t} {s}" for t, s in slotmap.items())
                       + ("(예비 칸 없이 이 칸 하나로 도니까 유튜브 받기가 멈춰요)" if len(slotmap) == 1
                          else "(전부 죽어서 유튜브 받기가 멈춰요)") + "\n")
                    # ⚠ 이 두 줄이 없으면 「방금 갈았는데 왜 또 뜨지」가 된다(운영자 260810 실측 — 자동 검사가
                    #    하루 2회뿐이라 교체 직후 최대 12시간 동안 옛 판정이 화면에 그대로 남는다).
                    + f"이 판정을 낸 검사 시각 = {now} · 자동 검사는 하루 2회(09시·21시 KST)뿐이에요.\n"
                    "⚠ 그 시각 뒤에 쿠키를 갈았다면 이 경고는 아직 옛 검사 결과예요 — 다음 검사까지 그대로 남아 있어요. "
                    "지금 바로 확인하려면 아래 «확인» 경로로 한 번 돌리면 돼요(1분).\n"
                    "고치는 법(3동작): ① 시크릿 창에서 유튜브 로그인 → ② 주소창에 youtube.com/robots.txt 이동 후 "
                    "쿠키 내보내기(Get cookies.txt LOCALLY) → 창 닫기 → ③ GitHub Settings ▸ Secrets ▸ Actions 의 "
                    # ⚠ 갈 칸은 **죽었다고 판정된 칸 그대로** 적는다(손으로 적은 이름이 배선과 반대였던 260812 실사고 봉합).
                    f"{'·'.join(dead) or kan('YT_COOKIES')} 교체(youtube.com 줄만 · 48KB 상한).\n"
                    "확인: Actions ▸ yt-cookie-whoami ▸ Run workflow → 「④ LOGGED_IN: true」면 복구. "
                    "⚠ 로그인 창을 열어둔 채 내보내면 쿠키가 회전해 몇 시간 만에 또 죽어요(260804 실측)."
                    # ⚠ 260810 실측 봉합 = 새로 뽑아 넣은 쿠키가 형식은 완벽한데(로그인 쿠키 10/10 · 만료 2027-01-24)
                    #    유튜브가 세션을 거부했다. 이 상태에서 「뽑는 절차를 다시 하라」만 반복하면 운영자가
                    #    같은 동작을 무한히 되풀이한다 — 회차가 쌓이면 계정 축을 같이 의심하게 알린다.
                    + ("\n⚠ 새로 갈았는데도 계속 죽는다면 뽑는 절차가 아니라 **그 계정 쪽**일 수 있어요"
                       "(유튜브가 그 계정 세션을 봇으로 보고 막는 상태 — 쿠키 형식이 멀쩡해도 거부돼요). "
                       "다른 구글 계정으로 한 번 뽑아 넣어 보면 어느 쪽인지 갈려요." if n >= ACCT_DOUBT else "")
                    # 조치문 = 사유 축으로 갈라 쓴다(위 COOKIE_TODO_FMT 주석의 260817 실사고 봉합).
                    + (COOKIE_TODO_FMT if "② 파싱:" in why else COOKIE_TODO)
                    .format(kan='·'.join(dead) or kan("YT_COOKIES")))
            msg("set", mid, body, "warn")
            meta["alert_id"] = mid
    else:
        print(f"[쿠키] 판정 불가(연속 카운터 유지) · {why[:80]}")   # 네트워크 딸꾹질 = 사망으로 안 센다

    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    tmp = LEDGER.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, LEDGER)   # 원자적 교체(부분 기록 차단 · vidl_run result.json 관례)
    print(f"원장: {LEDGER.relative_to(ROOT)} · 회차 {len(led['runs'])}건")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:   # fail-soft — 감시기가 워크플로를 죽이면 원장이 못 쌓인다
        print(f"::warning::쿠키 감시 실패(비치명): {type(e).__name__} {str(e)[:120]}")
        sys.exit(0)
