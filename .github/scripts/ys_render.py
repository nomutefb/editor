#!/usr/bin/env python3
"""유튜브 숏폼(ys) 렌더 — plan.json + 나레이션 타이밍 → 9:16 mp4 · 포스터 · 인포그래픽 PNG.

  ys_render.py <plan.json> <timing.json> <meta.json> <outdir> [--img-dir DIR] [--vid-dir DIR] [--font pretendard|gothic|barun]
               [--ratio 9:16|16:9] [--subbg on|off] [--subop 0~100]

  산출 = outdir/short.mp4 · outdir/poster.jpg · outdir/infographic.png · outdir/render.json(집계)
  장면 = 화면 층(헤드리스 Chromium) + 문장 자막 오버레이 + 장면 나레이션 → 장면 클립 → 이어붙이기.
  장면 화면 = 전부 화면 전체 + 자막만(운영자 260928 «GPT 도 화면 전체 · 9:16 로 제작 · 화면 안 멘트 안 쓰게» — 태그·큰 글자·칩·쪽수 없음):
    --vid-dir 에 s{i}.mp4 가 있으면 = 그록 영상 전면(꽉 채움)
    --img-dir 에 s{i}.png|jpg 가 있으면 = 맥 Codex 그림 전면 + 느린 확대 · --depth on 이면 그 그림을 전면 2.5D 입체 시차 영상으로(ys_depth.py)
    둘 다 없으면 = 모션 그래픽 = 화면 글자 없이 자막 위 무대 전체(운영자 260928) — --motion motion.json(Opus 모션 디자이너) 장면이면 그 코드,
      없거나 검문 실패면 틀 도식(ys_mg · 장면 mg 사양)

디자인 값은 창작하지 않는다 — viewer/index.html `:root` 원문을 그대로 인라인(mg_render.root_tokens 계승)하고
var(--bg)·var(--fg)·var(--mut)·var(--accent)·var(--line)만 쓴다. 폰트 = assets/fonts/pretendard.woff2(정본 사본 0).
fail 정책: 장면 하나라도 못 만들면 rc 1(부분 영상 납품 금지 — 나레이션과 화면이 어긋난 영상은 어색함의 몸통).
"""
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mg_render import root_tokens   # noqa: E402  디자인 토큰 SSOT 추출기(값 창작 0)
import ys_mg   # noqa: E402  장면 모션 그래픽(도식 8종 · 프레임 구동 캡처)
import ys_motion   # noqa: E402  모션 디자이너 산출(motion.json) · 무대 크기(ys_depth = 입체 분기 안에서만 늦게 부른다 = numpy 없는 러너에서도 나머지 방식이 산다)

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / 'assets' / 'fonts' / 'pretendard.woff2'
W, H, FPS = 1080, 1920, 30
PAD = 0.5          # 장면 꼬리 여백(초) — 다음 장면 전 숨
ZOOM = 0.035       # 장면 동안 느린 확대 비율
CAP_MAX = 30       # 자막 한 덩이 최대 글자(넘으면 가운데 가까운 띄어쓰기에서 둘로 나누고 시간은 글자 비율)
# 폰트 3종(운영자 260928 "프리텐다드·노토산스·나눔바른고딕 · 기본 프리텐다드") — 키 = 자막기(ly_burn FONT_FAMILY) 동일 키.
#   프리텐다드 = 레포 정본 파일(@font-face) · 노토 산스·나눔바른고딕 = 러너 apt 시스템 폰트(fonts-noto-cjk · fonts-nanum) 패밀리명.
FONTS = {'pretendard': 'NMP', 'gothic': "'Noto Sans CJK KR'", 'barun': "'NanumBarunGothic'"}
FAMILY = FONTS['pretendard']
LAND = False        # 16:9 가로(운영자 260928 «기본 9:16 · 16:9 선택»)
SUB_BG = True       # 자막 배경 점등(기본 켬)
SUB_OP = 1.0        # 자막 배경 불투명도(기본 100%)


def esc(s):
    return html.escape(str(s or ''))


def br(s):
    return '<br>'.join(esc(x) for x in str(s or '').split('\n'))


def fit(text, cap_px, width=920, ratio=1.0):
    """줄 최대 글자 수 기준 글자 크기 — 한글 1자 ≈ 1em 폭(보수적) · 상한 cap_px."""
    longest = max((len(x) for x in str(text or '').split('\n')), default=1) or 1
    return int(min(cap_px, width * ratio / longest))


def split_caption(text, a, z, cap=CAP_MAX):
    """긴 문장 = 가운데 가까운 띄어쓰기에서 재귀 분할 · 시간은 글자 수 비율로 나눈다."""
    text = text.strip()
    if len(text) <= cap or ' ' not in text:
        return [(a, z, text)]
    mid = len(text) // 2
    spaces = [m.start() for m in re.finditer(' ', text)]
    cut = min(spaces, key=lambda p: abs(p - mid))
    left, right = text[:cut].strip(), text[cut:].strip()
    t = a + (z - a) * len(left) / max(1, len(left) + len(right))
    return split_caption(left, a, t, cap) + split_caption(right, t, z, cap)


def base_css(tokens):
    return f"""{tokens}
@font-face{{font-family:NMP;src:url('file://{FONT}') format('woff2');font-weight:100 900}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;font-family:{FAMILY},'Noto Sans CJK KR',sans-serif;color:var(--fg);-webkit-font-smoothing:antialiased;word-break:keep-all}}
.pill{{display:inline-block;padding:14px 28px;border-radius:999px;border:2px solid rgba(var(--accent-rgb),.45);color:var(--accent);font-size:34px;font-weight:700;letter-spacing:-.5px}}
.chip{{display:inline-block;padding:14px 26px;border-radius:16px;background:rgba(255,255,255,.06);border:1px solid var(--line);font-size:36px;font-weight:600;margin:0 12px 12px 0}}
.acc{{color:var(--accent)}}
"""


def _shade(credit):
    """전면 장면 공용 층(css, body) = 아래 어둠막(자막 가독) + 마지막 장면만 위 출처 한 줄.
    화면 문구(태그·큰 글자·보조·칩·쪽수) 없음(운영자 260928 «GPT 도 화면 전체 · 화면 안 멘트 안 쓰게»)."""
    css = (f".st{{position:absolute;left:0;right:0;top:0;height:{int(H * .14)}px;background:linear-gradient(180deg,rgba(0,0,0,.5),transparent)}}"
           f".sb{{position:absolute;left:0;right:0;bottom:0;height:{int(H * .36)}px;background:linear-gradient(0deg,rgba(0,0,0,.66),transparent)}}"
           f".credit{{position:absolute;right:80px;top:{70 if LAND else 110}px;font-size:28px;line-height:1.3;color:var(--fg);opacity:.8;"
           f"max-width:{'1200' if LAND else '900'}px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:right}}")
    body = '<div class=sb></div>' + (f'<div class=st></div><div class=credit>{esc(credit)}</div>' if credit else '')
    return css, body


def shade_html(tokens, credit=''):
    """입체·그록 영상 위에 얹는 투명 층."""
    css, body = _shade(credit)
    return (f"<!doctype html><html><head><meta charset=utf-8><style>{base_css(tokens)}"
            f"html,body{{height:{H}px;background:transparent;overflow:hidden}}{css}</style></head><body>{body}</body></html>")


def full_html(tokens, img, credit=''):
    """GPT 그림 전면 = 그림이 화면 전체(cover) + 공용 층 — 느린 확대는 ffmpeg 가 준다."""
    css, body = _shade(credit)
    return (f"<!doctype html><html><head><meta charset=utf-8><style>{base_css(tokens)}"
            f"html,body{{height:{H}px;background:var(--bg);overflow:hidden}}{css}"
            f".pic{{position:absolute;inset:0;background:url('file://{img}') center/cover no-repeat}}</style></head>"
            f"<body><div class=pic></div>{body}</body></html>")


def bg_html(tokens):
    """모션 그래픽 장면 바탕 = 글자 0(운영자 260928 «모션 그래픽일 땐 화면 텍스트 없이») · 자막 자리까지 같은 바탕."""
    return f"""<!doctype html><html><head><meta charset=utf-8><style>{tokens}html,body{{margin:0;width:{W}px;height:{H}px;background:var(--bg)}}</style></head><body></body></html>"""


def caption_html(tokens, text):
    return f"""<!doctype html><html><head><meta charset=utf-8><style>{base_css(tokens)}
html,body{{height:{H}px;background:transparent;overflow:hidden}}
.cap{{position:absolute;left:{'200' if LAND else '70'}px;right:{'200' if LAND else '70'}px;top:{'900' if LAND else '1480'}px;display:flex;justify-content:center}}
.cap div{{{f'background:rgba(0,0,0,{SUB_OP:.2f});' if SUB_BG else 'text-shadow:0 2px 6px rgba(0,0,0,.95),0 0 18px rgba(0,0,0,.8);'}border-radius:20px;padding:22px 34px;font-size:{'46' if LAND else '50'}px;line-height:1.38;font-weight:700;text-align:center;letter-spacing:-.02em;overflow-wrap:anywhere}}
</style></head><body><div class=cap><div>{esc(text)}</div></div></body></html>"""


def infographic_html(tokens, plan, meta):
    ig = plan['infographic']
    title = br(ig.get('title'))
    if ig.get('accent'):
        a = esc(ig['accent'])
        title = title.replace(a, f'<span class=acc>{a}</span>', 1)
    quote = (f'<p>"{esc(ig["quote"])}"' + (f' — {esc(ig.get("quote_by"))}' if ig.get('quote_by') else '') + '</p>') if ig.get('quote') else ''
    cards = ''.join(f"<div class=card><div class=no>{esc(p['no'])}</div><div class=kick>{esc(p['kick'])}</div>"
                    f"<h3>{br(p['head'])}</h3><p>{esc(p['body'])}</p><div class=src>{esc(p['src'])}</div></div>"
                    for p in ig.get('panels') or [])
    tb = ig.get('table') or {}
    table = ''
    if tb.get('cols') and tb.get('rows'):
        th = ''.join(f'<th>{esc(c)}</th>' for c in tb['cols'])
        trs = ''.join('<tr>' + ''.join((f'<td><b>{esc(x)}</b></td>' if k == 0 else f'<td>{esc(x)}</td>') for k, x in enumerate(r)) + '</tr>'
                      for r in tb['rows'])
        h2 = f"<h2>{esc(tb['title'])}</h2>" if tb.get('title') else ''
        table = f"<div class=sec>{h2}<table><tr>{th}</tr>{trs}</table></div>"
    q = f"<div class=q>{esc(ig['question'])}</div>" if ig.get('question') else ''
    lim = f"<div class=lim>영상이 밝힌 한계 — {esc(ig['limit'])}</div>" if ig.get('limit') else ''
    src = f"원본 · {esc(meta.get('channel'))} 「{esc(meta.get('title'))}」" + (f" ({esc(meta.get('uploaded'))})" if meta.get('uploaded') else '') + ' · 유튜브 전사 기반 요약'
    return f"""<!doctype html><html><head><meta charset=utf-8><style>{base_css(tokens)}
html,body{{background:var(--bg)}}
.hd{{padding:90px 70px 60px;background:radial-gradient(900px 500px at 20% 0%,rgba(var(--accent-rgb),.18),transparent 70%)}}
.hd .pill{{font-size:30px}}
.hd h1{{margin-top:34px;font-size:{fit(ig.get('title'), 78, 940)}px;line-height:1.18;font-weight:800;letter-spacing:-.03em}}
.hd p{{margin-top:26px;font-size:34px;line-height:1.5;color:var(--mut)}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:28px;padding:10px 70px 0}}
.card{{background:rgba(255,255,255,.045);border:1px solid var(--line);border-radius:24px;padding:40px 38px}}
.no{{font-size:30px;font-weight:800;color:var(--accent)}}
.kick{{margin-top:6px;font-size:28px;color:var(--mut);font-weight:600}}
.card h3{{margin-top:22px;font-size:42px;line-height:1.25;font-weight:800;letter-spacing:-.03em}}
.card p{{margin-top:20px;font-size:29px;line-height:1.55;opacity:.86}}
.card .src{{margin-top:24px;font-size:25px;color:var(--accent);font-weight:700}}
.sec{{padding:70px 70px 0}}
.sec h2{{font-size:46px;font-weight:800;letter-spacing:-.03em}}
table{{width:100%;margin-top:30px;border-collapse:collapse;font-size:30px}}
th{{text-align:left;color:var(--mut);font-weight:600;padding:0 12px 18px 0;border-bottom:2px solid rgba(var(--accent-rgb),.4)}}
td{{padding:24px 16px 24px 0;border-bottom:1px solid var(--line);line-height:1.45;vertical-align:top}}
td b{{font-size:38px;color:var(--accent);font-weight:800}}
.q{{margin:70px 70px 0;padding:44px;border-radius:24px;background:rgba(var(--accent-rgb),.08);border:1px solid rgba(var(--accent-rgb),.35);font-size:40px;line-height:1.5;font-weight:700;letter-spacing:-.02em}}
.lim{{padding:40px 70px 0;font-size:27px;line-height:1.6;color:var(--mut)}}
.ft{{padding:50px 70px 80px;font-size:25px;color:var(--mut)}}
</style></head><body>
<div class=hd>{f"<span class=pill>{esc(ig['kicker'])}</span>" if ig.get('kicker') else ''}<h1>{title}</h1>{quote}</div>
<div class=grid>{cards}</div>{table}{q}{lim}<div class=ft>{src}</div>
</body></html>"""


def probe(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def progress(p, note=''):
    if os.environ.get('YS_ID'):
        subprocess.run([sys.executable, str(Path(__file__).with_name('ys_progress.py')), os.environ['YS_ID'],
                        'render', 'run', note, f'p={p:.3f}'], check=False)


def parse_args(argv):
    """위치 인자 4개 + `--키 값` 쌍(--img-dir · --font · --ratio · --subbg · --subop)."""
    pos, flags, i = [], {}, 1
    while i < len(argv):
        a = argv[i]
        if a.startswith('--') and i + 1 < len(argv):
            flags[a[2:]] = argv[i + 1]
            i += 2
            continue
        pos.append(a)
        i += 1
    return pos, flags


def main(argv):
    global FAMILY, W, H, LAND, SUB_BG, SUB_OP
    args, flags = parse_args(argv)
    img_dir = Path(flags['img-dir']) if flags.get('img-dir') else None
    vid_dir = Path(flags['vid-dir']) if flags.get('vid-dir') else None
    motion_by = {}
    if flags.get('motion') and Path(flags['motion']).exists():
        try:
            motion_by = {int(x['i']): x for x in json.load(open(flags['motion'], encoding='utf-8')).get('scenes') or []}
        except Exception as e:  # noqa: BLE001
            print(f'::warning::motion.json 읽기 실패 — 틀 도식으로 ({type(e).__name__})')
    depth = flags.get('depth') == 'on'
    dep_model = os.environ.get('YS_DEPTH_MODEL', '')
    FAMILY = FONTS.get(flags.get('font', ''), FONTS['pretendard'])
    LAND = flags.get('ratio') == '16:9'
    W, H = (1920, 1080) if LAND else (1080, 1920)
    SUB_BG = flags.get('subbg', 'on') != 'off'
    try:
        SUB_OP = max(0, min(100, int(flags.get('subop', '100')))) / 100
    except ValueError:
        SUB_OP = 1.0
    if len(args) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    plan = json.load(open(args[0], encoding='utf-8'))
    timing = json.load(open(args[1], encoding='utf-8'))
    meta = json.load(open(args[2], encoding='utf-8'))
    out = Path(args[3]); out.mkdir(parents=True, exist_ok=True)
    work = out / '_work'; work.mkdir(exist_ok=True)
    tokens = root_tokens()
    scenes = plan['scenes']
    if len(timing['scenes']) != len(scenes):
        print(f"::error::나레이션 장면 수({len(timing['scenes'])}) ≠ 대본 장면 수({len(scenes)})")
        return 1
    credit = f"원본 · {meta.get('channel', '')} 「{meta.get('title', '')}」"   # 마지막 장면 윗줄(쪽수 자리) 한 줄 = 글자 덩이 밖(넘쳐 잘리던 자리 · 260928 평의회)
    imgs_used = vids_used = mgs_used = deps_used = design_used = 0
    dep_notes = []
    MW, MH = ys_motion.canvas('16:9' if LAND else '9:16')   # 모션 무대 = 자막 자리 위 전체
    kinds, mgcap, posters = [], [], []
    font_css = f"@font-face{{font-family:NMP;src:url('file://{FONT}') format('woff2');font-weight:100 900}}"
    from playwright.sync_api import sync_playwright
    launch = {'args': ['--no-sandbox', '--font-render-hinting=none', '--force-color-profile=srgb']}
    if os.environ.get('MG_CHROMIUM'):
        launch['executable_path'] = os.environ['MG_CHROMIUM']

    def shot(page, text, path, full=False, transparent=False):
        f = work / (Path(path).stem + '.html')
        f.write_text(text, encoding='utf-8')
        page.goto('file://' + str(f))
        page.evaluate('document.fonts.ready')
        page.wait_for_timeout(120)
        page.screenshot(path=str(path), full_page=full, omit_background=transparent)

    caps_all = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(**launch)
        pg = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
        mgp = b.new_page(device_scale_factor=1)   # 모션 그래픽 = 그림 칸 크기 뷰포트(프레임 구동 캡처 전용)
        shot(pg, infographic_html(tokens, plan, meta), out / 'infographic.png', full=True)
        for i, sc in enumerate(scenes):
            last = i == len(scenes) - 1
            d = probe(timing['scenes'][i]['wav']) + PAD
            vid = img = None
            if vid_dir and (vid_dir / f's{i}.mp4').exists() and (vid_dir / f's{i}.mp4').stat().st_size > 10240 and probe(vid_dir / f's{i}.mp4') > 0.5:
                vid = str(vid_dir / f's{i}.mp4')
            if not vid and img_dir:
                for ext in ('png', 'jpg', 'jpeg', 'webp'):
                    c = img_dir / f's{i}.{ext}'
                    if c.exists() and c.stat().st_size > 1024:
                        img = str(c)
                        break
            # 그록·입체·그림 = 화면 전체 + 자막만(운영자 260928 «GPT 도 화면 전체 · 9:16 로 제작 · 화면 안 멘트 안 쓰게» · 모션 그래픽과 같은 원칙)
            if vid:
                vids_used += 1
                kinds.append(('vid', vid))
                shot(pg, shade_html(tokens, credit if last else ''), work / f's{i}o.png', transparent=True)
                mgcap.append(None)
            elif img and depth:   # GPT 입체 = 화면 전체 깊이 시차 영상 + 공용 층
                try:   # 입체 도구(numpy·opencv·onnxruntime)가 없거나 깨져도 = 정지 그림으로 대체(렌더 전체는 산다)
                    import ys_depth
                    ok, why = ys_depth.parallax_clip(img, work / f'dep{i}.mp4', W, H, d, dep_model)
                except Exception as e:  # noqa: BLE001
                    ok, why = False, f'입체 도구 없음({type(e).__name__})'
                if ok:
                    imgs_used += 1
                    deps_used += 0 if why else 1   # 평면 확대로 강하한 장면은 입체로 세지 않는다(표시 정직)
                    if why and why not in dep_notes:
                        dep_notes.append(why)
                    kinds.append(('dep', str(work / f'dep{i}.mp4')))
                    shot(pg, shade_html(tokens, credit if last else ''), work / f's{i}.png', transparent=True)
                    mgcap.append(None)
                else:
                    dep_notes.append(f'장면 {i + 1} 입체 실패({why}) — 정지 그림으로 대체')
                    imgs_used += 1
                    kinds.append(('img', img))
                    shot(pg, full_html(tokens, img, credit if last else ''), work / f's{i}.png')
                    mgcap.append(None)
            elif img:
                imgs_used += 1
                kinds.append(('img', img))
                shot(pg, full_html(tokens, img, credit if last else ''), work / f's{i}.png')
                mgcap.append(None)
            else:   # 모션 그래픽 = 글자 없는 전체 무대(Opus 모션 디자이너 코드 → 검문 실패면 틀 도식)
                mgs_used += 1
                kinds.append(('mg', None))
                shot(pg, bg_html(tokens), work / f's{i}.png')
                hp, n, spec = work / f'mg{i}.html', 0, motion_by.get(i)
                if spec:
                    hp.write_text(ys_mg.motion_page(tokens, font_css, FAMILY, spec['css'], spec['html'], MW, MH, credit if last else ''), encoding='utf-8')
                    try:
                        n = ys_mg.capture_full(mgp, hp, work / f'mg{i}', d, MW, MH)
                    except Exception as e:  # noqa: BLE001
                        n = 0
                        print(f'::warning::장면 {i + 1} 모션 디자인 렌더 실패({type(e).__name__}) — 틀 도식으로')
                    if n:
                        design_used += 1
                        mgcap.append({'dir': work / f'mg{i}', 'n': n, 'ef': 0, 'lf': 0, 'x': 0, 'y': 0, 'type': 'design'})
                    else:
                        dep_notes.append(f'장면 {i + 1} 모션 디자인이 검문을 못 넘어 기본 도식으로 만들었어')
                if not n:
                    mg = ys_mg.textless(ys_mg.normalize_mg(sc.get('mg'), sc))
                    hp.write_text(ys_mg.mg_html(tokens, font_css, FAMILY, mg, MW, MH, credit if last else ''), encoding='utf-8')
                    n, ef, lf = ys_mg.capture(mgp, hp, work / f'mg{i}', d, MW, MH)
                    mgcap.append({'dir': work / f'mg{i}', 'n': n, 'ef': ef, 'lf': lf, 'x': 0, 'y': 0, 'type': mg['type']})
            caps = []
            for a, z, t in timing['scenes'][i]['sents']:
                caps += split_caption(t, a, z)
            for k, (a, z, t) in enumerate(caps):
                shot(pg, caption_html(tokens, t), work / f's{i}c{k}.png', transparent=True)
            caps_all.append(caps)
            progress(0.4 * (i + 1) / len(scenes), f'장면 화면 {i + 1}/{len(scenes)}')
        b.close()
    parts = []
    for i, caps in enumerate(caps_all):
        wav = timing['scenes'][i]['wav']
        d = probe(wav) + PAD
        kind, src = kinds[i]
        first, final_scene = i == 0, i == len(caps_all) - 1
        if kind == 'vid':
            vd = probe(src)
            slow = min(1.15, d / vd) if 0 < vd < d else 1.0   # 짧으면 1.15배까지만 늦추고 나머지는 마지막 프레임 멈춤(억지 보간 0)
            ins = ['-i', src, '-i', wav, '-loop', '1', '-framerate', str(FPS), '-t', f'{d:.3f}', '-i', str(work / f's{i}o.png')]
            fc = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,setpts={slow:.4f}*(PTS-STARTPTS),fps={FPS},"
                  f"tpad=stop_mode=clone:stop_duration={d:.3f},trim=duration={d:.3f},setpts=PTS-STARTPTS,format=rgba[bv]"
                  f";[bv][2:v]overlay=0:0[v0]")
            base = 3
        else:
            ins = ['-loop', '1', '-framerate', str(FPS), '-t', f'{d:.3f}', '-i', str(work / f's{i}.png'), '-i', wav]
            fc, base = '', 2
            src0 = '[0:v]'
            if kind == 'dep':   # 화면 전체 입체 영상 위에 공용 층(s{i}.png = 투명 어둠막·출처)을 얹는다
                ins += ['-i', src]
                fc = (f"[2:v]format=rgba,scale={W}:{H},setsar=1,tpad=stop_mode=clone:stop_duration={d:.3f},trim=duration={d:.3f}[dv];"
                      f"[dv][0:v]overlay=0:0[bm];")
                src0, base = '[bm]', 3
            if kind == 'mg':
                m = mgcap[i]
                ins += ['-framerate', str(FPS), '-i', str(m['dir'] / 'f%04d.jpg')]
                rep_f = (f"loop=loop=-1:size={m['lf']}:start={m['ef']},setpts=N/{FPS}/TB" if m['lf']
                         else f"tpad=stop_mode=clone:stop_duration={d:.3f}")
                fc = f"[2:v]format=rgba,{rep_f},trim=duration={d:.3f}[mg];[0:v][mg]overlay={m['x']}:{m['y']}[bm];"
                src0, base = '[bm]', 3
            zm = 0 if kind in ('dep', 'mg') else ZOOM   # 입체·모션 = 무대가 이미 움직인다(바탕까지 확대하면 두 움직임이 겹쳐 어지럽다)
            fc += f"{src0}scale=w='{W}*(1+{zm}*t/{d:.3f})':h=-2:eval=frame,crop={W}:{H},setsar=1,format=rgba[v0]"
        lastv = 'v0'
        for k, (a, _z, _t) in enumerate(caps):
            ins += ['-loop', '1', '-framerate', str(FPS), '-t', f'{d:.3f}', '-i', str(work / f's{i}c{k}.png')]
            nxt = caps[k + 1][0] if k + 1 < len(caps) else d
            fc += f";[{lastv}][{k + base}:v]overlay=0:0:enable='between(t,{a:.3f},{nxt:.3f})'[v{k + 1}]"
            lastv = f'v{k + 1}'
        if kind == 'vid':   # 영상 장면 사이 = 컷(검은 깜빡임 0) · 맨 앞·맨 뒤만 페이드
            fades = ([f'fade=t=in:st=0:d=0.25'] if first else []) + ([f'fade=t=out:st={d - 0.3:.3f}:d=0.3'] if final_scene else [])
        else:
            fades = ['fade=t=in:st=0:d=0.25', f'fade=t=out:st={d - 0.3:.3f}:d=0.3']
        fc += (f";[{lastv}]{','.join(fades + ['format=yuv420p'])}[vo]"
               f";[1:a]aresample=44100,apad=pad_dur={PAD + 0.2},atrim=0:{d:.3f}[ao]")
        part = work / f'part{i}.mp4'
        subprocess.run(['ffmpeg', '-y', '-v', 'error', *ins, '-filter_complex', fc, '-map', '[vo]', '-map', '[ao]',
                        '-r', str(FPS), '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-c:a', 'aac', '-b:a', '160k',
                        '-ac', '2', '-t', f'{d:.3f}', str(part)], check=True)
        parts.append(part)
        progress(0.4 + 0.55 * (i + 1) / len(caps_all), f'장면 합치기 {i + 1}/{len(caps_all)}')
    lst = work / 'list.txt'
    lst.write_text(''.join(f"file '{p}'\n" for p in parts))
    final = out / 'short.mp4'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy',
                    '-movflags', '+faststart', str(final)], check=True)
    pw_ = f'scale={960 if LAND else 540}:-2'
    k0, s0 = kinds[0]
    if k0 == 'vid':   # 영상 1초 지점 + 얹는 층(자막·제목 없음)
        pin = ['-ss', '1', '-i', s0, '-i', str(work / 's0o.png')]
        pfc = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[b];[b][1:v]overlay=0:0,{pw_}"
    elif k0 == 'dep':  # 입체 영상 1초 지점 한 장 + 공용 층
        pin = ['-ss', '1', '-i', s0, '-i', str(work / 's0.png')]
        pfc = f"[0:v]scale={W}:{H},setsar=1[b];[b][1:v]overlay=0:0,{pw_}"
    elif k0 == 'mg':  # 등장이 끝난 모션 그래픽 한 장을 칸에 겹친다
        m = mgcap[0]
        fr = (min(m['n'], m['ef']) - 1) if m['ef'] else min(m['n'] - 1, 45)   # 틀 = 등장 끝 · 디자이너 장면 = 1.5초 지점
        pin = ['-i', str(work / 's0.png'), '-i', str(m['dir'] / f'f{max(0, fr):04d}.jpg')]
        pfc = f"[0:v][1:v]overlay={m['x']}:{m['y']},{pw_}"
    else:
        pin, pfc = ['-i', str(work / 's0.png')], pw_
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *pin, '-filter_complex', pfc, '-frames:v', '1', '-q:v', '3', str(out / 'poster.jpg')], check=True)
    dur = probe(final)
    if dur <= 0:
        print('::error::최종 영상 길이 0')
        return 1
    json.dump({'dur': round(dur, 2), 'scenes': len(scenes), 'img_used': imgs_used, 'vid_used': vids_used, 'mg_used': mgs_used,
               'depth_used': deps_used, 'design_used': design_used, 'notes': sorted(set(dep_notes))[:3],
               'ratio': '16:9' if LAND else '9:16', 'captions': sum(len(c) for c in caps_all),
               'mg_types': [m['type'] for m in mgcap if m and 'type' in m]}, open(out / 'render.json', 'w'), ensure_ascii=False)
    print(f'렌더 완료 — {dur:.1f}초 · 장면 {len(scenes)} · 영상 {vids_used} · 그림 {imgs_used} · 모션 {mgs_used} · 자막 {sum(len(c) for c in caps_all)}덩이')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
