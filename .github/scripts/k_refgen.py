#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k_refgen.py — /k(영상 프롬프트)·콘티(sb) 레퍼런스 이미지 '직영' 생성.

  k_refgen.py <prompt.md> <out_dir>
  env REFGEN_PREFIX(R2 키 접두 · 기본 k_out) · REFGEN_ASPECT(생성 비율 · 기본 16:9)

레인 2개 공용(260730 — 콘티 레인 재사용 · 스크립트 복제 0):
  · k  레인 = k_out/<id>/prompt.md  · 기본값 그대로(16:9 · k_out)
  · sb 레인 = sb_out/<id>/board.md · REFGEN_PREFIX=sb_out REFGEN_ASPECT=9:16(숏폼 기본)
    ↳ 콘티 md + 참조 이미지 URL이 한 폴더에 앉는다 = 힉스필드(시댄스) 1-way 주입 재료.

prompt.md 의 '## 🖼 레퍼런스' ```text 블록(1개 = 대표 1장 · 여러 개 = 다장 — 운영자 토글 260708·합 ≤7)을
뽑아 Gemini(직접 호출)로 블록당 이미지 1장 생성 →
  · R2 켜져 있으면 = k_out/<id>/ref.jpg(첫 장)·ref_2.jpg… 키로 업로드 + out_dir/ref.json({"url":첫장,"urls":[전부]}) 기록(레포 비대 0)
  · R2 없으면     = out_dir/ref.jpg 로컬 저장(git 폴백 — 대표 1장만·다장은 R2 필요)
뷰어 k.html 은 ref.json(urls 배열 → url 단수) 우선, 없으면 ref.jpg 경로로 표시.

기존 외부경로(k_refmd.py → drive_cards.py → Apps Script → Drive → Gemini) 의 in-repo 대체.
Apps Script·Drive·GDRIVE_SA_JSON·Cloud Run 불요. 게이트 = GEMINI_API_KEY(+ R2 5시크릿이면 R2).
카드/썸네일과 동일 파이프(thumb_gen.gemini_image·r2_upload) 재사용 = 배관 1개로 통일. fail-soft.
"""
import os, re, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import thumb_gen as tg   # gemini_image · r2_upload · R2_ON · KEY (모듈 import = main 미실행)

# 레퍼런스 = 글자 없는 깨끗한 주체/장면 컷(텍스트 합성 없음 = Kling @참조용).
REF_STYLE = " 글자·자막·캡션·워터마크·로고 없이 깨끗한 장면만."

# 인물 슬롯 = **한 페이지에 360도**(운영자 260814 「큼지막한게 하나 있는게 아니라 인물의 360도를
# 기록한게 더 중요한거라는거지 한 페이지에」 · 「항상 저렇게 인물이 뽑히도록」).
# ⚠ 왜 낱장 사진이면 안 되나 = 참조 한 장은 「이 얼굴을 유지하라」는 잠금인데, 정면 한 컷만 주면
#   옆·뒤로 돌아가는 순간 모델이 참고할 게 없어 **딴사람이 된다**(그 사고를 막는 게 회전 시트다).
# ⚠ 규격 창작 0 = `.claude/skills/master-sheet-v2/SKILL.md` §STEP2 CHARACTER 패널 세트와 §STEP4
#   템플릿 문장을 그대로 옮겼다(정면·3/4·측면·전신·표정 · 칸 이름만 글자 · 가로 3:2 · 2K).
#   단 「좌측 대형 정면」은 안 쓴다 — 운영자가 그 축을 정정했다(큰 정면 하나가 아니라 360 기록).
# 판마다 칸 구성이 다르다 — 사람은 얼굴, 물건은 형태, 장소는 자리다.
#   ⚠ 사람·물건 칸 구성은 `.claude/skills/master-sheet-v2/SKILL.md` §STEP2 를 그대로 옮겼다(창작 0).
#     견본 그림(`assets/reference-character-sheet-v2.png`)에 있는 **달리기(RUN)** 칸도 그대로 넣는다.
#   ⚠ 장소는 그 문서에 없다 = 운영자 260814 「환경이 주요가 되면 환경도 다각도로」 → 사람·물건과
#     **같은 문법**으로 짜되(한 페이지·같은 크기 칸·칸 이름만 글자) 칸 이름만 장소 축으로 바꾼다.
_SHEET_COMMON = (
    " Lay the panels out as one page, equally sized, same subject design, same lighting and same"
    " color grade in EVERY panel. Print only the short panel header labels in Korean with the English"
    " in parentheses, no other in-image text, no hex codes, no captions, no watermark, no logos."
)
TURN_SPECS = {
    "person": (" ONE CHARACTER TURNAROUND SHEET: 정면(FRONT), 3/4 (45 degrees), 측면(SIDE) profile,"
               " 전신(FULL BODY) head to shoe, 달리기(RUN) a full-body running pose with motion blur,"
               " and 표정(EXPRESSION) a row of 3 head close-ups (calm, alarmed, smiling)."
               " Identical face, hair and wardrobe in every panel." + _SHEET_COMMON),
    "product": (" ONE PRODUCT SHEET: 히어로(HERO) one larger beauty shot, then 정면(FRONT), 측면(SIDE),"
                " 후면(BACK) of the same object, and 디테일(DETAIL) 2-3 close inserts of its key finish."
                " Identical silhouette, label and material in every panel." + _SHEET_COMMON),
    "place": (" ONE LOCATION SHEET: 전경(WIDE) the whole place, 눈높이(EYE LEVEL) as a person standing in"
              " it would see, 반대편(REVERSE) the opposite direction from the same spot, 위에서(TOP DOWN)"
              " the layout, and 디테일(DETAIL) 2-3 close inserts of its fixed set pieces."
              " Identical architecture, props and time of day in every panel." + _SHEET_COMMON),
}
TURN_ASPECT, TURN_SIZE = "3:2", "2K"   # 시트 기본 = 가로 3:2 · 칸이 여럿이라 1K 면 얼굴이 뭉갠다

# 참조 슬롯 라벨 = `## 🖼 레퍼런스` 절의 「① 인물:」·「② 배경:」 — 파서 단일정본(grok_sb_video 가 이걸 쓴다)
_REF_LABEL = re.compile(r"^\s*[①-⑳]\s*([^\n:：]{1,30})\s*[:：]", re.M)
# ⚠ 다각도 시트는 **라벨로 신청한다**(추측 0) — 「배경」 하나만 적힌 슬롯은 종전대로 낱장 장면이다.
#   운영자 260814 = 「어떤 특정 일정한 환경이 **주요가 되면**」·「특정 광고 매체나 상품이 위주일 때」
#   → 감독이 「주요 장소:」·「제품:」이라 적은 것만 시트로 간다(전부 시트로 굽으면 값이 배로 든다).
_KIND_RE = (
    ("person", re.compile(r"인물|사람|캐릭터|주인공|출연|배우")),
    ("product", re.compile(r"제품|상품|물건|패키지|굿즈|보틀")),
    ("place", re.compile(r"주요\s*장소|주요\s*배경|주무대|메인\s*장소|고정\s*장소")),
)


def ref_labels(md):
    """참조 절 라벨을 블록과 **같은 순서**로 돌려준다(사본 0 = 슬롯 번호가 갈릴 여지 0)."""
    sec = re.search(r'##\s*🖼\s*레퍼런스\s*\n(.*?)(?=\n##\s|\Z)', md, re.S)
    return [x.strip() for x in _REF_LABEL.findall(sec.group(1) if sec else md)]


def sheet_kind(label):
    """이 슬롯을 다각도 시트로 굽나 — 굽는다면 어느 문법인가(아니면 None = 종전 낱장)."""
    for kind, rx in _KIND_RE:
        if rx.search(label or ""):
            return kind
    return None


def is_person(label):
    """사람 슬롯인가 — 정체 문장 꼬리(회전 시트 고지)를 붙일지 가르는 축."""
    return sheet_kind(label) == "person"


def extract_refs(md):
    """'## 🖼 레퍼런스' 절 안 ```text 블록 전부 — 단일(대표 1장)도 다장(운영자 토글 260708)도 같은 findall로 수렴.
    인포스트링 관용([^\n]*)·블록 사이 라벨 평문 허용(findall이 산문 무시) · Omni 참조 한도 7 가드."""
    sec = re.search(r'##\s*🖼\s*레퍼런스\s*\n(.*?)(?=\n##\s|\Z)', md, re.S)
    if not sec:
        return []
    blocks = re.findall(r'```[^\n]*\n(.*?)\n```', sec.group(1), re.S)
    out = [b.strip() for b in blocks if b.strip()]
    if len(out) > 7:
        print("::warning::레퍼런스 블록 {}개 > 7 — 초과분 절단(🔗 범례와 어긋날 수 있음 · 모델 계약 위반)".format(len(out)))
    return out[:7]


def main():
    if len(sys.argv) < 3:
        print("usage: k_refgen.py <prompt.md> <out_dir>", file=sys.stderr); return 0  # 비치명
    src, out_dir = sys.argv[1], sys.argv[2]
    if not tg.KEY:
        print("GEMINI_API_KEY 없음 — 레퍼런스 생략(스캐폴드)"); return 0
    try:
        md = open(src, encoding="utf-8").read()
    except OSError:
        print("prompt.md 없음 — 레퍼런스 생략"); return 0
    refs = extract_refs(md)
    if not refs:
        print("레퍼런스 블록 없음/비어있음 — 생략"); return 0

    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.basename(out_dir.rstrip("/"))
    # 레인 파라미터(260730 · 콘티[sb] 레인 재사용 — 기본값 = k 레인 종전 동작 = 무회귀):
    #   REFGEN_PREFIX = R2 키 접두(k_out|sb_out) · REFGEN_ASPECT = 생성 비율(k=16:9 가로 · sb=9:16 숏폼 기본)
    prefix = os.environ.get("REFGEN_PREFIX") or "k_out"
    aspect = os.environ.get("REFGEN_ASPECT") or "16:9"
    # 영상 레퍼런스 = 16:9 기본(가로 영상). 1K(토큰 절감, 썸네일/카드와 동일).
    # 부분 실패 = 슬롯 보존(압축 금지) — slot N ≡ 🔗 첨부 순서 범례 N 불변이 다장의 핵심 계약(검증1 260708 · 실패 슬롯 = null → 뷰어 실패 칩).
    slots = []
    labels = ref_labels(md)
    for i, ref in enumerate(refs, 1):
        lab = labels[i - 1] if i <= len(labels) else ""
        kind = sheet_kind(lab)
        if kind:
            # 다각도 시트 한 장(한 컷 금지) · 가로 3:2 · 2K
            png = tg.gemini_image(ref + TURN_SPECS[kind], TURN_SIZE, tag="kref", aspect=TURN_ASPECT)
            print("참조 {}번({}) = 다각도 시트로 굽는다({} 문법 · 한 페이지)".format(i, lab, kind))
        else:
            png = tg.gemini_image(ref + REF_STYLE, "1K", tag="kref", aspect=aspect)
        slots.append(png)
        if not png:
            print("::warning::레퍼런스 {}번 생성 실패(비치명 — 슬롯 보존·나머지 계속)".format(i))
    if not any(slots):
        print("::warning::레퍼런스 이미지 전부 생성 실패(비치명)"); return 0
    # 값 원장(운영자 260811 「제미나이 호출하는것도 값에 넣어야지」) — 실패 슬롯은 안 센다(안 만든 건 안 낸다).
    #   ⚠ 이 파일은 k·콘티 두 레인 공용이라 원장 파일 하나가 더 생기는 것 말고는 k 레인 무접촉이다.
    try:
        import sb_cost as sc   # noqa: PLC0415
        sc.add(out_dir, "gemini", "ref", sum(1 for s in slots if s))
    except Exception:  # noqa: BLE001
        pass

    if tg.R2_ON:
        urls = []
        for i, png in enumerate(slots, 1):
            if png is None:
                urls.append(None); continue
            key = "{}/{}/ref.jpg".format(prefix, stem) if i == 1 else "{}/{}/ref_{}.jpg".format(prefix, stem, i)   # 키 인덱스 = 범례 번호 고정(첫 장 = ref.jpg 하위호환 — 1번 실패 시 ref.jpg 미생성이나 뷰어는 ref.json 우선이라 무해)
            url = tg.r2_upload(png, key, tg._img_type(png)[0] or "image/jpeg")   # Content-Type = 매직바이트 실측(Gemini는 보통 JPEG — 거짓 선언 방지 · 키는 하위호환 유지)
            urls.append(url)   # 실패 = None 그대로(슬롯 보존)
            if not url:
                print("::warning::레퍼런스 {}번 R2 업로드 실패(슬롯 null 보존)".format(i))
        if any(urls):
            first = next(u for u in urls if u)
            json.dump({"url": first, "urls": urls}, open(os.path.join(out_dir, "ref.json"), "w", encoding="utf-8"), ensure_ascii=False)   # url = 하위호환 첫 성공장 · urls = 범례 순 슬롯(null 포함 — 뷰어가 실패 칩 렌더)
            print("레퍼런스 → R2 {}/{}장: {}".format(sum(1 for u in urls if u), len(urls), first))
            return 0
        print("::warning::R2 업로드 전부 실패 → git 폴백")
    # git 폴백(로컬 ref.jpg — 성공 첫 장만: 다장 로컬 커밋은 레포 비대라 R2 전용 · 단수 렌더는 1:1 미주장이라 범례 어긋남 무해)
    oks = [p for p in slots if p]
    if len(oks) > 1:
        print("::warning::git 폴백 = 대표 1장만 저장(다장은 R2 시크릿 필요)")
    open(os.path.join(out_dir, "ref.jpg"), "wb").write(oks[0])
    print("레퍼런스 → git 로컬: {}/ref.jpg".format(out_dir))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("k_refgen 경고(무시·비치명): {}".format(e), file=sys.stderr)
        sys.exit(0)
