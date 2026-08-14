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


def grid_of(n):
    """칸 배치 — 견본(12컷 = 4열 3행) 규격을 기준으로 한다."""
    if n <= 4:
        return 1, n
    if n <= 8:
        return 2, (n + 1) // 2
    if n <= 12:
        return 3, 4
    return 4, (n + 3) // 4


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

    cells = []
    for i, c in enumerate(cuts):
        cells.append("{}  ACTION: {}   CAMERA: {}   DIALOGUE: {}".format(
            CIRCLED[i] if i < len(CIRCLED) else "({})".format(i + 1),
            c["action"] or c["desc"] or "-",
            c["camera"] or "-",
            c["dialogue"] or "(없음)"))

    return (
        "You are a commercial director and storyboard artist. Generate ONE single horizontal "
        "AD STORYBOARD SHEET (콘티) that lays out an entire spot at a glance, on a light "
        "cream/ivory editorial background with thin grey cell borders.\n\n"
        "[SPOT]\n"
        "Title bar (top, one line): {title} — {length} / {n}컷\n"
        "Art style: photoreal cinematic, warm natural light, consistent grade across every cell\n"
        "Total cuts: {n}  →  grid {rows}×{cols}, circled numbers ①②③… in top-left of each cell\n\n"
        "[LOCKED DESIGN — identical in every cell]\n{lock}\n\n"
        "[CELLS — each = thumbnail on top + 3 metadata lines below]\n{cells}\n\n"
        "[STYLE RULES]\n"
        "- One flat planning sheet, light cream background, thin grey gridlines, circled cut numbers.\n"
        "- Each cell thumbnail = a different shot/angle, but SAME character/product/world design throughout.\n"
        "- Printed text = title bar + per-cell ACTION/CAMERA/DIALOGUE labels only. Korean action & "
        "dialogue, English camera terms. NO Japanese, NO hex codes, NO watermark, NO real brand logos.\n"
        "- Audio policy NO BGM.\n"
        "- Photoreal commercial look."
    ).format(title=title, length=length, n=len(cuts), rows=rows, cols=cols,
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
    ).format(title=title, n=len(cuts), rows=rows, cols=cols, cells="\n".join(cells))


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
    png, engine = None, None
    if os.environ.get("OPENAI_API_KEY", "").strip():
        try:
            png = gi.openai_image(prompt, None, SHEET_ASPECT)
            engine = "gpt_image"
        except Exception as e:  # noqa: BLE001
            print("::warning::{} GPT Image 실패 — 제미나이로 내려앉는다: {}".format(kind_nm, str(e)[:200]))
    if not png and tg.KEY:
        # 2K = 시트엔 칸마다 글자 세 줄이 들어가므로 1K 로는 뭉갠다(k_refgen 은 그림 한 장이라 1K).
        png = tg.gemini_image(prompt, "2K", tag="sbsheet",
                              aspect="{}:{}".format(*SHEET_ASPECT))
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
    if engine == "gemini":
        sc.add(out_dir, "gemini", "sheet", 1, note="2K 단가 미확인 = 1K 단가로 센 하한")
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
