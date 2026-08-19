#!/usr/bin/env python3
"""폰(termux)/맥 구독 수집 — X·인스타·스레드·틱톡(가정 IP = 러너 429 로터리·Meta 데센 차단·tikwm WAF 403 우회 · 운영자 260712 "ㄱ"·"맥에서 크롬 통해 접근 가능").
- 기존 기사 공유 경로(termux-share·queue-handler·pending/)와 완전 분리: 이 스크립트는
  viewer/sns_subs_phone.json 한 파일만 산출(기존 파이프 파일 무접촉 = 충돌 0).
- 수집 로직 = scraper/sns_trends.py의 x_subs/insta_subs/threads_subs/_load_accounts 재사용(stdlib만 · 추가 패키지 0).
- 소비 = sns_trends.py main()이 이 파일이 신선(기본 90분)하면 x·insta·threads 축만 채택(스테일 = 러너분).
- 스레드는 러너(데이터센터 IP) 수집이 불가(Meta 차단)라 이 경로가 유일 공급원 — 맥도 가정 IP면 동일 자격.
- 실행 = scripts/phone_subs.sh(크론 진입점)가 감쌈. 단독 실행도 가능: 레포 루트에서 python3 scripts/phone_subs.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scraper"))
import sns_trends as st  # noqa: E402

# ── 인스타 429 지수 백오프(운영자 260727) ─────────────────────────────────────────
# 판례: 쿠키 주입 성공(길이 266·401 아님) 후에도 **첫 계정부터 429가 8연속**. 인스타 IP 리밋은
#   두드릴 때마다 **갱신**되므로 30분 크론이 계속 때리면 영영 안 풀리는 자해 루프였다(로그 실측).
#   → 429를 맞으면 그 시각부터 일정 시간 인스타 호출 자체를 건너뛴다 = IP에 회복할 틈을 준다.
#   연속 실패마다 6h → 12h → 24h(상한)로 늘리고, 한 번 성공하면 카운터를 지워 즉시 정상 주기 복귀.
# ── 요청량 축소(운영자 260727 "인스타 주기를 1시간 30분 해도됨") ──────────────────────
# 진단 갱신: **LTE로 IP를 바꿔도 429** = IP축이 아니라 **계정·세션 단위 리밋**. 원인은 요청량 —
#   30분 × 20계정 = 하루 약 960회. 사람이 남의 프로필을 하루 960번 열 리 없으니 자동화로 찍힌다.
#   ⓐ 주기 90분(운영자 승인) + ⓑ 한 런에 5계정씩 **회전** → 하루 약 80회(-92%) · 20계정 한 바퀴 = 6시간.
# ⚠ 회전은 **누적 병합이 없으면 데이터를 오히려 줄인다**(매 런 5건만 남고 나머지 15계정분 증발) →
#   직전 산출물에서 이번 배치 계정분만 걷어내고 새로 붙인다. 뷰어의 3일 컷(cut3d)이 낡은 건 알아서 거른다.
# 상태 = 폰 로컬 JSON(git 밖 · {until,cnt,last,off}) · 삭제 = 전체 초기화(즉시 재시도). 구 "until count"
#   평문 형식도 읽어 계승(마이그레이션 무중단). 인스타 축에만 적용 — 다른 소스는 종전대로 매 런.
_CD_PATH = os.path.expanduser("~/.nomute_insta_cooldown")
_CD_STEPS = (6 * 3600, 12 * 3600, 24 * 3600)
# ── 무소득 장기화 승격(운영자 260730 "원론적으로 해결해서 다음에 안뜨게") ────────────────
# 위 백오프·회전은 **일시적** 리밋을 전제한다. 전제가 깨지면(쿠키 만료·계정 제재 = 두드려도 영원히 429)
#   cnt는 성공해야 리셋되니 24h 상한에 상주하고, 뷰어는 사유가 'cooldown'/'gap'인 동안 계속
#   "네가 할 일: 없어요 · 자동으로 걷혀요"만 출력한다 = **날마다 같은 알림이 뜨는데 아무도 안 고치는 무한 대기**.
#   그 문구 자체가 "이틀 넘게 계속 뜨면 그때 알려줘"라고 약속하는데 **이틀을 재는 코드가 없었다**(260730 실측: insta 0/20).
#   → 마지막 수확 시각(okat)을 상태에 남기고 임계를 넘으면 사유를 'stuck'으로 승격 = 뷰어가 운영자 조치로 갈라 읽는다.
#   [관측] 조항 = fail-soft는 실패를 감추는 장치가 아니다 → 스킵 런도 집계 1줄을 남기고 임계 이탈은 ::warning::.
_STUCK_DFLT_H = 48   # 임계 = 뷰어 'wait' 문구가 약속한 "이틀"과 같은 값(두 축이 어긋나면 약속과 동작이 갈린다)
def _envf(name, dflt):
    """env 숫자 파싱 — 오타 하나로 모듈 임포트가 죽던 자리(260730 검증 A-D8). 스크립트가 죽으면
    phone_subs.sh의 `|| exit 0`가 무음 종료시켜 x·스레드·틱톡·레딧·재난까지 **전 축이 같이 굶는다**
    (sns_trends.py:1822가 `_i(env) or 240`으로 이미 막아 둔 함정과 동형) → 폴백 = 기본값."""
    try:
        return float(str(os.environ.get(name) or dflt).strip())
    except Exception:  # noqa: BLE001
        print(f"::warning::{name} 값이 숫자가 아님 — 기본값 {dflt} 사용", file=sys.stderr)
        return float(dflt)

_GAP = _envf("INSTA_MIN_GAP_MIN", 60) * 60   # 최소 간격(분) — 60분(운영자 260819 «인스타랑 x 둘다 1시간 단위로 통일» · 구 90분[260727]에서 하향 = 엑스와 한 값 · 크론 30분이라 2런 중 1런만 실제 수집)
_BATCH = int(_envf("INSTA_BATCH", 5))       # 한 런에 도는 계정 수(0 이하 = 회전 끔 = 전량)
_STUCK = _envf("INSTA_STUCK_H", _STUCK_DFLT_H) * 3600   # 무소득 연속 임계(0 이하 = 승격 끔)

# ── 엑스 주기 게이트(운영자 260819 «인스타랑 x 둘다 1시간 단위로 통일하고 60분, 계정간 순회 간격은 30초») ──
# ⚠ 실측 배경 = 엑스만 **30분마다 6계정 전부**를 4초 간격으로 몰아 두드렸다(하루 288회). 인스타는 이미
#   90분·5계정 회전으로 하루 80회까지 줄여놨는데 엑스만 구판 그대로였고, 그 결과 회차마다 「되고 안 되고」가
#   갈렸다(260819 실측 = 새벽 내내 0건 → 10:01 회차에 갑자기 19건 · 두 번째 계정부터 429 확인).
#   → **두 축 모두 60분·계정간 30초**로 통일한다(운영자 재지정 260819 — 계정 간 간격을 넓히면 회차 주기를
#   90분까지 벌릴 이유가 없다는 판단. 인스타 구 90분도 이 값으로 같이 내린다 = 갱신이 오히려 빨라진다).
# ⚠ 회전(계정 나눠 돌기)은 **안 넣는다** — 운영자 지시는 주기·간격 두 축이고, 회전은 이월 병합까지 딸린
#   별건이다(인스타 주석 27행이 경고한 「병합 없는 회전 = 데이터가 오히려 준다」 축).
_X_GAP = _envf("X_MIN_GAP_MIN", 60) * 60      # 엑스 최소 간격 = 인스타와 **같은 60분**(운영자 260819 «인스타랑 x 둘다 1시간 단위로 통일»)
_X_SLEEP = _envf("X_ACCOUNT_SLEEP_S", 30)     # 계정 간 간격 = 30초(운영자 «계정간 순회 간격은 30초 단위» · 6계정 = 한 회차 30초×5 + 응답시간 ≈ 3분)
_X_ST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "push", "x_subs_state.json")


def _x_due():
    """엑스 수집 차례인가 — 마지막 수집 시각이 _X_GAP 이전이면 참(파일 부재·파손 = 참 = fail-open)."""
    if _X_GAP <= 0:
        return True
    try:
        return (time.time() - float((json.load(open(_X_ST, encoding="utf-8")) or {}).get("last") or 0)) >= _X_GAP
    except Exception:  # noqa: BLE001
        return True


def _x_stamp():
    """수집 시각 도장 — 원자 교체(인스타 _st_write 계약 계승 = 잘린 JSON이 회전을 무력화하던 사고 축)."""
    try:
        os.makedirs(os.path.dirname(_X_ST), exist_ok=True)
        t = _X_ST + ".tmp"
        with open(t, "w", encoding="utf-8") as f:
            json.dump({"last": time.time()}, f)
        os.replace(t, _X_ST)
    except Exception as e:  # noqa: BLE001 — 도장 실패가 수집을 못 죽인다(다음 런 재시도)
        print(f"::warning::x 주기 도장 실패(무시): {e}", file=sys.stderr)


def _x_collect(accounts, prev_items):
    """주기를 통과한 회차만 실제로 걷고, 아니면 **직전 산출물을 그대로 이월**한다(인스타 병합 계약과 같은 축).
    ⚠ 이월이 없으면 스킵 회차마다 엑스가 0건으로 굳어 화면에서 통째로 사라진다."""
    accounts = list(accounts or [])
    if not accounts:
        return []
    if not _x_due():
        print(f"x 계측: 미시도(주기 {int(_X_GAP / 60)}분) · 이월 {len(prev_items or [])}건")
        return list(prev_items or [])
    got = st.x_subs(accounts, limit=20, sleep_s=_X_SLEEP)
    _x_stamp()
    print(f"x 계측: 수확 {len(got)}건 · 등록 {len(accounts)}계정 · 계정간 {int(_X_SLEEP)}s")
    return got if got else list(prev_items or [])   # 빈 수확 = 차단 국면 → 직전분 보존(fail-soft)


def _st_read():
    """{until, cnt, last, off, okat, since} — JSON 우선, 구 평문("until cnt")도 계승. 파손·부재 = 전부 0(fail-open).
    okat = 마지막으로 **1건이라도 걷은** 시각(**0 = 한 번도 없음** · 260801부터 이 자리에 관측 0점을 넣지 않는다).
    since = 관측 시작점(fail-open 유예 기준) — 승격 시계 = `okat or since`.
    ⚠ 미래값 클램프(260730 검증 A-D3) — 폰 시계 점프·NTP 보정으로 until/last가 미래에 박히면 게이트를
    영원히 못 통과하고(해제 조건 = 성공, 성공 조건 = 게이트 통과 = 자기잠금) 뷰어엔 "자동으로 걷혀요"만
    영구 출력되는 **침묵 사망**이 된다 → 상한(최장 쿨다운) 넘는 값·미래 last = 파손과 동급 fail-open."""
    try:
        raw = open(_CD_PATH, encoding="utf-8").read().strip()
        if raw.startswith("{"):
            d = json.loads(raw)
            u, c, l, o = float(d.get("until") or 0), int(d.get("cnt") or 0), float(d.get("last") or 0), int(d.get("off") or 0)
            k, s = float(d.get("okat") or 0), float(d.get("since") or 0)
        else:
            a, b = raw.split()
            u, c, l, o, k, s = float(a), int(b), 0.0, 0, 0.0, 0.0
        now = time.time()
        if u - now > max(_CD_STEPS):
            print("::warning::insta 쿨다운 시각이 상한 초과(시계 점프 추정) — 무시하고 재시도", file=sys.stderr)
            u = 0.0
        if l > now:
            l = 0.0
        if k > now:   # 미래 okat = 무소득 시계가 영원히 안 차는 침묵(위 last 클램프와 동형 함정)
            k = 0.0
        if s > now:
            s = 0.0
        return u, c, l, o, k, s
    except Exception:  # noqa: BLE001
        return 0.0, 0, 0.0, 0, 0.0, 0.0


def _st_write(until, cnt, last, off, okat=0.0, since=0.0):
    """원자적 기록(260730 검증 A-D4) — 종전 직접 open("w")은 도즈·강제종료가 그 순간에 걸리면 잘린 JSON을
    남겼고, _st_read가 그걸 fail-open으로 0 처리해 **off가 0으로 리셋** = 계정 0~4만 계속 돌고 5~19는
    영영 안 도는 starvation(회전 자체는 건전한데 상태 유실로 무력화) → tmp+os.replace로 원자 교체."""
    try:
        tmp = _CD_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"until": until, "cnt": cnt, "last": last, "off": off, "okat": okat, "since": since}, f)
        os.replace(tmp, _CD_PATH)
    except Exception as e:  # noqa: BLE001 — 기록 실패 = 다음 런 재시도(종전 동작)
        print(f"::warning::insta 상태 기록 실패({type(e).__name__}) — 다음 런 재시도", file=sys.stderr)


def _skip_stamp(accounts, tag):
    """인스타를 **안 돈 런**의 사유 도장(260730 판례 봉합) — 종전엔 쿨다운·주기 대기로 스킵하면
    SUB_FAIL/SUB_OK에 insta 키가 통째로 안 실려, sns_trends main()의
    `_fsrc = {**SUB_FAIL, **PHONE_COVER.why}`가 **러너(데센 IP)의 429/budget 잔향**으로 채워졌다
    = 데이터는 폰인데 사유는 러너인 주체 뒤바뀜(260728 봉합의 스킵 경로 재발). 화면엔 폰이 쿠키 때문에
    막힌 것처럼 보여 운영자에게 '쿠키 갈아라'는 헛 조치를 시킨다. 폰이 스스로 '안 돌았다'고 찍어
    러너 기록을 덮는다 = 뷰어가 대기 상태로 갈라 읽는다(값 = 'cooldown' 쿨다운 · 'gap' 주기 대기)."""
    for a in accounts:
        st._sfail("insta", a, tag)


_CUT3D = 3 * 86400   # 이월 나이 컷 = 뷰어 cut3d(viewer/index.html)와 같은 창 — 두 축이 어긋나면 화면엔 없는데 커버는 성공으로 세는 은폐가 생긴다


def _merge(prev_items, got, done):
    """이번 회차 수집분(got) + 직전 산출물 이월(kept) 병합. done = 이번에 갱신된 계정(중복 제거 축).
    ⚠ 나이 컷(260730 검증 A-D9) — 종전 이월엔 필터가 없어 목록에서 지운 계정·영구 고장 계정의 옛 항목이
    무기한 잔존했고, main()의 got 산식이 **나이 무관하게 항목 등장 계정을 성공으로 계산**해(sns_trends.py L1977)
    8개월 된 시체 1건이 그 계정을 miss·why에서 영영 빼는 조용한 은폐를 만들었다. 뷰어 3일 컷과 같은 창으로 자른다."""
    cut = time.time() - _CUT3D
    kept = [it for it in (prev_items or [])
            if (it.get("account") or "").lower().lstrip("@") not in done and (it.get("time") or 0) >= cut]
    return kept + list(got or [])


def _metric(accounts, got, out, okat, now, note):
    """[관측] 인스타 레인 집계 1줄 — **스킵 런에도 반드시 찍는다**. 종전엔 실제 수집 런만 찍어
    쿨돈·주기 대기로 안 돈 런은 로그에 '아무 일 없음'으로 남았다 = "시도했는데 무소득"과 "아예 미시도"가
    구분되지 않는 조용한 0(레포 관례 = trend_images "N개 백필"·sns_tr "번역 N건")."""
    dry = (now - okat) / 3600 if okat else 0.0
    print("insta 계측: 수확 %d건 · 등록 %d계정 · 이월잔여 %d건 · 무소득 %.1fh(임계 %.0fh) · %s"
          % (len(got or ()), len(accounts), max(0, len(out or ()) - len(got or ())), dry, _STUCK / 3600, note))


def _insta_collect(accounts, prev_items):
    """쿨다운·주기·회전을 통과한 배치만 수집하고, 직전 산출물과 병합해 돌려준다."""
    until, cnt, last, off, okat, since = _st_read()
    now = time.time()
    accounts = list(accounts or [])
    if not accounts:
        return prev_items
    # 최초 관측 = 측정 구간이 없는 것 → '고장'으로 단정하지 않고 이번 런을 시계 0점으로 잡는다(fail-open 유예).
    # ⚠ 0점은 **since**에 적는다(260801 판례) — 종전엔 이 자리에서 okat(=마지막 수확)에 now를 박아,
    #   한 번도 못 걷은 상태가 "방금 걷은 것"으로 위장됐다. 그래서 ① 48h 승격이 영원히 안 차고
    #   ② 진단이 "마지막 수확 37.5시간 전"이라 거짓 보고해, 엔드포인트가 죽은 걸 **일주일간 아무도 못 봤다**.
    #   okat = 진짜 수확만(0 = 한 번도 없음) · since = 관측 시작점. 승격 시계는 둘 중 있는 쪽으로 잰다.
    if not since:
        since = now
        _st_write(until, cnt, last, off, okat, since)
    stuck = _STUCK > 0 and (now - (okat or since)) > _STUCK
    def _tag(base):
        """무소득이 임계를 넘으면 대기 사유를 'stuck'으로 승격 — 뷰어 sysErrMsgs가 대기(무조치)와
        승격(운영자 조치)을 이 코드 하나로 가른다. 승격해도 백오프 동작 자체는 종전 그대로(회복 시도는 계속)."""
        return "stuck" if stuck else base
    if now < until:
        print("::notice::insta 429 쿨다운 중 — %.1fh 남음(연속 %d회 · 두드릴수록 리밋이 갱신돼 회복이 늦어진다)"
              % ((until - now) / 3600, cnt), file=sys.stderr)
        if stuck:
            print("::warning::insta 무소득 %.1fh(임계 %.0fh 초과) — 자동 백오프로 회복되지 않는 상태 = 세션쿠키·계정 축 점검 필요"
                  % ((now - (okat or since)) / 3600, _STUCK / 3600), file=sys.stderr)
        _skip_stamp(accounts, _tag("cooldown"))
        _metric(accounts, [], prev_items, okat or since, now, "미시도(쿨다운 %.1fh 남음)" % ((until - now) / 3600))
        return prev_items
    if last and (now - last) < _GAP:
        print("::notice::insta 주기 대기 — %.0f분 남음(최소 간격 %.0f분 · 계정 리밋 회피)"
              % ((_GAP - (now - last)) / 60, _GAP / 60), file=sys.stderr)
        if stuck:
            print("::warning::insta 무소득 %.1fh(임계 %.0fh 초과) — 주기 대기 중이나 이전 시도들이 전부 무소득 = 세션쿠키·계정 축 점검 필요"
                  % ((now - (okat or since)) / 3600, _STUCK / 3600), file=sys.stderr)
        _skip_stamp(accounts, _tag("gap"))
        _metric(accounts, [], prev_items, okat or since, now, "미시도(주기 %.0f분 남음)" % ((_GAP - (now - last)) / 60))
        return prev_items
    batch = accounts if _BATCH <= 0 else [accounts[(off + i) % len(accounts)] for i in range(min(_BATCH, len(accounts)))]
    st.INSTA_429 = False
    got = st.insta_subs(batch, limit=20)
    done = {a.lower().lstrip("@") for a in batch}
    _skip_stamp([a for a in accounts if a.lower().lstrip("@") not in done], "rotate")   # 배치 밖 = 미시도(성공·429 양 경로 공통 · 260730 검증 A-D2: 429 경로에 도장이 없어 러너 잔향이 15계정을 다시 오염시켰다)
    if getattr(st, "INSTA_429", False):
        cnt = min(cnt + 1, len(_CD_STEPS))
        wait = _CD_STEPS[cnt - 1]
        # 회전은 실패해도 전진(260730 봉합) — 종전엔 off를 고정해 "다음에 같은 계정부터 재시도"였는데,
        #   첫 계정이 429 상주면 insta_subs가 잔여 배치를 _sbudget으로 통째 미시도 처리하므로 **성공이 영영 0**,
        #   cnt는 성공해야만 리셋되니 6→12→24h 상한에 박혀 자동 복구가 구조적으로 수렴하지 못했다(실측 260730 cnt=3).
        #   전진시키면 다음 깨어남에 **다른 5계정**을 두드린다 = 한 계정의 리밋이 20계정 전체를 인질로 잡지 못한다.
        if got:
            okat = now   # 429가 섞였어도 1건이라도 걷었으면 '무소득'이 아니다 = 승격 시계 리셋(승격은 진짜 전멸만)
        _st_write(now + wait, cnt, last, (off + len(batch)) % len(accounts), okat, since)
        print("::warning::insta 429 → %.0fh 쿨다운(연속 %d회 · 해제 = rm %s)" % (wait / 3600, cnt, _CD_PATH), file=sys.stderr)
        if stuck and not got:
            # 시도했는데 전멸 + 무소득 장기화 = 사유를 429가 아니라 'stuck'으로 덮는다. 429를 그대로 두면
            #   뷰어 _wait 판정이 그걸 대기로 세어 "기다리면 돼요"가 계속 이기고, 승격이 무력화된다.
            _skip_stamp(batch, "stuck")
            print("::warning::insta 무소득 %.1fh(임계 %.0fh 초과) — 두드려도 전멸 = 세션쿠키·계정 축 점검 필요"
                  % ((now - (okat or since)) / 3600, _STUCK / 3600), file=sys.stderr)
        # 429여도 **그 배치의 성공분은 살린다**(260730 검증 A-D1) — insta_subs는 계정별 fail-soft라
        #   5계정 중 4개 성공 후 5번째에서 429가 날 수 있는데, 종전 `return prev_items`는 그 4개를
        #   통째로 버렸다(배치에 리밋 상주 계정 1개가 끼면 그 5계정은 영원히 0건). 성공 계정만
        #   갈아끼우고 실패 계정은 이월 유지 = 데이터 순손실 0.
        out = _merge(prev_items, got, {a for a in (st.SUB_OK.get("insta") or ())})
        _metric(accounts, got, out, okat or since, now, "시도 %d계정 → 429 쿨다운 %.0fh" % (len(batch), wait / 3600))
        return out
    nxt = (off + len(batch)) % len(accounts)
    if got:
        okat = now
    _st_write(0, 0, now, nxt, okat, since)   # 성공 = 백오프 초기화 + 회전 전진
    out = _merge(prev_items, got, done)
    if stuck and not got:
        _skip_stamp(batch, "stuck")   # 429도 안 났는데 전멸 = 로그인월·계정 축(위 429 경로와 동일 승격)
        print("::warning::insta 무소득 %.1fh(임계 %.0fh 초과) — 리밋도 아닌데 전멸 = 세션쿠키·계정 축 점검 필요"
              % ((now - (okat or since)) / 3600, _STUCK / 3600), file=sys.stderr)
    print("::notice::insta 배치 %d계정(%d/%d 지점) 수집 %d건 · 이월 %d건"
          % (len(batch), off, len(accounts), len(got), len(out) - len(got)), file=sys.stderr)
    _metric(accounts, got, out, okat or since, now, "시도 %d계정(%d/%d 지점)" % (len(batch), off, len(accounts)))
    return out


acc, reg = st._load_accounts()
_tk_kr, _tk_gl = st._region_split("tiktok", acc, reg)   # 틱톡 지역분리(러너 _rsubs 동일 정본) — KR 독립 top-N = 큐레이션 한국 굶김 방지(운영자 260719 봉인)
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "viewer", "sns_subs_phone.json")
try:   # 직전 산출물 = 인스타 회전 병합의 이월분(다른 축은 종전대로 매 런 전량 재수집이라 미사용)
    _prev = json.load(open(P, encoding="utf-8")) or {}
    _prev_insta = _prev.get("insta") or []
    _prev_x = _prev.get("x") or []   # 엑스도 이월 대상 편입(260819 주기 게이트 · 스킵 회차 0건 굳음 차단)
except Exception:  # noqa: BLE001 — 최초 실행·파손 = 이월 없음(fail-open)
    _prev_insta, _prev_x = [], []
out = {"x": _x_collect(acc["x"], _prev_x), "insta": _insta_collect(acc["insta"], _prev_insta),
       # ⑯ x_search(가계정 X 검색) 폰 배선 제거 — adaptive.json 폐지 확정(빈 응답 실측 260723) + main() 미소비 = 데드콜. x_search 함수는 sns_trends.py에 dormant 존치(break-glass · env X_AUTH_TOKEN/X_CT0 보존) · 홈IP 밴 리스크 상환 · 딥링크(x.com/search)가 값 커버 · 평의회 260723 #3
       "threads": st.threads_subs(acc["threads"], limit=20),   # ⑧ 스레드(운영자 260712) — 계정 미등록 = [] no-op
       "tiktok": st.tiktok_subs(_tk_kr, limit=12) + st.tiktok_subs(_tk_gl, limit=12),   # 틱톡 구독(운영자 260721) — 러너 데센 IP가 tikwm /user/posts에 HTTP 403(WAF IP블록 실측 run 29800229859) → 가정 IP가 주 공급 · 지역별 독립 top-12(KR 먼저 = 큐레이션 한국 채움)
       "reddit": st.reddit_hot([s.strip() for s in (os.environ.get("REDDIT_SUBS") or "popular,korea,worldnews").split(",") if s.strip()]),   # ⑥ 레딧(운영자 260713) — 러너 403 Blocked 실측 → 가정 IP가 주 공급(소비 = sns_trends main 폰 채택)
       "disaster": st.disaster(limit=10)}   # ⑭ 재난문자(운영자 260713) — safetydata.go.kr이 러너 IP 차단·타임아웃 실측 → 가정 IP가 유일 공급원. 키 = 폰 env SAFETY_KEY(phone_subs.sh가 ~/.nomute_phone_env source · 미설정 = st.disaster 자체 [] no-op)
for k in ("x", "insta", "threads", "tiktok"):   # 지역 도장 = 러너 수집과 동일 규격(뷰어 한국/세계 접이 축 · 레딧 = 계정축 아님 = 무도장)
    for it in out[k]:
        it["region"] = reg.get(k, {}).get((it.get("account") or "").lower(), "gl")
# 계정별 성공·사유 동봉(260728) — 폰 채택 축(x·insta·threads·tiktok)은 **데이터는 폰인데 사유는 러너**라
#   miss와 why의 주체가 어긋나 있었다(러너 429/403 기록이 폰 결과 위에 얹혀 엉뚱한 계정을 지목). 같이 실어
#   보내면 sns_trends main()이 PHONE_COVER로 갈아 끼운다. set = JSON 불가라 정렬 리스트로.
out["_cover"] = {"ok": {k: sorted(v) for k, v in st.SUB_OK.items()}, "why": st.SUB_FAIL}
# 착지 원장 동봉(운영자 260806 "매번 고치는데 왜 재발하냐" · 8인 평의회) — 직전 회차가 **어디서 막혔는지**.
#   ⚠ 신설 사유 = 폰의 실패 서사가 전부 `~/phone_subs.log`(폰 로컬)에 갇혀 레포엔 **파일 나이 1비트**만
#   도착했다(평의회6 판정 BLIND 92) → watchdog 이 5개 원인{폰 죽음·수집 실패·git 착지·인증 만료·회선}을
#   구분 못 해 매번 "termux/맥 크론 확인해"만 단정했고, 운영자는 크론이 멀쩡한 걸 확인한 뒤 **남은 4축을
#   조사할 증거가 아무 데도 없는 상태**로 원점 복귀했다 = 260727·260806 재발의 구조적 뿌리.
#   ▷ 원장이 git 밖(`$HOME`)이라 **착지가 막혀도 쓰인다** — 이번 회차에 못 실리면 복구된 다음 회차에
#     「직전에 이래서 막혔다」가 실린다(= "git 으로 git 실패를 보고한다"는 모순의 유일한 해 · 1주기 지연 감수).
try:
    _ld = open(os.path.expanduser("~/.nomute_phone_land"), encoding="utf-8").read().strip().split("|")
    if len(_ld) >= 2 and _ld[1]:
        out["_cover"]["landing"] = {"at": _ld[0], "state": _ld[1], "why": (_ld[2] if len(_ld) > 2 else "")}
except Exception:  # noqa: BLE001 — 원장 부재(최초 실행)·파손 = 종전 동작 그대로(fail-open)
    pass
out["updated"] = st.datetime.now(st.KST).isoformat()   # KST(§📐 — 소비측 신선도 판정 기준)
json.dump(out, open(P, "w", encoding="utf-8", errors="replace"), ensure_ascii=False, indent=1)
print(f"phone-subs 수집: x {len(out['x'])}건 · insta {len(out['insta'])}건 · threads {len(out['threads'])}건 · tiktok {len(out['tiktok'])}건 · reddit {len(out['reddit'])}건 · 재난 {len(out['disaster'])}건")
