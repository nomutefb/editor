#!/usr/bin/env python3
"""유튜브 숏폼(ys) 장면 영상 — 그록(grok-imagine-video) 장면 1개 = 클립 1개 · 클립 안 비트 2~4개(운영자 260928 «그록 = 9:16 전면» · 260929 «예전 비디오 제작 방식과 절충»).

  ys_grok.py <id> <plan.json> <timing.json> <img_dir> <outdir> <ratio 9:16|16:9>
  → outdir/s{i}.mp4(소리 트랙 제거) + outdir/vid.json {used, total, note, cost_usd, modes, plan_src}

설계(260928 조사 · 15초×4 연장 체인 비채택 = 장면 경계와 어긋나고 순차라 느리고 이을수록 화질이 떨어진다):
  · 장면 경계 = 나레이션 문단 경계 → 장면마다 독립 클립 + 컷. 클립 **안**은 감독 콜(ys_grok_plan)이 쓴 비트 시각표
    (`0-3s: MOTION. CAMERA.` = 예전 콘티 레인 grok_sb_video.vid_prompt 문법) — 한 클립 안에서 카메라가 2~4번 바뀐다.
  · 모드(장면마다) = ① 참조(r2v): 맥 GPT 가 그린 캐릭터 보드(hero.png) + 스토리보드(board.png)를 참조로 — 예전 콘티 레인과 같은
    「그림 몇 장을 전 클립이 공유」(운영자 260811 «의미 없이 열 몇 장 만드는 건 손해») · 화면 비율을 명시(크롭 0)
    ② 첫 프레임(i2v): 장면 그림 s{i}.png(옛 맥 드라이버) ③ 글→영상(t2v): 맥이 꺼져 있을 때.
  · 길이 = 장면 나레이션 + 0.5초 올림(1~15초) · 모자라면 렌더가 1.15배 이내 늦춤 + 마지막 프레임 멈춤.
  · 부정문 0(그록 정본 = 영상 축 비주얼 부정문 금지 · 부정어가 그것을 부른다) · 인물 대명사 0(정체문으로 지목).
  · 3발 동시 · 실패 장면만 1회 재시도(실패 호출 = 청구 0) · 검열·자격 실패 = 재시도 안 함.
  · 자격 = shared/grok_api.fresh_token(회전형 리프레시 · 되쓰기 = 그 모듈 몫) · 워크플로가 nm-grok-key 줄에 세운다(콘티 레인과 같은 줄).
전 경로 rc 0 — 못 만든 장면은 렌더가 그림·모션 그래픽으로 채운다(영상은 항상 나온다 · 사유는 note 로 화면까지).
"""
import json
import math
import re
import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'shared'))
PAD = 0.5
MAX_SEC = 15
PAR = int(os.environ.get('YS_GROK_PAR', '3'))
BUDGET = int(os.environ.get('YS_GROK_BUDGET', '1200'))   # 전체 마감(초) = 스텝 시간 벽(25분)보다 넉넉히 작게 — 넘기면 남은 장면은 그림·모션으로
_plock = threading.Lock()   # 진행 게시 = 한 번에 하나(ys_progress 임시 파일 경합 0)
STYLE = os.environ.get('YS_VID_STYLE', 'Korean webtoon animation style, clean line art, soft cel shading, muted palette')   # 맥 그림(웹툰체)과 같은 결 · 긍정형만
I2V = 'Keep the exact art style, character design and colors of the first frame.'   # 첫 프레임이 있으면 = 화풍 재서술 대신 「첫 프레임 그대로」
# 참조 정체문(예전 콘티 레인 SHEET_NOTE·SHEET_CLAUSE 계보) — 「이건 설계도지 화면이 아니다」를 못 박아 칸·시트가 화면으로 새지 않게
HERO_NOTE = 'a multi-angle identity reference for that person only; in the video the person appears once, filmed inside the scene'
BOARD_NOTE = ("the director's storyboard for the whole video, panels in reading order, read only for setting, look, palette and mood; "
              "camera framing comes from the timeline below; the finished video is one full-bleed camera view")   # 구도 출처 = 비트 하나(보드·장면 줄과 3중 충돌 = 모델이 평균낸다 · 평의회 260929)
SHOT_LEAD = re.compile(r'(?i)^(?:an?\s+|the\s+)?(?:extreme\s+|medium\s+|tight\s+|wide\s+|full\s+|low[- ]angle\s+|high[- ]angle\s+|overhead\s+|top[- ]down\s+)*'
                       r'(?:close[- ]?up|shot|view|angle|portrait|framing|still)\s+(?:of\s+)?')
LIPS = 'Lips closed and still.'   # 소리 = 트랙 제거 + 나레이션 → 입이 움직이면 립싱크처럼 보인다(예전 콘티 레인 sound_clause(False) 짝)
EMBED_MAX = int(os.environ.get('YS_GROK_EMBED_MAX') or '900000')   # 참조를 본문에 싣는 상한(예전 콘티 레인 실측 = 주소 방식은 xAI 쪽 받기가 끊겨 편이 죽었다)


def progress(id_, st, note='', p=None):
    a = [sys.executable, str(Path(__file__).with_name('ys_progress.py')), id_, 'vid', st, note]
    if p is not None:
        a.append(f'p={p:.3f}')
    with _plock:
        subprocess.run(a, check=False)


def seconds_for(dur):
    return max(1, min(MAX_SEC, int(math.ceil(float(dur or 0) + PAD))))


def timeline(beats):
    """비트 → `0-3s: MOTION. CAMERA. 3-7s: …` (비트 1개면 시각 없이 — 한 호흡에 눈금을 치면 끊어 그린다)."""
    multi, t, out = len(beats) > 1, 0, []
    for b in beats:
        body = ' '.join(x.rstrip('. ') + '.' for x in (b.get('motion') or '', b.get('camera') or '') if x.strip())
        if body:
            out.append(f"{t}-{t + int(b.get('sec') or 0)}s: {body}" if multi else body)
        t += int(b.get('sec') or 0)
    return ' '.join(out)


def prompt_for(sc, mode, hero_en='', beats=None, i=0, refs=()):
    """mode = r2v(참조: refs 순서 = 'hero'·'board') · i2v(첫 프레임) · t2v(글→영상). beats = 감독 비트(없으면 대본 motion 1개)."""
    beats = beats or [{'sec': 0, 'motion': (sc.get('motion') or '').strip() or 'Slow push-in; subtle ambient motion.', 'camera': ''}]
    tl = timeline(beats)
    if mode == 'i2v':   # 첫 프레임이 구도·화풍·얼굴을 이미 쥐었다 = 움직임만(구도 재서술은 그림과 싸운다)
        return f"{tl}{' ' + LIPS if hero_en and sc.get('hero') else ''} {I2V}"
    scene = ' '.join(str(sc.get('img') or sc.get('head') or '').split())[:220].rstrip('. ')
    hero_here = bool(hero_en and sc.get('hero'))
    lips = f' {LIPS}' if hero_here else ''
    who = f"The protagonist is {hero_en.rstrip('. ')}. " if hero_here else ''   # 주인공을 글로 정의(없으면 장면마다 다른 사람)
    if mode == 'r2v':
        parts = []
        for k, kind in enumerate(refs):
            if kind == 'hero':
                parts.append(f"<IMAGE_{k}> shows the protagonist, {hero_en.rstrip('. ')}, {HERO_NOTE}.")
            elif kind == 'board':
                hint = ' '.join(SHOT_LEAD.sub('', scene).split()[:8])
                parts.append(f"<IMAGE_{k}> shows {BOARD_NOTE}; this clip is panel {i + 1}" + (f" (the one showing {hint})." if hint else '.'))
        if 'hero' in refs:   # 잠금 = 사람 참조만(스토리보드를 잠그면 「칸을 그리지 마라」와 부딪친다)
            parts.append(f"Keep the protagonist's face, hair and wardrobe identical to <IMAGE_{list(refs).index('hero')}>.")
        elif who:            # 캐릭터 보드가 없으면 글 정의로라도(보드는 구도·분위기만 읽으라 했으니 얼굴 출처가 0이 된다)
            parts.insert(0, who.strip())
        place = SHOT_LEAD.sub('', scene)   # 장면 줄 = 장소·행동만(샷 크기는 비트가 정한다)
        return ' '.join(parts + [f"Scene: {place}." if place else '', tl + lips, STYLE + '.']).replace('  ', ' ').strip()
    return f"{who}{scene + '. ' if scene else ''}{tl}{lips} {STYLE}.".strip()


def embed(path, public=''):
    """참조 1장 → 본문에 실을 값(작으면 바이트 · 크면 JPEG 로 줄여서 · 줄이기 불가면 공개 주소 · 그것도 없으면 원바이트)."""
    raw = Path(path).read_bytes()
    if len(raw) <= EMBED_MAX:
        return raw
    try:
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert('RGB')
        side = 1280
        while True:
            if max(im.size) > side:
                r = side / float(max(im.size))
                im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, 'JPEG', quality=90, subsampling=0, optimize=True)   # CONTRACT: check_image_format — q90 단일
            if buf.tell() <= EMBED_MAX or side <= 640:
                break
            side = int(side * .8)
        if buf.tell() <= EMBED_MAX:
            return buf.getvalue()
    except Exception:  # noqa: BLE001  PIL 없음·깨진 그림 = 주소로
        pass
    return public or raw


def kill_tree(pattern):
    """명령줄에 pattern 이 든 프로세스와 그 자손 전부에 SIGTERM(대기 만료된 배경 감독 정리 · 평의회 260929)."""
    import signal
    mine, p = set(), os.getpid()   # 나와 내 조상(스텝 셸 등)은 제외 — 명령줄에 같은 글자가 들어 있어도 스스로를 죽이지 않게
    while p > 1 and p not in mine:
        mine.add(p)
        try:
            p = int(open(f'/proc/{p}/stat').read().rsplit(')', 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            break
    todo = [int(x) for x in subprocess.run(['pgrep', '-f', pattern], capture_output=True, text=True).stdout.split()]
    seen = set()
    while todo:
        p = todo.pop()
        if p in seen or p in mine:
            continue
        seen.add(p)
        todo += [int(x) for x in subprocess.run(['pgrep', '-P', str(p)], capture_output=True, text=True).stdout.split()]
    for p in seen:
        try:
            os.kill(p, signal.SIGTERM)
        except OSError:
            pass
    return len(seen)


def strip_audio(src, dst):
    """그록 자체 소리 = 버린다(나레이션·자막은 우리가 덮는다) · 영상 트랙은 재인코딩 없이."""
    r = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(src), '-an', '-c:v', 'copy', str(dst)], capture_output=True, text=True)
    return r.returncode == 0 and Path(dst).exists() and Path(dst).stat().st_size > 10240


def main(argv):
    if len(argv) < 7:
        print(__doc__, file=sys.stderr)
        return 2
    id_, plan, timing = argv[1], json.load(open(argv[2], encoding='utf-8')), json.load(open(argv[3], encoding='utf-8'))
    img_dir, out, ratio = Path(argv[4]), Path(argv[5]), argv[6] if argv[6] in ('9:16', '16:9') else '9:16'
    out.mkdir(parents=True, exist_ok=True)
    scenes = plan['scenes']
    total = len(scenes)

    info = {}

    def done(used, note, cost=0.0):
        with open(out / 'vid.json', 'w', encoding='utf-8') as f:
            json.dump({'used': used, 'total': total, 'note': note, 'cost_usd': round(cost, 3), **info}, f, ensure_ascii=False)
        print(f'장면 영상 {used}/{total} · 비용 ${cost:.2f} · {note}')
        return 0

    t_end = time.time() + BUDGET
    done(0, '그록 단계가 시간 안에 끝나지 못해 그림·모션 그래픽으로 채웠어(그록 서버 지연 추정).')   # 선기록 = 스텝이 시간 벽에 잘려도 사유가 남는다(끝나면 덮어쓴다)

    if not os.environ.get('XAI_REFRESH_TOKEN'):
        progress(id_, 'skip', '그록 자격 미등록')
        return done(0, '그록 자격(XAI_REFRESH_TOKEN)이 등록돼 있지 않아 그림·모션 그래픽으로 채웠어 — 관리자 설정이 필요해.')
    try:
        import grok_api
    except Exception as e:  # noqa: BLE001  코드·설치 문제
        progress(id_, 'skip', '그록 모듈 로드 실패')
        return done(0, f'그록 모듈을 불러오지 못해(코드·설치 문제) 그림·모션 그래픽으로 채웠어. ({type(e).__name__})')
    try:
        tok = grok_api.fresh_token()
    except Exception as e:  # noqa: BLE001  사유 3갈래 = 자격 죽음(사람이 다시 로그인) · 통로 막힘(요금제) · 외부 장애(잠시 후)
        why = str(e)[:100]
        if getattr(e, 'dead_auth', False):
            progress(id_, 'skip', '그록 자격 만료')
            return done(0, f'그록 로그인이 풀려 그림·모션 그래픽으로 채웠어 — 관리자가 그록 자격을 다시 등록해야 해. ({why})')
        if getattr(e, 'tier_blocked', False):
            progress(id_, 'skip', '그록 통로 막힘')
            return done(0, f'이 계정에 그록 영상 통로가 열려 있지 않아 그림·모션 그래픽으로 채웠어(요금제·권한 확인 필요). ({why})')
        progress(id_, 'skip', '그록 인증 서버 장애')
        return done(0, f'그록 인증 서버에 닿지 못해(외부 장애) 그림·모션 그래픽으로 채웠어 — 잠시 후 다시 해줘. ({why})')

    # 연출 비트 = 배경 감독 콜 산출(ys_grok_plan.sh → grokplan.json) · 없으면(콜 실패·미완) 대본 motion 비트 1개
    #   기다림 = 자격 확인 **뒤**(자격이 죽은 판에서 헛대기 0) · 진행 게시 · 만료되면 감독을 끈다(결과를 안 쓰는 Opus 콜·토큰 노출 0)
    import ys_grok_plan
    gp_path = Path(os.environ.get('YS_GROK_PLAN') or Path(argv[2]).with_name('grokplan.json'))
    done_mark = gp_path.with_name('grokplan.done')
    if not done_mark.exists() and gp_path.with_name('grokplan.bg').exists():   # 감독 스텝이 배경으로 띄웠다는 표지
        progress(id_, 'run', '연출 감독 기다리는 중', 0.01)
        w_end = time.time() + int(os.environ.get('YS_GROK_PLAN_WAIT') or '300')
        while not done_mark.exists() and time.time() < w_end:
            time.sleep(5)
        if not done_mark.exists():
            kill_tree('ys_grok_plan.sh')   # 감독 셸 + 그 아래 콜 전부(안쪽 timeout 은 자기 프로세스 그룹이라 그룹 kill 로는 안 죽는다)
    try:
        with open(gp_path, encoding='utf-8') as f:
            gp = json.load(f)
        assert len(gp.get('clips') or []) == total
    except Exception:  # noqa: BLE001  없음·깨짐 = 대체안
        gp = ys_grok_plan.build('', plan, timing)
    beats_of = {c['i']: c['beats'] for c in gp['clips']}
    # 참조 그림 = 맥 GPT 캐릭터 보드·스토리보드(ys_images 가 내려받음) — 있으면 전 장면 참조 모드
    hero_en = (plan.get('hero') or {}).get('en', '')
    pub = (os.environ.get('R2_PUBLIC_BASE') or '').rstrip('/')
    refs_raw = {}
    ref_on = os.environ.get('YS_GROK_REF', '1') != '0'   # A/B 레버(레포 변수 YS_GROK_REF=0 = 참조 모드 끔 → 첫 그림·글→영상 · 예전 콘티 SB_SHEET_REF 관례)
    for kind in ('hero', 'board') if ref_on else ():
        p = img_dir / f'{kind}.png'
        if p.exists() and p.stat().st_size > 2048 and not p.is_symlink():
            refs_raw[kind] = embed(p, f'{pub}/ys_img/{id_}/{kind}.png' if pub else '')
    if not hero_en:
        refs_raw.pop('hero', None)   # 정의문 없는 인물 참조 = 누구를 잠그는지 모른다
    first_frames = sum(1 for i in range(total) if (img_dir / f's{i}.png').exists())
    try:
        with open(img_dir / 'img.json', encoding='utf-8') as f:
            board_tried = bool(json.load(f).get('board'))   # 맥이 켜져 스토리보드를 시도했는데 못 받은 판 = 「맥 꺼짐」이 아니다
    except Exception:  # noqa: BLE001
        board_tried = False
    fill = '그림·모션 그래픽' if first_frames else '모션 그래픽'   # 보드 모드엔 장면 그림이 없다 = 빈 장면은 모션 그래픽만
    lead = ('참조 모드(' + ' + '.join(x for x, k in (('스토리보드', 'board'), ('캐릭터 보드', 'hero')) if k in refs_raw) + ')') if refs_raw \
        else (f'첫 그림 {first_frames}장' if first_frames else '글→영상')
    progress(id_, 'run', f'그록 {total}장면 발사 · {lead} · 비트 {sum(len(b) for b in beats_of.values())}개', 0.02)
    state = {'ok': 0, 'fin': 0, 'ref_bad': set(), 'ref_err': ''}
    costs, fails, t2v, modes, sent, hows = [], [], [], {}, {}, {}
    refs_url = {k: f'{pub}/ys_img/{id_}/{k}.png' for k in refs_raw} if pub else {}   # 바이트가 막히면 주소로(xAI 가 직접 받는다)

    def ladder(sc, img):
        """이 장면이 시도할 발사 사다리 — 참조(바이트) → 참조(공개 주소) → 캐릭터 보드 1장 → 첫 그림 → 글→영상(+1회 재시도).
        260929 실측 = 참조 2장 요청이 발사 단계에서 거절(5/7장면) · 예전 콘티 레인 = 몸집 거절이면 바이트↔주소 전환 → 같은 계보.
        한 장면에서 거절된 사다리 칸은 전 장면 공용 표지(ref_bad)에 올라 남은 장면은 그 칸을 건너뛴다(같은 거절 반복 0)."""
        kinds = (('hero',) if sc.get('hero') and 'hero' in refs_raw else ()) + (('board',) if 'board' in refs_raw else ())   # 주인공 없는 장면 = 인물 참조를 안 싣는다(실으면 사람을 넣는다)
        steps = []
        if kinds:
            steps.append(('r2v', 'bytes', kinds))
            if pub:
                steps.append(('r2v', 'url', kinds))
            if len(kinds) == 2:
                steps.append(('r2v', 'bytes', ('hero',)))   # 두 장이 막히면 얼굴 한 장만(정체 우선 · 화풍은 글 STYLE)
        steps = [x for x in steps if x not in state['ref_bad']]
        if img.exists() and img.stat().st_size > 2048:
            steps.append(('i2v', '', ()))
        steps += [('t2v', '', ()), ('t2v', '', ())]
        return steps

    def one(i):
        sc = scenes[i]
        img = img_dir / f's{i}.png'
        sec = seconds_for(timing['scenes'][i].get('dur'))
        last, first, no_ref = '', True, False
        for mode, how, kinds in ladder(sc, img):
            if mode == 'r2v' and no_ref:
                continue
            left = t_end - time.time()
            if left < 150:   # 마감 임박 = 새 발사 안 함(발사 120초 + 받기 여유)
                last = last or '그록 마감 시간 초과'
                break
            if not first and mode != 'r2v':
                time.sleep(4)
            first = False
            refs = None
            if mode == 'r2v':
                refs = [refs_raw[k] if how == 'bytes' else refs_url[k] for k in kinds]
            image = img.read_bytes() if mode == 'i2v' else None
            modes[i] = mode
            if mode == 't2v' and i not in t2v:
                t2v.append(i)
            # 첫 프레임 = 구도·조명을 그림이 쥐었다 → 대본 움직임만(감독 비트의 샷 크기·조명은 그림과 싸운다)
            prompt = prompt_for(sc, mode, hero_en, beats_of.get(i) if mode != 'i2v' else None, i, kinds)
            try:
                sent[i] = prompt[:900]   # 실제로 나간 문장(판이 끝난 뒤 되짚기 · 예전 콘티 rec["prompt"] 선례)
                rid = grok_api.start_video(prompt, token=tok, ratio=ratio, image=image, refs=refs, seconds=sec)
                v = grok_api.wait_video(rid, token=tok, max_sec=max(30, int(left - 120)))
                costs.append(float(v.get('cost_usd') or 0))   # 청구 = 완료 시점(받기·소리 제거가 깨져도 값은 기록)
                raw = grok_api.fetch(v['url'])
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                    f.write(raw)
                ok = strip_audio(f.name, out / f's{i}.mp4')
                os.unlink(f.name)
                if not ok:
                    raise RuntimeError('받은 영상 파일이 깨졌어')
                if mode == 'r2v':
                    hows[i] = how + ('' if len(kinds) == len(refs_raw) or not sc.get('hero') else '·1장')
                state['ok'] += 1
                return
            except Exception as e:  # noqa: BLE001
                last = str(e)[:100]
                where = getattr(e, 'where', '')
                if getattr(e, 'dead_auth', False) or getattr(e, 'tier_blocked', False) or where == 'video-timeout':
                    break   # 자격·통로 막힘·서버 지연 = 같은 요청을 다시 쏴도 안 바뀐다
                if mode == 'r2v':
                    no_ref = where == 'video-moderated'   # 참조 그림째 검열 = 같은 그림 다른 방식도 막힌다 → 바로 첫 그림·글→영상
                    with _plock:
                        if where == 'video-start':
                            state['ref_bad'].add((mode, how, kinds))   # 발사 단계 거절(몸집·형식) = 그 사다리 칸은 전 장면 건너뛴다
                        if not state['ref_err']:
                            state['ref_err'] = f'{how}·{len(kinds)}장 · {where or type(e).__name__} · {last}'
                            print(f'  참조 발사 거절(첫 사유) = {state["ref_err"]}')   # 다음 판이 원인을 보게 로그에 남긴다
                    continue
                if where == 'video-moderated':
                    break   # 참조 없는 검열 = 같은 문장은 또 막힌다
        fails.append((i, last))

    def tick(fut):
        state['fin'] += 1
        progress(id_, 'run', f'장면 영상 {state["ok"]}/{total}', state['fin'] / total)

    with ThreadPoolExecutor(max_workers=PAR) as ex:
        futs = [ex.submit(one, i) for i in range(total)]
        for f in futs:
            f.add_done_callback(tick)
        for i, f in enumerate(futs):
            try:
                f.result()
            except Exception as e:  # noqa: BLE001  한 장면의 예상 밖 오류가 나머지를 못 죽인다
                fails.append((i, f'{type(e).__name__}: {str(e)[:80]}'))
    used = state['ok']
    cost = sum(costs)
    info.update({'modes': {m: sum(1 for v in modes.values() if v == m) for m in set(modes.values())}, 'plan_src': gp.get('src', ''),
                 'ref_how': {str(k): v for k, v in sorted(hows.items())}, 'ref_err': state['ref_err'],
                 'beats': sum(len(beats_of.get(i) or []) for i in range(total)), 'prompts': {str(k): v for k, v in sorted(sent.items())}})
    t2v_n = len([i for i, m in modes.items() if m == 't2v' and (out / f's{i}.mp4').exists()])
    if state['ref_err']:
        print(f"  참조 사다리 결과 = {info.get('ref_how') or '참조 성공 0'} · 거절 칸 {len(state['ref_bad'])}")
    t2v_note = '' if not t2v_n else (f' · 참조가 막힌 {t2v_n}장면은 글→영상' if refs_raw
                                     else ' · 스토리보드를 못 받아 글→영상으로 만들었어' if board_tried
                                     else ' · 맥이 꺼져 있어 첫 그림 없이 글→영상으로 만들었어' if not first_frames
                                     else f' · 첫 그림이 없는 {t2v_n}장면은 글→영상')
    t2v_note = (f' · {lead}' if refs_raw else '') + (' · 연출 비트 = 대본 움직임(감독 콜 없음)' if gp.get('src') != 'director' else '') + t2v_note
    if used == total:
        progress(id_, 'done', f'장면 영상 {used}장면')
        return done(used, f'그록 영상 {used}장면{t2v_note}', cost)
    fails.sort()
    why = '; '.join(f'장면 {i + 1}: {w}' for i, w in fails[:3])
    progress(id_, 'done', f'장면 영상 {used}/{total}')
    return done(used, f'그록 영상 {used}/{total}장면만 받았어 — 나머지는 {fill}으로 채웠어{t2v_note}. ({why})', cost)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
