#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sb_sheet.py — 콘티(board.md)를 **한 장짜리 콘티 시트 그림**으로 굽는다.

  sb_sheet.py <board.md> <out_dir>

운영자 260811 「시트 뽑는 스킬있으면 붙여줘」.

⚠ 왜 필요했나 = 콘티 경로는 지금까지 **글만** 냈다(sb-make.md 6항 = 「이 경로는 콘티 시트
  *이미지* 생성 프롬프트가 아니라 텍스트 콘티 데이터를 출력한다 · 이미지 생성 0 = 0크레딧
  초안 게이트」). 그래서 운영자가 견본으로 보여준 「열두 칸을 한눈에 보는 시트」가 산출에
  없었다 — 그 규약이 정한 「후속 단계」가 바로 이 파일이다.

⚠ 이미지 엔진이 Gemini 가 아니라 **GPT Image** 인 이유 = 시트 한 장에 타이틀바 1줄 +
  칸마다 ACTION / CAMERA / DIALOGUE 세 줄 = 글자가 서른 줄 넘게 들어간다. 화면 안 글자는
  모델마다 편차가 큰 축이고, storyboard-v1 스킬이 이 산출을 GPT Image 기준으로 규격화해
  뒀다(`.claude/skills/storyboard-v1/SKILL.md` §gpt_image_2 호출 스펙). 그 규격을 그대로
  따른다 — 값 창작 0.

⚠ 그록 참조로도 쓸 수 있다 = 시트는 화풍·인물·공간을 한 장에 담고 있어 참조 그림으로도
  유효하다(운영자 260811 「어짜피 시트가 저화질이여도 캐릭터가 비슷하게 나오면 됨」).
  다만 참조 목록의 **주력은 인물 낱장**이다 — 참조 1장이 한 축을 잠그는데 시트는 여러 축이
  섞여 있어 잠금이 흐려진다(그래서 시트는 목록 **뒤**에 붙인다).

CONTRACT: check_grok_sb_chain

fail-soft = 시트가 실패해도 콘티·레퍼런스·영상은 그대로 간다.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_image as gi          # noqa: E402  openai_image (GPT Image 호출 SSOT)
import thumb_gen as tg          # noqa: E402  r2_upload · R2_ON · _img_type
from grok_sb_video import cuts_of   # noqa: E402  컷 파서 = 한 벌만 둔다(사본 0)
import sb_cost as sc                # noqa: E402  값 원장(그림값도 합산)

SHEET_ASPECT = (3, 2)   # storyboard-v1 §호출 스펙 = aspect_ratio "3:2" 고정
_TITLE = re.compile(r"^#\s+(.+)$", re.M)
_LEN = re.compile(r"^길이:\s*(.+)$", re.M)
_STYLE = re.compile(r"^##\s*👤\s*캐릭터\s*\n(.*?)(?=\n##\s|\Z)", re.S | re.M)

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"

# 판형 견본 = 저장소 실물(운영자 260816 「그 에디터 뒤져보면 스토리보드 예시 있어 그거 써」).
#   ⚠ 왜 필요했나 = 지금까지 이 스크립트는 견본을 **글로 설명만** 했다. 감독 지침
#     (`prompts/sb-make.md` 1-b)은 이미 같은 그림을 「정본 양식 실물」로 못 박고 감독에게
#     Read 를 시키는데, 정작 **그림을 굽는 쪽은 그 그림을 한 번도 안 봤다** = 한 정본을
#     두 층이 서로 다르게 쓰던 자리다. 칸 나눔·머리줄·글자 자리·바탕 톤이 회차마다 흔들린 축.
#   ⚠ 참조는 **제미나이 축에만** 싣는다 — GPT 축은 첨부가 붙으면 편집 창구(images/edits)로
#     갈아타서 **견본 그림 자체를 고치려 든다**(견본에 찍힌 남의 얼굴·문구가 산출에 남는다).
#     그쪽은 종전대로 글 규격만으로 새로 그린다(gen_image.openai_image 첫 줄 분기).
#   ⚠ 견본이 없거나 못 읽으면 종전 동작 그대로(글 규격만) = fail-soft.
#   ⚠ 끄기 = `SB_SHEET_REFPIC=0`.
SAMPLE_DIR = os.path.join("apps", "storyboard", "샘플")
# 스케치 판 견본은 아직 저장소에 없다 → 그 판은 글 규격만으로 굽는다(빈 문자열 = 참조 없음).
SAMPLES = {"board": "스토리보드 (1).png", "conti": ""}
SAMPLE_MAX = 1600   # 긴 변 상한 — 견본 원본이 5MB대라 그대로 실으면 요청이 비대해진다
SAMPLE_CLAUSE = (
    "The attached image is our house LAYOUT SAMPLE for this kind of sheet. Copy its structure: "
    "the single title bar across the top, the cell grid proportions, where the thumbnail sits in "
    "each cell, where the label lines sit under it, the label typography weight, the thin cell "
    "borders and the overall background tone. Do NOT copy its people, wardrobe, location, props "
    "or any of its text content — those come from the cut list below.\n\n")


def sample_png(kind):
    """판형 견본 한 장을 참조 그림 bytes 로 읽는다(없으면 None = 종전 동작)."""
    if os.environ.get("SB_SHEET_REFPIC") == "0":
        return None
    nm = SAMPLES.get(kind) or ""
    if not nm:
        return None
    p = os.path.join(SAMPLE_DIR, nm)
    if not os.path.exists(p):
        print("::warning::판형 견본 없음({}) — 글 규격만으로 굽는다".format(p))
        return None
    try:
        import io
        from PIL import Image
        im = Image.open(p).convert("RGB")
        if max(im.size) > SAMPLE_MAX:
            sc_ = SAMPLE_MAX / float(max(im.size))
            im = im.resize((max(1, round(im.size[0] * sc_)), max(1, round(im.size[1] * sc_))),
                           Image.LANCZOS)
        buf = io.BytesIO()
        # q-ok: 모델에 넣는 참조 입력이지 산출물이 아니다(품질 축 = check_image_format 비대상)
        im.save(buf, "JPEG", quality=90, subsampling=0, optimize=True)
        return buf.getvalue()
    except Exception as e:  # noqa: BLE001
        print("::warning::판형 견본 읽기 실패 — 글 규격만으로 굽는다: {}".format(str(e)[:200]))
        return None



def grid_of(n):
    """칸 배치 — **빈칸이 안 남는** 격자를 고른다.

    ⚠ 구판은 10컷을 3행 4열(12칸)로 잡아 **빈칸 2개**를 남겼다. 운영자 견본은 전부 꽉 찬 격자다
      (10컷 = 5열 2행 · 9컷 = 3열 3행 · 8컷 = 4열 2행 · 12컷 = 4열 3행). 빈칸이 남으면 모델이
      그 자리를 제 마음대로 채운다 = 콘티에 없는 컷이 그려진다.
    ⚠ 나누어떨어지는 배치가 여럿이면 **가로로 넓은 쪽**을 고른다(시트가 가로 3:2라서).
    """
    best = None
    for cols in range(2, 6):                        # 견본 실측 = 열이 3·4·5 (한 줄 열 배열은 없다)
        if cols > n:
            break
        rows = -(-n // cols)
        if cols < rows:                             # 세로로 긴 격자는 가로 시트에 안 맞는다
            continue
        empty = rows * cols - n
        score = (empty, abs((cols / float(rows)) - 1.5))
        if best is None or score < best[0]:
            best = (score, rows, cols)
    if best:
        return best[1], best[2]
    return 1, n                                     # 컷이 2~3개뿐이면 한 줄이 맞다


_CONT = re.compile(r"^연속성\s*[:：]\s*(.+)$", re.M)
_LOG = re.compile(r"^##\s*🎬\s*시나리오\s*\n+([^\n]+)", re.M)
_CSLINE = re.compile(r"^논평\s*구조\s*[:：]\s*(.+)$", re.M)
_CUTHEAD = re.compile(r"^###\s*컷\s*\d+\s*·\s*([\d.]+)\s*~\s*([\d.]+)\s*s", re.M)


def continuity_of(md):
    """머리 아래 **연속성 규칙 한 줄** — 견본이 이야기의 뼈대를 잡는 자리(운영자 260814 견본 실측).

    ⚠ 견본 실물 = 「평행 편집, A라인 = 달리는 사람 / 주인공은 전 컷 좌→우 / 문은 항상 화면 오른쪽
      / 차임 x3 / 점프에서 배경음 뮤트」. 이게 있으면 칸끼리 방향과 자리가 안 흔들린다.
    ⚠ 값 창작 0 = 감독이 `## ⚙️ 설계 요약`에 적은 `연속성:` 줄을 그대로 쓴다. 아직 그 줄이 없는
      옛 콘티는 로그라인 + 논평 구조로 **있는 것만** 조립한다(없는 규칙을 지어내지 않는다).
    """
    m = _CONT.search(md)
    if m and m.group(1).strip():
        return " ".join(m.group(1).split())
    bits = []
    g = _LOG.search(md)
    if g:
        bits.append(" ".join(g.group(1).split()))
    c = _CSLINE.search(md)
    if c and "없음" not in c.group(1):
        bits.append("논평 구조 " + " ".join(c.group(1).split()))
    return " / ".join(bits)


def times_of(md, cuts):
    """컷마다 `0.0~1.2s` 시작·끝 — 콘티 머리에 이미 적혀 있다(`cuts_of` 는 길이만 남기고 버린다)."""
    got = _CUTHEAD.findall(md)
    if len(got) == len(cuts):
        return [(a, b) for a, b in got]
    t, out = 0.0, []                       # 표기가 없으면 컷 길이를 누적해 만든다
    for c in cuts:
        out.append(("{:g}".format(t), "{:g}".format(t + c["sec"])))
        t += c["sec"]
    return out


def audio_of(cuts):
    """머리줄 오디오 표기 — 견본은 여기에 소리 구성이 적혀 있다. 값은 콘티 실값에서 센다."""
    has_sfx = any((c.get("sfx") or "").strip() for c in cuts)
    has_line = any(_real_line(c.get("dialogue")) for c in cuts)
    parts = [x for x in (("DIALOGUE" if has_line else ""), ("SFX" if has_sfx else "")) if x]
    return (" + ".join(parts) + ", NO BGM") if parts else "NO BGM"


def _real_line(s):
    """실제 대사가 있는 칸인가 — 「(없음)」·「—」·빈칸은 대사가 아니다."""
    s = (s or "").strip()
    return bool(s) and s not in ("(없음)", "없음", "-", "—", "–")


def sheet_prompt(md, cuts):
    """storyboard-v1 §프롬프트 템플릿을 콘티 실값으로 채운다(문구 창작 0)."""
    title = (_TITLE.search(md).group(1).strip() if _TITLE.search(md) else "콘티")
    length = (_LEN.search(md).group(1).strip() if _LEN.search(md) else "")
    length = re.sub(r"[—\-·]?\s*\d+\s*컷", "", length).strip() or "{}s".format(sum(c["sec"] for c in cuts))
    lock = ""
    m = _STYLE.search(md)
    if m:
        # 캐릭터 절의 ```text 블록 = 정체성 락(마스터시트 V2 서술) → 전 칸 고정 조건으로 옮긴다
        blocks = re.findall(r"```text\s*\n(.*?)```", m.group(1), re.S)
        lock = " ".join(b.strip().replace("\n", " ") for b in blocks)[:900]
    rows, cols = grid_of(len(cuts))

    times = times_of(md, cuts)
    cells = []
    for i, c in enumerate(cuts):
        one = "{}  TIME: {}–{}s   ACTION: {}   CAMERA: {}".format(
            CIRCLED[i] if i < len(CIRCLED) else "({})".format(i + 1),
            times[i][0], times[i][1],
            c["action"] or c["desc"] or "-",
            c["camera"] or "-")
        if _real_line(c.get("dialogue")):          # 대사 칸은 **있는 컷에만** 붙는다(견본 실측)
            one += "   DIALOGUE: 「{}」".format(c["dialogue"].strip("「」"))
        cells.append(one)
    ad = "[광고: ON]" in md
    cont = continuity_of(md)

    return (
        "You are a {who} and storyboard artist. Generate ONE single horizontal "
        "STORYBOARD SHEET (콘티) that lays out the whole piece at a glance, on a light "
        "cream/ivory editorial background with thin grey cell borders.\n\n"
        "[SPOT]\n"
        "Title bar (top, one line): {title} — {n} CUTS, {length}, {audio}\n"
        "{contline}"
        "Art style: photoreal cinematic, warm natural light, consistent grade across every cell\n"
        "Total cuts: {n}  →  grid {rows}x{cols}. Draw EXACTLY {n} cells and no more{lastrow} — "
        "never invent an extra cell to fill the grid. Circled numbers (1)(2)(3)... in top-left "
        "of each cell\n\n"
        "[LOCKED DESIGN — identical in every cell]\n{lock}\n\n"
        "[CELLS — each = thumbnail on top + metadata lines below]\n{cells}\n\n"
        "[STYLE RULES]\n"
        "- One flat planning sheet, light cream background, thin grey gridlines, circled cut numbers.\n"
        "- Each cell thumbnail = a different shot/angle, but SAME character/product/world design throughout.\n"
        "- Printed text = title bar{contsay} + per-cell TIME/ACTION/CAMERA labels, and a DIALOGUE line "
        "ONLY in the cells that actually have a spoken line. Korean action & dialogue, English camera "
        "terms. NO Japanese, NO hex codes, NO watermark, NO real brand logos.\n"
        "- Audio policy NO BGM.\n"
        "- Photoreal {look} look."
    ).format(who="commercial director" if ad else "film director",
             look="commercial" if ad else "cinematic",
             title=title, length=length, n=len(cuts), rows=rows, cols=cols,
             lastrow=("" if rows * cols == len(cuts) else
                      " (the last row holds only {} cells and ends there)".format(
                          len(cuts) - cols * (rows - 1))),
             audio=audio_of(cuts),
             contline=("Continuity rule (ONE line printed directly under the title bar, small type): "
                       "{}\n".format(cont) if cont else ""),
             contsay=" + the continuity rule line" if cont else "",
             lock=lock or "Keep character, wardrobe and location design identical across all cells.",
             cells="\n".join(cells))


def conti_prompt(md, cuts):
    """스케치 동작 콘티 — 스토리보드와 **같은 칸 배치**로 동작만 연필 스케치로 뜬다.

    운영자 260814 = 「스케치 동작 시트가 있으면 모션이 훨씬 퀄이 올라간다 · 만화 그리기 전에
    연필로 스케치 뜨는 것과 같음 · 스토리보드 각각에 맞게 짜는 것」.

    ⚠ 스토리보드와 무엇이 다른가 = 스토리보드는 **그 컷이 어떻게 보이는가**(완성 그림)이고
      이건 **그 안에서 무엇이 어떻게 움직이는가**(자세와 이동)다. 그래서 색·질감·조명을 빼고
      연필선과 움직임 화살표만 남긴다 — 남기면 모델이 그 그림의 화풍을 따라 그린다.
    ⚠ 칸 번호·배치는 스토리보드와 1:1 이어야 한다(참조 두 장이 서로 다른 순서를 말하면 사고).
    """
    title = (_TITLE.search(md).group(1).strip() if _TITLE.search(md) else "콘티")
    rows, cols = grid_of(len(cuts))
    cont = continuity_of(md)
    cells = []
    for i, c in enumerate(cuts):
        cells.append("{}  MOTION: {}   CAMERA MOVE: {}".format(
            CIRCLED[i] if i < len(CIRCLED) else "({})".format(i + 1),
            c.get("motion") or c["action"] or c["desc"] or "-",
            c["camera"] or "-"))
    return (
        "You are a storyboard artist. Generate ONE single horizontal MOTION SKETCH SHEET — rough "
        "graphite pencil sketches on white paper, like the pose thumbnails an artist draws before "
        "inking a comic.\n\n"
        "[SHEET]\n"
        "Title bar (top, one line): {title} — 동작 스케치 / {n}컷\n"
        "{contline}"
        "Grid {rows}x{cols}, circled numbers ①②③… in the top-left of each cell, same cut order as the "
        "storyboard.\n\n"
        "[CELLS — each = one rough pencil sketch of the MOVEMENT in that cut]\n{cells}\n\n"
        "[STYLE RULES]\n"
        "- Pencil line art only: loose graphite strokes, light construction lines, white paper, thin "
        "grey gridlines. NO color, NO photoreal rendering, NO lighting, NO texture.\n"
        "- Draw the POSE and the MOTION: arrows for body movement and for camera movement, a few "
        "motion lines, start pose solid and end pose lightly ghosted where the body travels.\n"
        "- Same character build and wardrobe silhouette in every cell.\n"
        "- Printed text = title bar + circled cut numbers only. NO Japanese, NO watermark, NO logos."
    ).format(title=title, n=len(cuts), rows=rows, cols=cols, cells="\n".join(cells),
             # ⚠ 화살표 방향의 정본 = 연속성 줄이다(견본 「주인공은 전 컷 좌→우」). 이 줄이 없으면
             #   칸마다 화살표가 제멋대로여서 스케치가 오히려 모델을 헷갈리게 한다.
             contline=("Continuity rule: {} — every body-movement and camera-movement arrow must obey "
                       "this rule.\n".format(cont) if cont else ""))


# 굽는 판 = 두 장(운영자 260814 「스토리보드 1, 콘티 1」) — 순서 계약 = 스토리보드 먼저 · 콘티 나중
KINDS = {
    "board": ("스토리보드", "sheet.jpg", "sheet_prompt"),
    "conti": ("스케치 동작 콘티", "conti.jpg", "conti_prompt"),
}


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: sb_sheet.py <board.md> <out_dir> [board|conti]")
    md_path, out_dir = sys.argv[1], sys.argv[2]
    kind = (sys.argv[3] if len(sys.argv) > 3 else "board").strip().lower()
    if kind not in KINDS:
        sys.exit("모르는 판 이름: {}(쓸 수 있는 것 = {})".format(kind, " · ".join(KINDS)))
    kind_nm, key_nm, fn_nm = KINDS[kind]
    md = open(md_path, encoding="utf-8").read()
    stem = os.path.basename(os.path.normpath(out_dir))
    prefix = os.environ.get("REFGEN_PREFIX", "sb_out")

    cuts = cuts_of(md)
    if not cuts:
        print("{}: 미시도(컷 0개) — board.md 형식 확인".format(kind_nm))
        return 0

    # ⚠ 엔진 2단(260811 실측 봉합) — 첫 실호출(run 31536019555)에서 이 스텝이 **1초 만에 끝났다**.
    #   OPENAI_API_KEY 가 레포 시크릿에 없어서 통째로 미시도였고, 영상 12컷은 다 나왔는데
    #   시트만 조용히 0장이었다(에러 0 · 잡은 초록). 없는 키를 기다리는 층은 죽은 층이라
    #   **이미 있는 자격(Gemini)** 으로 내려앉는다 — 종전 정본(GPT Image)은 1순위 그대로다.
    prompt = globals()[fn_nm](md, cuts)
    refpic = sample_png(kind)               # 판형 견본(운영자 260816) — 없으면 None = 종전 동작
    png, engine = None, None
    if os.environ.get("OPENAI_API_KEY", "").strip():
        try:
            # ⚠ 견본을 여기엔 안 싣는다 — 첨부가 붙으면 편집 창구로 갈아타 견본 자체를 고친다(위 주석).
            png = gi.openai_image(prompt, None, SHEET_ASPECT)
            engine = "gpt_image"
        except Exception as e:  # noqa: BLE001
            print("::warning::{} GPT Image 실패 — 제미나이로 내려앉는다: {}".format(kind_nm, str(e)[:200]))
    if not png and tg.KEY:
        # 2K = 시트엔 칸마다 글자 세 줄이 들어가므로 1K 로는 뭉갠다(k_refgen 은 그림 한 장이라 1K).
        png = tg.gemini_image((SAMPLE_CLAUSE + prompt) if refpic else prompt, "2K", tag="sbsheet",
                              aspect="{}:{}".format(*SHEET_ASPECT), ref_png=refpic)
        engine = "gemini"
    if not png:
        print("{}: 미시도(OPENAI_API_KEY·GEMINI_API_KEY 둘 다 없음)".format(kind_nm))
        return 0

    url = None
    if tg.R2_ON:
        try:
            url = tg.r2_upload(png, "{}/{}/{}".format(prefix, stem, key_nm),
                               tg._img_type(png)[0] or "image/jpeg")
        except Exception as e:  # noqa: BLE001
            print("::warning::{} R2 업로드 실패: {}".format(kind_nm, str(e)[:200]))
    if not url:
        # R2 가 없으면 레포에 남긴다(판마다 1장뿐이라 비대 위험이 작다 = k_refgen 폴백 관례)
        open(os.path.join(out_dir, key_nm), "wb").write(png)
    # ⚠ 값은 **판마다 다른 칸**에 적는다 — 두 판이 같은 칸(kind)을 쓰면 뒤가 앞을 덮어 호출
    #   두 번이 원장에는 한 번으로 남는다(평의회 260814 실측 = 화면 금액이 실제보다 작아진다).
    # ⚠ 엔진과 무관하게 적는다 — GPT Image 로 성공하면 종량제 호출인데 원장이 0이었다(같은 병).
    _kind = "sheet" if kind == "board" else kind
    if engine == "gemini":
        sc.add(out_dir, "gemini", _kind, 1, note="2K 단가 미확인 = 1K 단가로 센 하한")
    elif engine:
        sc.add(out_dir, engine, _kind, 1, usd=0, note="단가 미확인 — 호출 수만 기록")
    # ⚠ 원장은 **판마다 한 칸씩 덮어쓴다** — 통째로 새로 쓰면 먼저 구운 판의 주소가 지워진다
    #   (스토리보드를 굽고 콘티를 구우면 스토리보드 주소가 사라지는 형태 = 조용한 유실).
    js = os.path.join(out_dir, "sheet.json")
    try:
        d = json.load(open(js, encoding="utf-8"))
        if not isinstance(d, dict):
            d = {}
    except Exception:  # noqa: BLE001
        d = {}
    d["cuts"] = len(cuts)
    if kind == "board":
        d["url"], d["engine"] = url, engine          # 하위호환 = 뷰어·러너가 읽는 그 자리
    else:
        d[kind], d[kind + "_engine"] = url, engine
    try:
        json.dump(d, open(js, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:  # noqa: BLE001
        pass
    print("{}: {}컷 1장 · 엔진 {} → {}".format(
        kind_nm, len(cuts), engine, url or os.path.join(out_dir, key_nm)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print("::warning::sb_sheet 예외(비치명): {}".format(str(e)[:300]))
        sys.exit(0)
