#!/usr/bin/env bash
# 채널 요약(메뉴4) AI 브리프 — 인스타 채널 지표(insta_data.json)를 보고 '성장 서사 + 지금 상황 + 관리 전략'을 짚어주는 브리핑(운영자 260714 "초등학생도 아 이 채널 이렇게 성장해왔네·이래야겠네 전략이 뿅뿅").
# ⚠️ SNS 트렌드 브리프(sns_brief.sh·viewer/sns_brief.json)와 완전 별개 축 — 골격만 미러(운영자 "트렌드 요약 참고만·덮어씌우지 말고") · 출력 = viewer/chan_brief.json.
# 페르소나 = "채널을 같이 키우는 친한 그로스 애널리스트 · 호칭·이름 없이 친근 인사(KST) · 성장 서사 → 급변 원인 콕 → 데이터 근거 실행 전략 · 쉬운 말 · 수치 신뢰선 사수"(sns_brief v8 톤 계승).
# 구성 = 기간 5부(운영자 260714 "1년 전반부 총론만 나옴 → 구분 요약" · 2차 확정 = 3일/7일/28일/3개월/전체 총론) — 출력 = sections[{k,label,text}] + text(전문 = 하위호환·마커 파싱 실패 시 유일 렌더).
# 게이트 3중(sns_brief.sh 계승): ① CHAN_BRIEF=1(§📰-e 카나리아 — 기본 OFF 머지 → dispatch 실측 → 승격) ② 입력 다이제스트 동일 = 스킵(토큰 0 · 데이터 무변화 = 재생성 낭비 0) ③ 실패 = fail-soft(직전 brief 유지 · rc 0 — 뷰어는 파일 없으면 블록 미표시 = 조용한 공백).
# 모델 = PIPE_MODEL(opus 5 · shared/model_env.sh — §🤖 생성/하드작업 축) · effort max · turns 8 · timeout 600 · 운영자 "토큰 아끼지 말고" = 다이제스트에 전 축 탑재.
# --safe-mode(--bare 절대 금지 = OAuth 즉사 §📰-d) · 폴오버 SSOT 경유(§📰-f) · WebSearch/WebFetch = --allowedTools 명시(게시물 소재 사건 맥락 확인용 — 헤드리스는 미허용 도구 즉시 거부 · sns_brief 실측 260713 계승).
set -u
[ "${CHAN_BRIEF:-0}" = "1" ] || { echo "chan-brief: OFF(CHAN_BRIEF!=1) — 스킵"; exit 0; }
cd "$(git rev-parse --show-toplevel)"
[ -s viewer/insta_data.json ] || { echo "chan-brief: insta_data.json 없음 — 스킵(no-op 스캐폴드)"; exit 0; }
. shared/model_env.sh
. shared/claude_transient.sh
. shared/claude_meter.sh        # claude_meter() SSOT — 토큰 계측(analyze.sh:72 동형 · 260803 계측 사각 봉합)
MODEL="${CHAN_BRIEF_MODEL:-$PIPE_MODEL}"
OUT_JSON="viewer/chan_brief.json"

# ── 입력 다이제스트(insta_signals 산출물의 표시 전용 요약 — 재계산 0 · 지침 §4-7 분업 유지) + 변화 해시 ──
DIG="$(python3 - <<'PY'
import json, hashlib
def fv(v):
    """조회수 → 만/억 단위 한국식(반올림) — 원시 콤마숫자를 모델에 먹이면 만단위 지시를 무시하던 근원 차단(sns_brief 분신술2 계승)."""
    v = v or 0
    if v >= 100_000_000:
        s = ("%.1f" % (v / 100_000_000)).rstrip('0').rstrip('.')
        return "%s억" % s
    if v >= 10_000:
        return "{:,}만".format(round(v / 10_000))
    return "{:,}".format(round(v))
def pm(x):
    return '—' if x is None else ("%.2f" % x).rstrip('0').rstrip('.')
d = json.load(open('viewer/insta_data.json'))
if not d.get('profile'):
    print(''); raise SystemExit
p = d['profile']; a = d.get('account_day') or {}; avg = d.get('avg') or {}
L = ['[계정 지금]']
L.append(f"팔로워 {fv(p.get('followers_count'))} · 최근일 조회 {fv(a.get('views'))} · 도달 {fv(a.get('reach'))} · 공유 {fv(a.get('shares'))} · 저장 {fv(a.get('saves'))} · 프로필 방문 {fv(a.get('profile_views'))}")
AVL = {'views': '조회', 'reach': '도달', 'profile_views': '방문', 'interactions': '상호작용', 'follows': '팔로우', 'posts': '게시'}
rows = []
for k, lb in AVL.items():
    v = avg.get(k) or {}
    if v.get('ratio_7d') is None: continue
    rows.append(f"{lb} 최근7일평균 {fv(v.get('avg_7d'))}/일 = 전기간평균({fv(v.get('avg_all'))}/일)의 {round(v['ratio_7d']*100)}%")
if rows: L.append('[7일 대 전기간 평균] ' + ' · '.join(rows))
# 팔로워 활동 시간대(운영자 260714 "시간대는 총론 반영 가능") — 관객 쪽 데이터 = 게시 스케줄 교란 무관 · 수기 폴백이면 출처 명시
if d.get('online_peak_kst'):
    _pk = ' · '.join(d['online_peak_kst']) if isinstance(d['online_peak_kst'], list) else str(d['online_peak_kst'])
    _src = str(d.get('online_src') or '')
    L.append(f"[팔로워 접속 피크(KST)] {_pk}" + (f" — 출처: 운영자 인사이트 실측({_src[7:-1]})" if _src.startswith('manual(') else ''))
    _oh = d.get('online_hours_kst')
    if _oh:
        try:
            _hs = ' · '.join(f"{h}시 {v}" for h, v in sorted(_oh.items(), key=lambda x: int(x[0])))
            L.append(f"[팔로워 활동 시간 분포(KST · 상대 높이 = 피크 100)] {_hs}" + (f" — {d['online_note']}" if d.get('online_note') else ''))
        except Exception:
            pass
eras = d.get('eras') or {}
if eras:
    L.append('[성장 3기(게시물 성과 기준)]')
    for k in sorted(eras):
        v = eras[k]
        L.append(f"{k}: 게시물 {v.get('n')}개 · 조회 중앙 {fv(v.get('views_med'))}(평균 {fv(v.get('views_avg'))}) · 1천뷰당 공유 {pm(v.get('share_pm_med'))}·저장 {pm(v.get('save_pm_med'))}·댓글 {pm(v.get('cmt_pm_med'))}·좋아요 {pm(v.get('like_pm_med'))}")
ev = (d.get('daily_meta') or {}).get('events') or []
if ev:
    L.append('[운영자 관측 변곡 이벤트] ' + ' / '.join(f"{e.get('date')} {e.get('label')}({e.get('note','')})" for e in ev))
series = d.get('daily_series') or []
if series:
    # ⚠ 260809 실사고 봉합(운영자 "너무 수박 겉핥기 · 2일째 거의 올린 게 없는 게 문제인데 너무 돌려 말한다"):
    #   구판은 이 줄에 조회·게시수·follows만 실었는데 실측 = **views가 최근 30일 전건 결측**(7/13~8/9 · API 축 죽음)이고
    #   follows도 말미 전건 0-fill(뷰어가 이미 결측 처리하는 그 축) → 모델이 사흘을 말할 일별 근거가 **한 칸도 없었다**.
    #   그래서 [계정 지금]의 최근일 스냅샷 하나로 사흘을 논하다 "아직 하루가 안 찼으니 최종치는 아니다" 류로 뭉갤 수밖에 없었다
    #   (= 겉핥기는 모델의 게으름이 아니라 **데이터가 지워진 자리**였다 · 스레드 `[1차 실측]`·틱톡 `_e1`과 같은 병).
    #   → 살아있는 실측 2축을 싣는다: **도달(reach = 전건 실측)** + **팔로워 순증감(follower_net = 27일치 실측)**,
    #     그리고 그날 올린 게시물을 **실명·조회로**(post_refs) — "어느 날 뭘 올렸고 그날 계정이 어떻게 움직였나"가 한 줄에 붙는다.
    L.append('[최근 30일 일일 계정 실측 — 조회·도달·게시 수·팔로워 **순증감**(=신규 유입 빼기 취소 · 위 「신규 유입」과 다른 자다)·그날 올린 것(— = 미수집)]')
    for r in series[-30:]:
        _rf = ' / '.join(f"«{str(x.get('name') or '(무캡션)')[:22]}» {fv(x.get('views'))} 링크 {x.get('permalink') or '—'}" for x in (r.get('post_refs') or [])[:3])
        _nt = r.get('follower_net')
        L.append(f"{str(r.get('date',''))[5:]} 조회 {fv(r.get('views')) if r.get('views') is not None else '—'}"
                 f" · 도달 {fv(r.get('reach')) if r.get('reach') is not None else '—'}"
                 f" · 게시 {r.get('posts') if r.get('posts') is not None else 0}"
                 f" · 팔로워 {(('+' if _nt > 0 else '') + format(_nt, ',')) if isinstance(_nt, int) else '—'}"
                 + (f" · 올린 것: {_rf}" if _rf else ''))
    # [게시 리듬 ↔ 반응] — 운영자가 가장 알고 싶어 한 축("올리던 일일 게시가 낮아지니 조회 터지는 게 멈춰있는 실황").
    # 표시용 합산만(신호 원본 = insta_signals · [기간 창별 실측]과 같은 관례) · 결측일은 분모에서 뺀다(0으로 세면 거짓 하락).
    try:
        import statistics as _stt, datetime as _dtr
        _win = [r for r in series[-28:] if r.get('reach') is not None or r.get('views') is not None]
        def _amt(r): return r.get('views') if r.get('views') is not None else r.get('reach')
        _lbm = '조회' if all(r.get('views') is not None for r in _win) else '도달(조회 미수집 구간 = 도달로 대체)'
        _on = [_amt(r) for r in _win if (r.get('posts') or 0) > 0]
        _off = [_amt(r) for r in _win if not (r.get('posts') or 0)]
        if len(_on) >= 3 and len(_off) >= 3:
            _mo, _mf = _stt.median(_on), _stt.median(_off)
            _last = next((r for r in reversed(series) if (r.get('posts') or 0) > 0), None)
            _gap = ''
            if _last and _last.get('date'):
                _dd = (_dtr.date.fromisoformat(max(r['date'] for r in series if r.get('date'))) - _dtr.date.fromisoformat(_last['date'])).days
                _gap = f" · 마지막 게시일 {_last['date'][5:]}(그로부터 {_dd}일) · 그 뒤 게시 0인 날 {_dd}일 연속"
            _nets = [r['follower_net'] for r in series[-14:] if isinstance(r.get('follower_net'), int)]
            _nline = ''
            if _nets:
                _nline = (f" || 같은 창 팔로워: 최근 {len(_nets)}일 순증 합 {('+' if sum(_nets) > 0 else '')}{sum(_nets):,}명"
                          f"(줄어든 날 {sum(1 for x in _nets if x < 0)}일 · 최근 3일 {' · '.join(('+' if x > 0 else '') + str(x) for x in _nets[-3:])})"
                          f" = 계정 {_lbm.split('(')[0]} 축과 팔로워 축은 **따로 움직인다**(각각 말할 것)")
            L.append(f"[게시 리듬 ↔ 반응 실측(최근 {len(_win)}일 · 단위 = {_lbm})] "
                     f"올린 날({len(_on)}일) 중앙 {fv(_mo)} vs 안 올린 날({len(_off)}일) 중앙 {fv(_mf)} = **{round(_mo / _mf, 2) if _mf else '—'}배**"
                     f"{_gap}{_nline}")
    except Exception:
        pass
    # [주 단위 리듬(최근 4주)] — [28일] 창의 재료(운영자 260809 2차 "배선 ㄱㄱ" = [3일] 문법을 7일·28일로 확장).
    # ⚠ 이게 없으면 모델이 위 30줄을 **손으로 세서** 주 단위를 만든다 — 260809 첫 산출이 실제로 그랬고(「서른 날 중 열엿새가 빈칸」 = 실측 16일 정확),
    #   맞았다는 건 운이 좋았다는 뜻이지 계약이 아니다(누락·오산이 나도 아무도 못 잡는다 = 이 레포가 싫어하는 「사람 눈이 유일한 검출기」).
    # 축 = 게시 수 · 빈 날 · 도달 중앙 · 팔로워 순증 · **중앙 초과 장수**(= 그 주에 「크게 터진 장」이 몇 개였나 = 공백의 의미를 가르는 값).
    try:
        import statistics as _stw, datetime as _dtw
        _anc = max(_dtw.date.fromisoformat(r['date']) for r in series if r.get('date'))
        _pl = d.get('posts') or []
        _vv = [x['views'] for x in _pl[:20] if x.get('views')]
        _med = _stw.median(_vv) if len(_vv) >= 5 else None
        _wk = []
        for _k in range(4):
            _lo = _anc - _dtw.timedelta(days=7 * _k + 6); _hi = _anc - _dtw.timedelta(days=7 * _k)
            _rr = [r for r in series if r.get('date') and _lo <= _dtw.date.fromisoformat(r['date']) <= _hi]
            if not _rr: continue
            _rc = [r['reach'] for r in _rr if r.get('reach') is not None]
            _nt = [r['follower_net'] for r in _rr if isinstance(r.get('follower_net'), int)]
            _big = sum(1 for x in _pl if _med and _lo.isoformat() <= str(x.get('iso'))[:10] <= _hi.isoformat() and (x.get('views') or 0) > _med)
            _wk.append(f"{_lo.isoformat()[5:]}~{_hi.isoformat()[5:]}: 게시 {sum(r.get('posts') or 0 for r in _rr)}개"
                       f" · 빈 날 {sum(1 for r in _rr if not (r.get('posts') or 0))}일"
                       f" · 도달 중앙 {fv(_stw.median(_rc)) if _rc else '—'}"
                       f" · 팔로워 순증 {(('+' if sum(_nt) > 0 else '') + format(sum(_nt), ',')) if _nt else '—'}"
                       f" · 중앙 초과 장수 {_big if _med else '—'}")
        if _wk:
            L.append('[주 단위 리듬(최근 4주 · 최신 주부터) — 중앙 = 최근 20개 조회 중앙 %s]' % (fv(_med) if _med else '—'))
            L += _wk
    except Exception:
        pass
# 게시-팔로워 인과 실측(insta_signals 산출 — 회초리의 '왜냐면' 근거 · 운영자 260715 Q02)
tmg = d.get('timing') or {}
if tmg:
    L.append(f"[게시-팔로워 인과 실측(일별 {tmg.get('n_days')}일 · {tmg.get('from')}~{tmg.get('to')})] "
             f"팔로워 증가는 게시 행위(당일 상관 {tmg.get('corr_posts_follows')})가 아니라 당일 조회수(상관 {tmg.get('corr_views_follows')})를 따름 · 다음날까지 {tmg.get('corr_views_follows_next')} = 게시 후 24~48시간 창 · "
             f"안 올린 날(표본 {tmg.get('rest_days_n')}일)의 신규 유입 = 직전 3일 평균의 {round((tmg.get('rest_rel_med_ex_viral') or 0) * 100)}%(지연 바이럴 1일 제외 중앙 — 쉬면 다음날부터 꺼진다) · "
             f"올린 날 하루 **신규 유입**(취소 빼기 전) 중앙 {tmg.get('post_day_med')}명 ⚠창 {tmg.get('from')}~{tmg.get('to')} = 지금과 다른 시대가 섞였다 · "
             f"게시물 1개당 팔로워: {' · '.join(f'{k} {v}명' for k, v in (tmg.get('follows_per_post_by_era') or {}).items())} · {tmg.get('note','')}")
# 테마별 이탈 초과(운영자 260811 "어떤 게시물이 톤이 안 맞느냐" · 평의회 8인 · 정본 = insta_signals._theme_leak)
# ⚠ 판정이 아니라 사실 스냅샷이다. 아직 못 잴 때는 **왜 못 재는지**를 실어 보낸다(침묵하면 "문제 없음"으로 읽힌다).
tl = d.get('theme_leak') or {}
if tl.get('ready'):
    _fl = [t for t in (tl.get('themes') or []) if t.get('flag')]
    L.append(f"[테마별 이탈 초과 — 관측 {tl.get('n_days')}일 · 무게시 대조일 {tl.get('base_days')}일 · "
             f"무게시일 이탈 중앙 {tl.get('base_med')}명 · 문턱 {tl.get('z_cut')}배]")
    for t in (tl.get('themes') or []):
        _tail = '⚠문턱 넘음' if t['flag'] else f"(이 축은 {t['floor']}명 미만이면 안 보인다)"
        L.append(f"  {t['cat']}: 올린 날 {t['days']}일 · 이탈 중앙 {t['med']}명 · 무게시 대비 {t['excess']:+}명 · z {t['z']} {_tail}")
    if tl.get('waived'):
        L.append('  판정 유예(표본 부족): ' + ' · '.join(f"{w['cat']} {w['days']}일" for w in tl['waived']))
    L.append(f"  ※ {tl.get('note')}")
else:
    L.append(f"[테마별 이탈 초과] 아직 못 잰다 — {tl.get('why', '원장 미착수')}")

# 팔로워 표본(계정 인구통계 + 운영자 자가 보고 · 운영자 260715 Q03)
smp = d.get('audience_sample') or {}
if smp:
    _pcs = []
    if smp.get('age_gender_top'): _pcs.append('성·연령 상위: ' + ' · '.join(f"{x['k']} {x['pct']}%" for x in smp['age_gender_top']) + ' (U=성별미공개)')
    if smp.get('country_top'): _pcs.append('국가: ' + ' · '.join(f"{x['k']} {x['pct']}%" for x in smp['country_top'][:5]))
    if smp.get('city_top'): _pcs.append('도시: ' + ' · '.join(f"{x['k'].split(',')[0]} {x['pct']}%" for x in smp['city_top'][:5]))
    if smp.get('geo_base'): _pcs.append(f"국가·도시 퍼센트 분모 = {smp['geo_base']}(합이 100 미만 = API 상위 목록 밖 잔여)")   # 분모 명시(260726 교정 — 축 합 분모 시절 도시가 1.29배 부풀던 것)
    # 기준일 밀림 딱지(운영자 260726 한 수 승인) — 인구통계는 lifetime 스냅샷이라 자동 수집이 죽으면 값이 그대로 굳는다.
    # 모델이 그걸 '오늘의 관객'으로 읽고 최근 변화의 근거로 쓰는 걸 막는 게 목적(뷰어 demoStaleMsgs와 같은 판정식·같은 임계 2일).
    _lag = None
    if smp.get('as_of'):
        try:
            import datetime as _dt3
            _lag = (_dt3.date.fromisoformat(str(d.get('generated_kst'))[:10]) - _dt3.date.fromisoformat(str(smp['as_of']))).days
        except Exception:
            _lag = None
    _stale = f"(⚠ {_lag}일 전 기준 = 자동 갱신이 안 따라가는 축 · 오늘 값 아님)" if (_lag is not None and _lag >= 2) else ''
    L.append(f"[팔로워 표본(계정 전체 · API 실측{' · 기준 ' + smp['as_of'] + _stale if smp.get('as_of') else ''})] " + ' / '.join(_pcs))
    if smp.get('operator_note'):
        L.append('[팔로워 표본 — 운영자 자가 보고(데이터 아님 · 취급 주의)] ' + smp['operator_note'])
# 알고리즘 협착 — 운영자 가설 + 주제 간 실측(운영자 260715 Q05)
echo = d.get('echo') or {}
if echo.get('note'):
    ln = '[알고리즘 협착 — 운영자 가설(단정 금지)] ' + echo['note']
    ev = echo.get('evidence') or {}
    if ev:
        ln += f" || 이번 데이터 실측: 정치 1천뷰당 좋아요 {pm(ev.get('pol_like_pm_med'))}(전 주제 {ev.get('pol_like_rank')}위) · 조회 중앙 {fv(ev.get('pol_views_med'))} = 사회({fv(ev.get('soc_views_med'))})의 {ev.get('pol_vs_soc_views_pct')}%"
    L.append(ln)
# ── 기간 창별 실측(운영자 260714 "7일·14일·28일·3개월·전체 총론 구분 요약") — 각 기간 섹션의 수치 근거(표시용 합산만 · 신호 원본 = insta_signals §4-7 분업 유지) ──
if series:
    import datetime as _dt
    _anchor = max(_dt.date.fromisoformat(r['date']) for r in series if r.get('date'))
    _allv = [r['views'] for r in series if r.get('views') is not None]
    _base = (sum(_allv) / len(_allv)) if _allv else 0
    pall = d.get('posts') or []
    L.append('[기간 창별 실측(창 = 최신일서 거슬러) — 기간 섹션 요약의 근거]')
    for _days, _lb in ((3, '3일'), (7, '7일'), (28, '28일'), (90, '3개월')):   # 3일 신설·14일 제거(운영자 260714 2차 "3일, 7일, 28일, 3개월, 전체")
        _lo = _anchor - _dt.timedelta(days=_days - 1)
        _rows = [r for r in series if r.get('date') and _dt.date.fromisoformat(r['date']) >= _lo]
        _vs = [r['views'] for r in _rows if r.get('views') is not None]
        if not _vs: continue
        _avgd = sum(_vs) / len(_vs)
        _pn = sum(r.get('posts') or 0 for r in _rows)
        _pp = sorted((x for x in pall if str(x.get('iso') or '')[:10] >= _lo.isoformat()), key=lambda x: -(x.get('views') or 0))[:3]
        _ln = f"{_lb}: 일평균 조회 {fv(_avgd)}(전기간 일평균의 {round(_avgd / _base * 100) if _base else 0}%) · 조회 합계 {fv(sum(_vs))} · 게시 {_pn}개"
        if _pp: _ln += ' · 창 내 톱 게시물: ' + ' / '.join(f"{str(x.get('name') or '(무캡션)')[:28]}(조회 {fv(x.get('views'))})" for x in _pp)
        L.append(_ln)
# 게시 요일 분포 + 교란 딱지(운영자 260714 "토일월에 쉬어서 그때 많이 올림 — 요일 성과는 그 영향이 커") — 요일 우열 단정을 데이터로 차단
_pall = d.get('posts') or []
if _pall:
    import datetime as _dt2
    _dc = {}
    for x in _pall:
        try:
            _w = ['월', '화', '수', '목', '금', '토', '일'][_dt2.datetime.fromisoformat(str(x.get('iso')).replace('Z', '+00:00')).weekday()]
            _dc[_w] = _dc.get(_w, 0) + 1
        except Exception:
            pass
    if _dc:
        L.append('[게시 요일 분포(표본 ' + str(sum(_dc.values())) + '개) — ⚠운영자 휴무일(토·일·월)에 게시 몰림: 요일별 성과 차이는 게시량 영향이 커서 요일 우열 단정 금지] '
                 + ' · '.join(f"{k} {_dc.get(k, 0)}" for k in ('월', '화', '수', '목', '금', '토', '일')))
fmt = d.get('fmt') or {}
if fmt:
    L.append('[포맷별(전 기간)] ' + ' / '.join(f"{k}: n={v.get('n')} · 조회 중앙 {fv(v.get('views_med'))} · 1천뷰당 공유 {pm(v.get('share_pm_med'))}·저장 {pm(v.get('save_pm_med'))}" for k, v in fmt.items()))
tp = d.get('topics') or {}
tk = sorted((k for k in tp if (tp[k].get('n') or 0) >= 5), key=lambda k: -(tp[k].get('views_med') or 0))
if tk:
    L.append('[주제별 조회 중앙] ' + ' · '.join(f"{k} {fv(tp[k].get('views_med'))}(n={tp[k].get('n')})" for k in tk[:10]))
axes = (d.get('signals') or {}).get('axes') or {}
AXL = [('format', '포맷'), ('naming_style', '네이밍 스타일'), ('hour_band', '업로드 시간대'), ('dow', '업로드 요일')]
sg = []
for ax, lb in AXL:
    for b in (axes.get(ax) or [])[:3]:
        lift = b.get('lift') or {}
        sg.append(f"{lb}={b.get('bucket')}: 공유 ×{lift.get('share_pm','—')} · 저장 ×{lift.get('save_pm','—')} · n={b.get('n')}{' (표본부족)' if b.get('low_sample') else ''}")
if sg: L.append('[호응 신호(평균 대비 배율)] ' + ' / '.join(sg))
posts = d.get('posts') or []
if posts:
    def tag(x):
        """반응 지문(fp = 채널 중앙 2배↑ 지배 반응축 — 그 게시물에 반응한 표본의 대리 지표)·확장문(exp) 딱지."""
        t = ''
        if x.get('fp'): t += f" · 지문 {x['fp']}"
        if x.get('exp'): t += ' · 🚪확장문'
        return t
    L.append('[TOP 게시물(점수순 12) — 지문 = 반응한 표본의 결(공유형=지인에 퍼나름·저장형=모아둠·댓글형=참전·좋아요형=가볍게 호응) · 🚪확장문 = 주력 주제 밖에서 평소 2배↑ 터짐+저장 강세 = 기존 팔로워 밖 새 표본 유입 신호]')
    for i, x in enumerate(posts[:12]):
        L.append(f"{i+1}위 [{x.get('iso','')} {x.get('format','')}·{x.get('style','')}·{x.get('cat','')}·{x.get('era','')}] {str(x.get('name') or '(무캡션)')[:60]} · 조회 {fv(x.get('views'))} · 1천뷰당 공유 {pm(x.get('share_pm'))}·저장 {pm(x.get('save_pm'))}{tag(x)} · 링크 {x.get('permalink') or '—'}")
    # 최근 게시물 = 나이(경과)·채널 중앙 대비 배수 동반(운영자 260809 "각각의 게시물 조회가 어떤 게 유지되고").
    # ⚠ 나이가 없으면 "아직 크는 중"과 "다 큰 것"을 구분할 수단이 아예 없어서 모델이 뭉갤 수밖에 없다(그게 겉핥기의 절반).
    # 성숙 기준 48h = brief_lib RIPE_H 동값(원장 성과 비교의 그 축) — 사본이 아니라 같은 판정선을 쓴다는 뜻.
    import datetime as _dta
    _now = _dta.datetime.fromisoformat(str(d.get('generated_kst')))
    _recent = sorted(posts, key=lambda x: str(x.get('iso') or ''), reverse=True)
    _med20 = None
    try:
        import statistics as _st2
        _vv = [x['views'] for x in _recent[:20] if x.get('views')]
        _med20 = _st2.median(_vv) if len(_vv) >= 5 else None
    except Exception:
        _med20 = None
    def _age(x):
        try:
            _h = (_now - _dta.datetime.fromisoformat(str(x.get('iso')).replace('Z', '+00:00')).astimezone(_now.tzinfo)).total_seconds() / 3600
        except Exception:
            return ''
        _s = f" · 올린 지 {round(_h)}시간" if _h < 48 else f" · 올린 지 {round(_h / 24)}일"
        return _s + ('(아직 크는 중 = 48시간 미만 · 최종치 아님)' if _h < 48 else '(다 큰 값)')
    def _rel(x):
        return f" · 최근 20개 중앙 대비 ×{round((x.get('views') or 0) / _med20, 2)}" if _med20 else ''
    L.append(f"[최근 게시물(최신 10) — 나이·중앙 대비 동반 · 최근 20개 조회 중앙 {fv(_med20) if _med20 else '—'}]")
    for x in _recent[:10]:
        L.append(f"[{x.get('iso','')} {x.get('format','')}·{x.get('style','')}·{x.get('cat','')}] {str(x.get('name') or '(무캡션)')[:60]} · 조회 {fv(x.get('views'))}{_rel(x)} · 1천뷰당 공유 {pm(x.get('share_pm'))}{tag(x)}{_age(x)} · 링크 {x.get('permalink') or '—'}")
    _exps = [x for x in posts if x.get('exp')]
    if _exps:
        L.append('[🚪확장문 게시물(최신 8) — 채널이 커지는 문 후보]')
        for x in sorted(_exps, key=lambda x: str(x.get('iso') or ''), reverse=True)[:8]:
            L.append(f"[{x.get('iso','')} {x.get('cat','')}] {str(x.get('name') or '(무캡션)')[:60]} · 조회 {fv(x.get('views'))}{tag(x)} · 링크 {x.get('permalink') or '—'}")
body = '\n'.join(L)
PVER = 'chanbrief-v16-260811-leak'   # v15 = 게시물 링크 참조(골드·이탤릭 .tbrief-ref 계승) + 강조 밀도 개정(2층 섹션당 3~5·1층 1) + [3개월] 기 대 기 리듬(운영자 260809 3차)   # 구   # v14 = 7일·28일 확장   # v14 = [7일]·[28일]에 [3일] 실황 문법 확장(운영자 260809 2차 "배선 ㄱㄱ") — 7일 = 그 주 게시물 한 장씩 개별 판정+축 분리 · 28일 = [주 단위 리듬] 4주 블록 신설(중앙 초과 장수 = 그 주 성패 축 · 구판은 모델이 30줄을 손으로 세야 했다)   # 구   # v13 = [3일] 실황   # v13 = [3일] 실황 두껍게(운영자 260809 "수박 겉핥기 · 게시물 하나하나 디테일 · 너무 돌려 말한다") — 실측 진범 = 데이터 공백: views 최근 30일 전건 결측 + follows 말미 0-fill이라 모델이 사흘을 말할 일별 근거가 0칸이었다 → 살아있는 축(도달·팔로워 순증감·그날 올린 것 실명) 편입 + [게시 리듬 ↔ 반응] 신설 + 게시물 나이·중앙 대비 배수 + 완곡어법 금지 전 섹션 계약   # 구   # v12 = 총론 디테일 복원(운영자 260808 5차 실측 지적 — 게시물 실명·이유·바깥 시류·알고리즘 추정·흐름 제안 3문단 필수 · ⑦ 시류 원료 동반)   # 구   # v11/v5 = ⑥ 정체 축 → 오늘의 행동 1개 강제(운영자 260808 3차 — 반복만 하고 안 옮겨지던 고리 절단)   # 구   # v10 = 누적 지식 라이브러리(운영자 260808 — 직전 1회차 1500자[전문의 36%]만 보던 것을 24회차 판단 원장으로 교체: 정체성 궤적·총론 방향·반복 제안·갈린 축 · 정본 apps/insta/brief_lib.py)   # v9.4 = 팔로워 표본 기준일 딱지(운영자 260726 · 밀리면 ⚠N일 전 병기) · v9.3 = 총론 '→ 그래서 무엇을' 결론 1줄 필수 + 강조 밀도 상향(운영자 260717 — 총론이 최장 판인데 볼드 2개·강조색 0으로 밋밋 실측 → 볼드 넉넉히·핵심어 1층)   # v9.2 = 신뢰 게이트(운영자 260715 Q06 — 거의 확실만 해석·방향)   # v9.1 = 알고리즘 협착 가설+실측(운영자 260715 Q05) · v9 = 회초리·표본(운영자 260715 Q02·Q03 — 인과 실측·팔로워 표본·반응 지문·확장문)   # 프롬프트 버전 — 바뀌면 해시 불일치 = 다음 run 강제 재생성 · v8 = 총론 분리(운영자 260714 "총론=비전·방향성·미션 큰 그림 3~12개월 / 전체=전체 기간 분석 디테일" — [전체 총론] 1부 → [전체]+[총론] 2부 = 6부) · v7 = 강조 2층 · v6 = 시간대·요일교란 · v5 = 존재이유+연재+아카이브 · v4 = 3일신설 · v3 = 5부 · v2 = 프리앰블금지
print(hashlib.sha256((PVER + '\n' + body).encode()).hexdigest()[:16])
print(body)
PY
)" || { echo "::warning::chan-brief 다이제스트 실패 — 직전 유지"; exit 0; }
SHA="$(printf '%s\n' "$DIG" | head -1)"
BODY="$(printf '%s\n' "$DIG" | tail -n +2)"
[ -z "$BODY" ] && { echo "::warning::chan-brief 입력 빈 값(profile 없음 등) — 직전 유지"; exit 0; }
PREV="$(python3 -c "import json;print(json.load(open('$OUT_JSON')).get('src_hash',''))" 2>/dev/null || echo '')"
if [ -n "$SHA" ] && [ "$SHA" = "$PREV" ]; then
  echo "chan-brief: 입력 동일($SHA) — 스킵(토큰 0)"
  exit 0
fi

KST_NOW="$(TZ='Asia/Seoul' date '+%Y-%m-%d %H:%M %A')"   # 발화 기준 = 항상 한국시(§📐-d)

# ── 누적 지식 라이브러리 동봉(운영자 260808 "매번 판단이 그때그때 참고 지식이 없어서 새로 시작하는 것 같다 · 채널 요약의 라이브러리가 있으면 좋을듯 · 쌓이면 경쟁력") ──
# 구판 = 직전 1회차 text 앞 **1500자**만 동봉(운영자 260714 3차 연재 축) → 260808 실측 = 브리프 전문 4,187자라 **64% 절단**,
# 컷 지점이 [28일] 중간이라 [3개월]·[전체]·[총론]이 통째로 증발했다. 총론 = 정체성·비전 = 가장 오래 가는 판단인데 매 회차 백지.
# 그 결과 = 정체성 표현 8일 8변 · 업로드 시간대 제안이 하루 만에 정반대로 뒤집힘(어제 뭐라 했는지 모르니까).
# → 아카이브(chan_brief_log.jsonl · 이미 24회차 축적)를 라이브러리로 굽는다: ①정체성 궤적 ①-b총론 방향 ②반복 제안 ③갈린 축 ④직전 전문(3000자).
# LLM 0콜·네트워크 0·stdlib only(정본 = apps/insta/brief_lib.py) · fail-soft(실패 = 빈 블록 = 종전 동작).
LIB_BLOCK="$(python3 apps/insta/brief_lib.py --scope ig 2>/dev/null || true)"
[ -n "$LIB_BLOCK" ] && LIB_BLOCK="
$LIB_BLOCK
"

PROMPT="너는 이 인스타 뉴스 채널(@no_mute)을 운영자와 같이 키우는 친한 그로스 애널리스트다. 아래는 이 채널의 실제 지표 데이터다. 지표 나열이 아니라, 이걸 읽고 '이 채널이 어떻게 성장해왔고 · 지금 무슨 일이 벌어지고 있고 · 그래서 뭘 하면 되는지'를 이야기해준다. 지금 시각(한국): ${KST_NOW}.

[존재 이유 — 운영자가 이걸 읽는 목적]
이슈 터졌나 감시하는 게 아니다. *기간 창끼리 추이를 비교해 전략 방향을 잡는* 도구다 — 3일→전체로 창이 넓어질수록 나무에서 숲으로 시야가 바뀌는 맛이 핵심. 짧은 창에서 '문제'로 보이던 게 긴 창에선 '정상 리듬'이거나 그 반대인 지점을 명시적으로 짚어라. 매 섹션의 마지막 줄 = 그 창에서만 보이는 전략적 시사점 한 줄(이 창을 열어보는 이유가 되는 문장).

[여는 인사]
가볍고 친근하게, 호칭·이름 없이 열어라 — 예: '일요일 밤이니까 이번 주 채널 상태 짚고 갈게.' (이름 부르기·'안녕 ○○'·'사장님' 류 호칭 전면 금지 · 딱딱한 비서 톤 금지 · 매번 똑같은 문장은 피하기.)

[출력 구조 — 6부(기간 5창 + 총론) · 절대 준수]
아래 6개 섹션 마커를 정확히 이 표기 그대로, 이 순서로, 각각 단독 줄로 쓴다(마커 줄에 다른 글자 금지 · 첫 마커 위에 아무것도 쓰지 마라):
[3일]
[7일]
[28일]
[3개월]
[전체]
[총론]
- [3일] = 지난 사흘의 **실황 중계**. 여는 인사 한 줄로 시작. ⚠ **운영자 260809 개정 — '수박 겉핥기 · 게시물 하나하나의 디테일을 잡아달라 · 너무 돌려 말하니 유의미한 인사이트가 안 나온다'는 실측 지적.** 아래 4개를 전부 넣는다(**6~9줄**):
  ⓪ **[단위 계약 — 어기면 그 문장은 통째로 거짓말이다]** 이 데이터에는 서로 다른 두 자가 있다.
     · **신규 유입** = 그날 새로 들어온 사람 수(취소를 빼기 전). 「올린 날 하루 신규 유입 중앙 N명」이 이 자다.
     · **순증감** = 신규 유입 빼기 취소. 일별 줄의 「팔로워 +77」이 이 자다.
     **두 자를 한 문장에서 비교하거나 나누지 마라.** 실제 사고 예 — 「하루 신규 중앙 287인데 8/10은 겨우 +77,
     4분의 1로 꺾였다」는 **틀린 문장**이다(287=신규, 77=순증. 같은 자로 바꾸면 292라 꺾인 적이 없다).
     비교하려면 같은 자끼리만 하고, 창이 다르면 창을 밝혀라(신규 중앙의 창은 지금과 다른 시대가 섞여 있다).
  ⓪-b **[테마 이탈 계약]** [테마별 이탈 초과] 블록이 「아직 못 잰다」면 **이 축을 아예 언급하지 마라**(없는 결론 금지).
     값이 있으면 ⚠문턱을 넘은 축만 말하고, **게시물 한 장을 범인으로 지목하지 마라** — 그 데이터는 존재하지 않는다
     (게시물별 취소 지표가 API에 없고 하루에 여러 장을 올린다). 말해도 되는 건 「이 테마를 올린 날의 이탈이
     안 올린 날보다 N명 많았다」까지다. 그리고 **금지형이 아니라 배치형으로 써라** — 「이 테마를 올리지 마라」가
     아니라 「이 결은 큰 장 다음날 자리에 놓지 마라」 쪽. 없애는 조언은 검증이 영영 불가능하고(안 올린 글의
     성적표는 존재하지 않는다) 배치하는 조언은 다음 회차에 검증된다.

  ① **지금 무슨 상태인지 첫 줄에 직설로.** [게시 리듬 ↔ 반응 실측]에 게시 공백(마지막 게시로부터 N일)이 찍혀 있으면 **그것부터 그대로 말해라** — 운영자가 원하는 문장은 이 꼴이다: '올리던 리듬이 사흘째 끊겼고, 그래서 조회가 터지는 게 멈춰 있는 실황이다. 대신 팔로워는 유지되는 중.' 지표 탓·시장 탓으로 돌리거나 '아직 하루가 안 찼으니 최종치는 아니다' 류로 뭉개지 마라(그건 원인을 아는데 안 말하는 것이다).
  ② **계정 축과 팔로워 축을 갈라서** 각각 한 줄 — 한쪽이 꺼져도 다른 쪽은 유지될 수 있고, 그 어긋남 자체가 이 창의 정보다(순증감 수치를 그대로 인용).
  ③ **창 안 게시물을 하나하나 실명으로.** [최근 게시물]의 캡션 일부·조회·중앙 대비 배수·**나이**를 붙여 '이건 다 컸고 / 이건 아직 크는 중 / 이건 중앙의 절반에서 멈췄다'로 **개별 판정**하라. 창에 새 게시물이 없으면 '직전 게시물들이 지금 어디까지 와서 멈춰 있나'를 같은 방식으로 짚어라 — 창이 비었다고 할 말이 없는 게 아니다.
  ④ 사흘 흐름이 7일·28일 추세와 같은 방향인지 어긋나는지(나무 vs 숲 대조) + 이 창에서만 보이는 시사점 한 줄.
- [7일] = 이번 주 벌어진 일. ⚠ **운영자 260809 2차 개정 — [3일]의 실황 문법을 이 창에도 그대로 적용한다**(같은 겉핥기가 여기 남아 있었다). **6~9줄**:
  ① 최근 7일이 전 기간 평균 대비 어떤지 + **그 주의 게시 리듬**(며칠 올렸고 며칠 비었나)을 한 줄에.
  ② **그 주 게시물을 한 장씩** — [최근 게시물]의 조회·**중앙 대비 배수**·지문으로 '이건 중앙을 넘겼다 / 이건 절반에서 멈췄다'를 **개별 판정**하고, 그중 제일 잘 된 것과 제일 안 된 것의 **차이가 뭐였는지**를 데이터로 대라(포맷·소재·문장 결). 소재 사건 확인이 필요하면 WebSearch로 확인된 것만 한 줄.
  ③ **계정 축 ↔ 팔로워 축**을 갈라서 각각(순증 합·마이너스 날 유무).
  ④ [3일]과 같은 말 반복 금지 — 사흘에선 안 보이던 게 이레에선 보이는 지점(예: 사흘은 개점휴업인데 이레로 보면 앞부분에 몰아 올렸다)을 짚어라 + 이 창의 시사점 한 줄.
- [28일] = 최근 한 달의 파도. ⚠ **운영자 260809 2차 개정 — 근거는 [주 단위 리듬(최근 4주)] 블록을 그대로 쓴다**(30일 줄을 손으로 세지 마라 = 오산·누락 위험). **5~7줄**:
  ① **주 대 주로 읽어라** — 4개 주 블록을 나란히 놓고 게시 수·빈 날·도달 중앙·팔로워 순증·**중앙 초과 장수**가 어떻게 움직였는지. 특히 **중앙 초과 장수**가 그 주의 성패를 가르는 값이다(게시를 많이 해도 크게 터진 장이 0이면 다른 주다).
  ② **공백을 평소 리듬과 대조** — 이 채널은 원래 빈 날이 많다. 그러니 '공백이 있다'가 아니라 **'이번 공백이 어디에 붙었나'**(잘 터진 주 뒤인가, 이미 식은 주 뒤인가)가 정보다.
  ③ 전환점이 있으면 날짜로 콕 + 그날 올린 것 실명([최근 30일 일일 계정 실측]의 '올린 것' 칸).
  ④ [7일]에서 한 말 반복 금지 — 한 달로 봐야만 보이는 것 + 시사점 한 줄.
- [3개월] = 중기 서사. ⚠ **운영자 260809 3차 개정 — [3일]·[7일]·[28일]과 같은 리듬을 여기도 적용한다**(이 창만 뭉뚱그리면 사다리가 거기서 끊긴다). **6~8줄**:
  ① [성장 3기]를 **기 대 기로** 세워라(조회 중앙·1천뷰당 공유/저장/댓글/좋아요가 기마다 어떻게 갈렸는지) — [28일]이 주 대 주였다면 여기는 기 대 기다.
  ② **각 기를 대표하는 게시물을 실명·링크로** 한 장씩 집어 그 기의 성격을 보여줘라([TOP 게시물]의 시기·지문 활용).
  ③ [운영자 관측 변곡 이벤트]와 맞물려 **지금이 어느 기의 어디쯤**인지 + 🚪확장문이 있으면 '팔로워 밖에서 새 표본이 들어오는 문'으로.
  ④ 앞 창들에서 한 말 반복 금지 — 석 달로 봐야만 보이는 것(기의 교체·체질 변화) + 시사점 한 줄.
- [전체] = **전체 기간에 대한 분석 요약(총론 아님 · 운영자 260714 '전체는 기간 분석에 집중·디테일하게')** — 처음부터 지금까지 무슨 일이 있었는지 성장 스토리를 수치로 총정리(초등학생도 '아, 이렇게 커왔구나') + '지금까지의 내용' 느낌 + *바로 이후 정도*까지의 예측(먼 미래 방향은 여기 쓰지 마라 = 총론 역할). 관리 전략 '→ '로 시작하는 줄 3~4줄(각 줄 = '→ 무엇을 하자 — 근거(수치)' 꼴 · 예: '→ 릴스 비중을 더 올리자 — 릴스가 피드보다 1천뷰당 공유가 ×1.7 높다.' · 뻔한 일반론 금지 — 데이터서만 나올 말로) + 맺음 한 줄. 7~10줄. ⚠ '→ ' 줄들은 앱이 '클로신의 제안' 블록으로 자동 분리 표시한다 — '전략은 이렇다:' 류 예고 없이 줄만, 맺음은 '→ ' 없이.
- ⚠ [누적 지식 라이브러리]에 **[⑥ 말은 반복했는데 한 번도 안 옮겨진 축]**이 있으면, 이 섹션의 '→ ' 전략 줄 **하나는 반드시** 그 축을 **오늘의 행동 한 개**로 좁혀 써라 — 방침이 아니라 행동이다. '릴스 비중을 올리자'(방침 · 이미 여러 번 말했고 안 옮겨졌다 = 금지) 대신 '오늘 첫 장은 릴스 평서로 걸자'(행동)처럼 **무엇을·언제·어떤 모양으로**가 한 줄에 들어가야 한다. 반복된 방침을 또 적는 건 다섯 번째 반복일 뿐이다.
- [총론] = **채널 전체를 아우르는 비전·방향성·미션(운영자 260714 '짧게 3개월 길게 12개월·먼 날들까지·큰 그림·회초리 아닌 나침반')** — 모든 기간 분석을 관통해 '이 채널이 무엇이고 어디로 가야 하는가'를 제시하라: 정체성(무슨 채널로 자리잡았나)·나아갈 큰 방향(3~12개월)·핵심 미션. ⚠ **운영자 260808 개정 — 총론이 얇아졌다는 실측 지적('실제로 어떤 게시물이 어땠고, 이 정도는 돼야 · 디테일이 너무 빠져서 남의 인스타 뒤지는 느낌')에 따라 아래 3문단을 필수로 넣는다.** 구판이 '개별 기간 수치를 나열하지 말라'고만 해서 모델이 게시물 실명·근거를 통째로 뺐고, 그 결과 정체성 선언문만 남아 읽을 게 없어졌다. ① **임팩트 문단(필수)** = 크게 터진 게시물 **1~2장을 실명으로 콕**(캡션 일부·조회·포맷) → **왜 터졌나**를 채널 안 근거(1천뷰당 공유·저장·지문 등 수치)로 대라. ② **바깥 시류 문단(필수·데이터에 [⑦ …]이 있을 때)** = 그 게시물이 올라간 시각에 밖에서 돌던 대세 키워드를 보고 '이 흐름을 탄 것 같다 / 무관하게 자체 사건으로 터졌다'를 **네가 판정해 문장으로** 써라. 탔다고 보면 무엇이 어떻게 겹쳤는지 쓰고, 알고리즘 영향은 '~로 보인다·~쪽에 가깝다' 추정 어미로만(단정 금지 · 못 잇겠으면 '이건 시류와 무관한 자체 사건이었다'고 정직하게). ⚠ 억지로 잇지 마라 — 없는 인과를 지어내는 게 얇은 총론보다 나쁘다. ③ **그래서 어떤 흐름을 가져갈까 문단(필수)** = ①②에서 나온 성질을 앞으로 어떻게 반복 가능한 흐름으로 만들지(소재 결·문장 톤·타이밍) 방향으로. 그 위에 정체성·미션 산문을 얹어 닫는다. **맨 마지막 줄은 '→ '로 여는 단 한 줄 결론**(운영자 260717 필수): '→ 그래서 무엇을 — 한 문장 방향' · **이 마지막 1줄에만** 수치 근거·여러 줄 전략 나열을 금지한다(방향 한 문장 = 응축) — 본문 ①②③은 수치·게시물 실명을 **적극적으로 써라**. '전체'가 지금까지의 수치 총정리+실행 전략이라면, 총론은 '왜 그게 됐나(안+밖)' + 멀리 보는 나침반이다 — 둘은 다른 글이되 총론도 근거를 갖는다. **10~14줄**(마지막 '→' 결론 1줄 포함).
- 각 섹션 = 그 기간 창 데이터([기간 창별 실측]·일일 흐름·TOP·최근 게시물)가 근거([총론]만 전 기간 종합). 섹션 간 같은 문장 복붙 금지 — 창이 넓어질수록 시야도 넓어지게, 앞 창과의 시야 차이(같은 데이터가 달리 읽히는 지점)를 살려라. ⚠ [전체](디테일 분석)와 [총론](먼 방향·비전)은 반드시 다른 글 — 총론에 수치 분석을, 전체에 먼 미래 비전을 넣지 마라.

[근거·신뢰선 — 절대 준수]
- ⚠ **게시물을 말할 땐 반드시 링크로 건다(운영자 260809 3차 · 전 섹션 공통)** — 데이터의 게시물 줄에 「· 링크 <주소>」가 붙어 있다. 그 게시물을 문장에서 언급하는 **첫 자리**에 마크다운 링크로 써라: \`[«🏠 폐버스가 청년 임시주택?»](https://www.instagram.com/p/…)\` 꼴. 앱이 이걸 **골드·이탤릭 참조**로 그려서 운영자가 그 자리에서 실물을 열어볼 수 있다.
  · 링크 텍스트 = 캡션 앞부분(길면 잘라라 · 겹화살괄호 «» 안에 넣는 게 이 브리핑의 관례).
  · 링크 안에 별표 강조를 겹치지 마라(\`[**제목**](url)\` 금지 — 링크는 그 자체로 이미 눈에 띄는 층이다). 수치·판정어는 링크 **밖**에서 강조해라.
  · 같은 게시물을 한 섹션에서 여러 번 말하면 **처음 한 번만** 링크(반복 링크 = 지저분하다).
  · 데이터에 링크가 '—'인 게시물은 링크 없이 캡션만.
- 수치는 데이터에 적힌 표기 그대로(만/억 단위 유지). 데이터에 없는 수치·사건 날조 절대 금지.
- share_pm 같은 원어·전문용어를 그대로 노출하지 마라 — '1천뷰당 공유'처럼 쉬운 말로. 어려운 개념은 반 줄로 풀어서.
- 외부 사건은 WebSearch/WebFetch로 확인한 것만. 못 찾으면 사건 언급 없이 지표만 담백하게.
- [팔로워 접속 피크]·[팔로워 활동 시간 분포]가 데이터에 있으면 게시 타이밍 전략의 근거로 살려라 — 특히 [전체 총론] 전략 줄 후보(예: '→ 피크인 18~21시에 맞춰 올리자 — 팔로워 활동이 이 구간에 가장 높다'). 이건 관객이 언제 깨어 있느냐라 게시 습관과 무관한 데이터다.
- 반대로 요일 우열('무슨 요일이 잘 터진다')은 [게시 요일 분포]의 ⚠딱지대로 단정 금지 — 게시가 몰린 요일은 성과도 같이 부풀어 보인다. 요일 얘기가 필요하면 '게시가 몰려서 그렇게 보일 수 있다'는 유보를 같이 달아라. 시간대 이야기까지만 확언한다.

[신뢰 게이트 — 거의 확실한 것만 해석·방향을 말한다(운영자 260715 · 전 섹션 공통 최상위 규칙)]
- 해석('~때문이다')과 방향성('~하자', '→ ' 전략 줄 전부)은 **거의 확실 등급 데이터에서만** 꺼낸다. 거의 확실 = 표본 충분한 실측 수치(상관·중앙값·API 실측 인구통계·접속 피크·[게시-팔로워 인과 실측]·주제/포맷 중앙값·확장문 같은 규칙 기반 딱지).
- 다음은 해석·방향의 **단독 근거 금지**: '가설'·'단정 금지'·'자가 보고' 딱지가 붙은 것(협착의 게시물 단위 관계·성향 메모), (표본부족)/low_sample 버킷, 요일 우열(교란 딱지), 결측(—) 구간. 언급하려면 '아직 가설이다/표본이 모자라다'를 문장 안에 명시하고, 방향 제안으로 잇고 싶으면 반드시 거의 확실 등급 근거를 같이 세워라.
- 애매하면 해석을 지어내지 말고 '이건 데이터로 아직 모른다'고 말해라 — 그게 회초리의 신뢰선이다. 확실 7할을 또렷하게 > 불확실 10할을 그럴듯하게.

[회초리 — 잘한 건 콕 집고, 근거로만 때려라(운영자 260715)]
- ⚠ **완곡어법 금지(운영자 260809 '너무 돌려 말하니까 유의미한 인사이트가 안 나온다') — 전 섹션 공통.** 원인이 운영자 자신의 운영(게시 공백·리듬 하락)에 있으면 **그 문장을 그대로 쓴다**: '올린 게 없어서 멈춰 있다'가 정답인 자리에 '외부 유입이 상대적으로 둔화됐다' 같은 말을 놓지 마라. 데이터가 가리키는 원인을 알면서 부드럽게 감싸는 순간 그 브리핑은 쓸모가 0이 된다 — 운영자는 위로가 아니라 실황을 보려고 이걸 연다. 단, 직설은 **근거와 한 몸**이다(수치 없이 훈계만 = 금지 · 신뢰 게이트는 그대로 적용).
- 잘 터진 게시물 1~2개는 반드시: ① '이 부분이 터졌다' 콕(어느 게시물·수치) → ② 왜 터졌나 — 주제가 그 시기 흐름(사건·시류)을 탔는지 진단(외부 사건은 WebSearch로 확인된 것만·못 찾으면 지표만) → ③ 그 게시물의 '지문'으로 반응한 표본을 그려라(공유형 = 지인에게 퍼나르는 표본 · 저장형 = 모아두고 다시 보는 표본 · 댓글형 = 참전하는 표본) → ④ '~를 활용하면 더 좋겠다' 다음 수 1개까지. 칭찬으로 끝내지 말고 반드시 ④까지.
- '그냥 자주 올려라' 류 일반 훈수 전면 금지 — 모든 지적·권고에는 [게시-팔로워 인과 실측]이나 지표 수치가 근거로 붙어야 한다(핵심 실측: 팔로워는 게시 *행위*가 아니라 조회가 터진 날 는다 — 다만 안 올리면 터질 것도 없다. [게시-팔로워 인과 실측]의 상관·휴식일 vs 게시일 중앙값을 그대로 인용해 근거를 대라).
- 🚪확장문 딱지 게시물이 있으면 '지금 팔로워 밖에서 새 표본이 들어오는 문'으로 짚어라 — 특히 [3개월]·[총론]에서 채널이 커지는 방향의 근거로.
- [알고리즘 협착] 블록이 있으면 정치·편향 소재 다룰 때의 확산 페널티 근거로 써라 — 단 '가설+부분 실측'이니 단정하지 말고 '네가 관측했고 데이터도 그 방향(좋아요 최고·조회 최저권)' 꼴로. 대안 제시 = 확산형 소재(사회·양쪽이 갈리는 구도)와 협착형 소재(한쪽만 환호)의 구분을 게시물 콕 집어.
- [팔로워 표본 — 운영자 자가 보고]의 성향 메모는 운영자의 추정(데이터 아님): 다수 성향은 소재 감도 참고까지만 쓰고, 특정 성향 몰빵 권고·채널을 정치 성향 채널로 규정하는 표현은 금지. 성향이 섞인 표본 자체가 이 채널의 강점(명시적 표방 없이 시작·문화 혼합 출발)이니 그 균형을 지키는 방향으로 제안하라 — 성향 밖 표본이 반응한 게시물(🚪)이 바로 그 균형의 증거다.

[말투 — 살아있게(팬픽·웹소설 문체)]
친근한 소식통 톤. 단문으로 툭툭 끊되 길이 섞기 · 종결을 '~다'에 가두지 말고 '~더라(현장 톤)·~네(발견)·~거든(배경)'을 1~2번 · 수치는 끊어 던지고 자기정정으로 강조('97만 조회. 평소의 세 배.') · '무려·심지어·하필·그것도' 훅 · 대시(—)·쉼표로 뜸. 금지: 느낌표 떡칠·하트·2인칭 호칭(여러분/너)·신파·오글·말줄임(...) 남발.

[형식]
- 응답 첫 줄 = [3일] 마커 그 자체. 그 위에 '확인됐어/찾아봤어/이야기 풀게' 류 준비·확인 멘트, '---' 같은 구분선, 서두 사족 전면 금지(그건 네 사고 과정이지 브리핑이 아니다).
- 강조는 2층: 제일 크게 튄 수치·전환점·그 판을 한마디로 규정하는 핵심어 = *별표 하나*(1층 = 강조색 · 진짜 특별한 것만 · 예: '248만' 같은 튄 수치, 채널 정체성·미션의 핵심 명사) · 그다음 눈이 먼저 가야 할 핵심 명사·동사구 = **별표 둘**(2층 = 볼드만·강조색 아님). ⚠ **밀도 개정(운영자 260809 3차 \"내용의 포인트가 되는 부분은 볼드체, 정말 중요한 부분은 강조색\")** = **2층(볼드)은 그 섹션의 '포인트가 되는 말'마다 붙인다 — 섹션당 3~5개**(판정어·전환을 만든 명사구·수치의 의미를 규정하는 말 · 예: **장수가 아니라 큰 장의 개수** · **끝난 일은 지나가고 진행 중인 일만 퍼나른다**). 볼드 1~2개로 끝나는 섹션 = 실패(읽는 사람 눈이 앉을 자리가 없다). **1층(강조색)은 섹션당 1개**, 그 판에서 제일 중요한 단 하나(제일 크게 튄 수치 또는 그 창을 한마디로 규정하는 말)에만 — 두 개 이상 = 강조가 죽는다. 긴 [전체]·[총론]은 2층 5~7개 — 특히 [총론]은 제일 길고 중요한 판인데 볼드가 밋밋하면 실패다: 정체성·방향·미션을 이루는 키워드(명사구)를 중간중간 골고루 볼드로 짚고, 그중 채널을 한마디로 규정하는 말 하나는 1층 강조색으로 올려라(볼드 2개·강조색 0으로 밋밋하게 두지 마라). 별표 사이 줄바꿈 금지 · 별표 짝 반드시 닫기.
- 헤더·번호목록·마크다운 제목·이모지 금지(섹션 마커 5줄과 전략 줄의 '→ '만 예외).

${LIB_BLOCK}
[데이터 = 이 채널의 실제 지표]
$BODY"

claude_preflight "$MODEL" || true   # 죽은 활성계정 침묵 행 공회전 소거(운영자 260717 · 산 계정 = 수초 · 전멸 = 본선 강행 fail-soft) — 핑 소요는 벽시계 캡 안에서 소화
out=""; _to_tried=0   # _to_tried = 타임아웃(rc=124) 강제 계정 전환 1회 소진 플래그(analyze.sh 계승)
for _try in 1 2 3 4; do
  # 누적 벽시계 캡(평의회6 260714 · analyze.sh ANALYZE_JOB_DEADLINE 관용구 계승 · 260717 예산 재산정): 정상 생성 실측 ~9분(260714 성공 런 9m07s)이라
  # 종전 시도당 600s = 무여유 → v9 프롬프트 비대 후 시도1 타임아웃 → 재시도 중 잡 20분 하드킬 3연속(cancelled · run 29455365666 실측) = 브리프 이틀 정지 사고.
  # 재산정 = 시도당 900s · 캡 960s(풀타임아웃 후 재시도 1회 보장: 시도1 종료 ~905s < 960) · 최악 959+900=31분 < 잡 timeout 35분 = fail-soft·커밋 스텝 생존. 평상시 무영향(쿼터 실패 = 초 단위 반환).
  [ "$SECONDS" -gt 960 ] && { echo "::warning::chan-brief 시간 예산 소진(${SECONDS}s>960s) — 직전 brief 유지(fail-soft)"; exit 0; }
  out="$(printf '%s' "$PROMPT" | METER_SRC=chan-brief METER_MODEL="$MODEL" METER_EFFORT=high claude_meter 900 --model "$MODEL" --effort high --safe-mode --max-turns 8 \
    --allowedTools "WebFetch,WebSearch" \
    --disallowedTools "Bash,Edit,Write,Read,Glob,Grep,Task,NotebookEdit,TodoWrite" 2>/tmp/chanbrief.err)"; rc=$?
  if [ $rc -ne 0 ] || [ -z "$out" ]; then
    if claude_failover "$out$(cat /tmp/chanbrief.err 2>/dev/null)"; then continue; fi   # 쿼터 = 4계정 체인 1단씩(§📰-f)
    # 타임아웃(rc=124)은 출력이 비어 is_quota가 못 잡는 사각지대 → *딱 1회* 강제 계정 전환 후 재시도(analyze.sh:292 계승 · 운영자 260714 Q12 "막히면 대기 말고 바로 다른 계정 · 몇 번 돌리면 해결"). 서브2 지연(rc=124)에서 멈춰 서브3 미도달하던 것 봉합. 1회 제한 = 타임아웃 대개 입력바운드라 무한 전환은 시간·쿼터만 소진(평의회 260704).
    if [ $rc -eq 124 ] && [ "$_to_tried" = "0" ] && claude_failover_force; then _to_tried=1; continue; fi
    echo "::warning::chan-brief 생성 실패(rc=$rc) — 직전 brief 유지(fail-soft)"; exit 0
  fi
  break
done
[ -z "$out" ] && { echo "::warning::chan-brief 빈 출력 — 직전 유지"; exit 0; }

BRIEF_TEXT="$out" BRIEF_SHA="$SHA" python3 - <<'PY'
import json, os, datetime, re
KST = datetime.timezone(datetime.timedelta(hours=9))
raw = (os.environ.get('BRIEF_TEXT') or '').strip()
# 줄바꿈 보존(요점별 개행 · sns_brief 계승) — 줄별 trim + 빈줄 3+ → 1 + 독해 상한(5부 구성 = 길어짐 · 과출력 가드 2000→9000)
# + 단독 구분선(---·***) 줄 제거(결정론 — 프롬프트 금지의 안전망 · 수평선은 tbrief에서 맨 텍스트로 노출) · 구분선 앞 서두 프리앰블은 프롬프트 가드가 담당(카나리아 1차 실측 봉합)
lines = [ln.rstrip() for ln in raw.replace('\r\n', '\n').split('\n') if not re.fullmatch(r'\s*[-*_]{3,}\s*', ln)]
t = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)).strip()[:9000]
# 기간 5부 파싱(운영자 260714 "7일·14일·28일·3개월·전체 총론 구분") — 마커 단독 줄 분할 · 마커 미출력/1개뿐 = sections 생략 → 뷰어 fail-soft(전문 단일 렌더 = 구 스키마 하위호환)
SECS = [('d3', '3일'), ('d7', '7일'), ('d28', '28일'), ('m3', '3개월'), ('all', '전체'), ('overview', '총론')]   # v8 총론 분리(운영자 260714): all=전체기간 분석 / overview=비전·방향성·미션 큰그림 — 세그는 all까지, overview는 뷰어 (3)고정
parts = re.split(r'^\[(3일|7일|28일|3개월|전체|총론)\]\s*$', t, flags=re.M)
seen = {}
for i in range(1, len(parts) - 1, 2):
    seen.setdefault(parts[i], parts[i + 1].strip())
secs = [{'k': k, 'label': lb, 'text': seen[lb][:1800]} for k, lb in SECS if seen.get(lb)]
if secs and parts[0].strip():   # 첫 마커 위 잔여 서두(가드 뚫림 대비) = 첫 섹션에 흡수
    secs[0]['text'] = (parts[0].strip() + '\n' + secs[0]['text'])[:1800]
# 판단 이력 카드 = 화면 비노출로 전환(운영자 260809 "내가 볼 필요는 없음 · AI 요약을 진행하는 프로그램이 체킹하면 됨").
# 뷰어 소비처(libCard)를 걷었으므로 doc['lib'] 배송도 같이 걷는다 — 아무도 안 읽는 데이터를 굽는 건 이 레포가 반복해 지적한 죽은 원장 축이다.
# ⚠ 라이브러리 자신은 무접촉: brief_lib → LIB_BLOCK → PROMPT 경로가 이 파일 위쪽에 그대로 살아 있다(= 프로그램이 체킹하는 축).
doc = {'text': t[:6000], 'updated': datetime.datetime.now(KST).isoformat(timespec='seconds'),
       'src_hash': os.environ.get('BRIEF_SHA') or ''}
if len(secs) >= 2: doc['sections'] = secs
json.dump(doc, open('viewer/chan_brief.json', 'w', encoding='utf-8'), ensure_ascii=False)
# 인사이트 아카이브(운영자 260714 3차 "모으면 뭔가 나올수도") — 일자별 회차 축적 = 추이 비교·패턴 채굴 원료 · 같은 날 재생성 = 최신으로 교체 · 캡 180회차(파일 비대 가드) · 뷰어 미노출(겉면 불변)
import os.path
log = 'viewer/chan_brief_log.jsonl'
today = doc['updated'][:10]
rows = []
if os.path.exists(log):
    for ln in open(log, encoding='utf-8').read().splitlines():
        ln = ln.strip()
        if not ln: continue
        try:
            if json.loads(ln).get('date') != today: rows.append(ln)
        except Exception: pass
rows.append(json.dumps({'date': today, 'updated': doc['updated'], 'sections': secs if len(secs) >= 2 else None, 'text': None if len(secs) >= 2 else doc['text']}, ensure_ascii=False))
open(log, 'w', encoding='utf-8').write('\n'.join(rows[-180:]) + '\n')
print('chan-brief 저장:', len(t), '자', '·', len(secs), '섹션', '· 아카이브', len(rows[-180:]), '회차')
PY
echo "chan-brief: 갱신 완료($SHA)"
