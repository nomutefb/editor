#!/usr/bin/env python3
"""유튜브 숏폼(ys) 렌더 — plan.json + 나레이션 타이밍 → 9:16 mp4 · 포스터 · 인포그래픽 PNG.

  ys_render.py <plan.json> <timing.json> <meta.json> <outdir> [--img-dir DIR] [--font pretendard|gothic|barun]
               [--ratio 9:16|16:9] [--subbg on|off] [--subop 0~100]

  산출 = outdir/short.mp4 · outdir/poster.jpg · outdir/infographic.png · outdir/render.json(집계)
  장면 = 슬라이드 PNG(헤드리스 Chromium) + 느린 확대 + 문장 자막 오버레이 + 장면 나레이션 → 장면 클립 → 이어붙이기.
  --img-dir 에 s{i}.png|jpg 가 있으면 그 장면 위쪽에 그림을 깔고(맥 Codex 이미지 레인), 없으면 글자 화면.

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


def layout(img):
    """장면 배치(px) — 세로 9:16 = 위 그림·아래 글자 / 가로 16:9 = 왼쪽 글자·오른쪽 그림.
    글자는 한 덩이 세로 흐름(.txt = 큰 글자 → 보조 → 칩 → 출처)이라 줄 수가 늘어도 겹치지 않는다(고정 top 배치 폐기 · 16:9 실측 겹침 봉합).
    txt = 글자 덩이 영역(위·아래 경계) · tw = 큰 글자 자동 맞춤 폭 · 자막 영역(세로 1480~ · 가로 900~)은 비워 둔다."""
    if LAND:
        if img:
            return dict(top=70, pic='left:1000px;right:80px;top:170px;height:680px', txt='top:170px;bottom:230px;right:1000px',
                        tw=840, big_cap=104, head_cap=60, just='center')
        return dict(top=70, pic='', txt='top:170px;bottom:230px;right:80px', tw=1760, big_cap=150, head_cap=72, just='center')
    if img:
        return dict(top=120, pic='left:80px;right:80px;top:230px;height:740px', txt='top:1010px;bottom:470px;right:80px',
                    tw=920, big_cap=110, head_cap=80, just='flex-start')
    return dict(top=120, pic='', txt='top:360px;bottom:470px;right:80px', tw=920, big_cap=150, head_cap=84, just='center')


def slide_html(tokens, sc, idx, total, img=None, credit=''):
    tag = esc(sc.get('tag'))
    step = f'{idx} / {total - 2}' if 0 < idx < total - 1 else ''
    chips = ''.join(f'<span class=chip>{esc(c)}</span>' for c in sc.get('chips') or [])
    big, head = sc.get('big') or '', sc.get('head') or ''
    L = layout(img)
    vis = f"<div class=pic style=\"background-image:url('file://{img}')\"></div>" if img else ''
    big_px, head_px = fit(big, L['big_cap'], L['tw']), fit(head, L['head_cap'], L['tw'])
    step_or_credit = f'<span class=credit>{esc(credit)}</span>' if credit else f'<span class=step>{step}</span>'
    return f"""<!doctype html><html><head><meta charset=utf-8><style>{base_css(tokens)}
html,body{{height:{H}px;overflow:hidden;background:var(--bg)}}
body{{background:radial-gradient(1200px 900px at {'30% 40%' if LAND else '50% 28%'},rgba(var(--accent-rgb),.13),transparent 60%),var(--bg)}}
.top{{position:absolute;left:80px;right:80px;top:{L['top']}px;display:flex;justify-content:space-between;align-items:center}}
.step{{font-size:34px;color:var(--mut);font-weight:600}}
.pic{{position:absolute;{L['pic']};border-radius:28px;background-size:cover;background-position:center;border:1px solid var(--line)}}
.pic::after{{content:'';position:absolute;inset:0;border-radius:28px;background:linear-gradient(180deg,transparent 55%,rgba(0,0,0,.55))}}
.txt{{position:absolute;left:80px;{L['txt']};display:flex;flex-direction:column;justify-content:{L['just']};gap:36px;overflow:hidden}}
.big{{font-size:{big_px}px;line-height:1.12;font-weight:800;letter-spacing:-.03em;color:var(--accent)}}
.head{{font-size:{head_px}px;line-height:1.22;font-weight:800;letter-spacing:-.03em}}
.credit{{font-size:28px;line-height:1.3;color:var(--mut);max-width:{'1200' if LAND else '620'}px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:right}}
</style></head><body>
<div class=top><span class=pill>{tag}</span>{step_or_credit}</div>
{vis}<div class=txt><div class=big>{br(big)}</div><div class=head>{br(head)}</div><div class=chips>{chips}</div></div>
</body></html>"""


FIT_JS = """() => {
  const t = document.querySelector('.txt'); if (!t) return 0;
  const over = () => { const r = t.getBoundingClientRect(), k = [...t.children].filter(c => c.offsetHeight);
    if (!k.length) return false; return k[0].getBoundingClientRect().top < r.top - 1 || k[k.length - 1].getBoundingClientRect().bottom > r.bottom + 1; };
  let n = 0;
  while (over() && n < 8) { for (const s of ['.big', '.head']) { const e = t.querySelector(s); if (e) e.style.fontSize = (parseFloat(getComputedStyle(e).fontSize) * 0.9) + 'px'; } n++; }
  if (over()) { const c = t.querySelector('.chips'); if (c) c.style.display = 'none'; return 'chips'; }
  return n;
}"""


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
    imgs_used = 0
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
        if not full and not transparent:   # 장면 = 글자 덩이가 영역을 넘으면 큰 글자·보조 글자를 0.9배씩 줄이고(최대 8번) 그래도 넘치면 칩을 뺀다 = 조용한 잘림 0
            r = page.evaluate(FIT_JS)
            if r == 'chips':
                print(f'::warning::{Path(path).stem} 글자가 많아 칩을 뺐어')
        page.screenshot(path=str(path), full_page=full, omit_background=transparent)

    caps_all = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(**launch)
        pg = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
        shot(pg, infographic_html(tokens, plan, meta), out / 'infographic.png', full=True)
        for i, sc in enumerate(scenes):
            img = None
            if img_dir:
                for ext in ('png', 'jpg', 'jpeg', 'webp'):
                    c = img_dir / f's{i}.{ext}'
                    if c.exists() and c.stat().st_size > 1024:
                        img, imgs_used = str(c), imgs_used + 1
                        break
            last = i == len(scenes) - 1
            shot(pg, slide_html(tokens, sc, i, len(scenes), img, credit if last else ''), work / f's{i}.png')
            caps = []
            for a, z, t in timing['scenes'][i]['sents']:
                caps += split_caption(t, a, z)
            for k, (a, z, t) in enumerate(caps):
                shot(pg, caption_html(tokens, t), work / f's{i}c{k}.png', transparent=True)
            caps_all.append(caps)
            progress(0.4 * (i + 1) / len(scenes), f'장면 그림 {i + 1}/{len(scenes)}')
        b.close()
    parts = []
    for i, caps in enumerate(caps_all):
        wav = timing['scenes'][i]['wav']
        d = probe(wav) + PAD
        ins = ['-loop', '1', '-t', f'{d:.3f}', '-i', str(work / f's{i}.png'), '-i', wav]
        fc = f"[0:v]scale=w='{W}*(1+{ZOOM}*t/{d:.3f})':h=-2:eval=frame,crop={W}:{H},setsar=1,format=rgba[v0]"
        lastv = 'v0'
        for k, (a, _z, _t) in enumerate(caps):
            ins += ['-loop', '1', '-t', f'{d:.3f}', '-i', str(work / f's{i}c{k}.png')]
            nxt = caps[k + 1][0] if k + 1 < len(caps) else d
            fc += f";[{lastv}][{k + 2}:v]overlay=0:0:enable='between(t,{a:.3f},{nxt:.3f})'[v{k + 1}]"
            lastv = f'v{k + 1}'
        fc += (f";[{lastv}]fade=t=in:st=0:d=0.25,fade=t=out:st={d - 0.3:.3f}:d=0.3,format=yuv420p[vo]"
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
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(work / 's0.png'), '-vf', f'scale={960 if LAND else 540}:-2', '-q:v', '3',
                    str(out / 'poster.jpg')], check=True)
    dur = probe(final)
    if dur <= 0:
        print('::error::최종 영상 길이 0')
        return 1
    json.dump({'dur': round(dur, 2), 'scenes': len(scenes), 'img_used': imgs_used, 'ratio': '16:9' if LAND else '9:16',
               'captions': sum(len(c) for c in caps_all)}, open(out / 'render.json', 'w'), ensure_ascii=False)
    print(f'렌더 완료 — {dur:.1f}초 · 장면 {len(scenes)} · 그림 {imgs_used} · 자막 {sum(len(c) for c in caps_all)}덩이')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
