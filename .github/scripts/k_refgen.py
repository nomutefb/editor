#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k_refgen.py — /k(영상 프롬프트)·콘티(sb) 레퍼런스 이미지 '직영' 생성.

  k_refgen.py <prompt.md> <out_dir>
  env REFGEN_PREFIX(R2 키 접두 · 기본 k_out) · REFGEN_ASPECT(생성 비율 · 기본 16:9)
      REFGEN_SHEET=0(다각도 시트 승격 끄기 = 전부 낱장 = 260814 이전 동작)

⚠ 이 파일은 **k 레인과 콘티 레인 공용**이다 — 260814 다각도 시트 승격은 두 레인에 같이 걸린다
  (라벨에 「인물」·「제품」·「주요 장소」가 있을 때만 발동 · 끄는 값 = REFGEN_SHEET=0).

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
    " Lay the panels out as one page, same subject design, same lighting and same color grade in EVERY"
    " panel. Print only the short panel header labels in Korean with the English in parentheses,"
    " no other in-image text, no hex codes, no captions, no watermark, no logos."
)
# ⚠ 사람 칸 구성 = 운영자가 준 견본 다섯 장 실측 그대로다(260814). 다섯 장 전부 ⓐ 왼쪽에 **큰 정면**이
#   있고 ⓑ **뒷모습 칸은 없다**. 그래서 「큰 정면 금지 · 뒤 추가」로 적었던 첫 판을 회수했다 —
#   운영자 말(「큼지막한 게 하나 있는 게 아니라 360도 기록이 더 중요」)은 큰 정면을 없애라는 게 아니라
#   그 한 컷으로 끝내지 말라는 뜻이었고, 견본이 그 둘을 같이 갖고 있다(모방 1순위 = 견본이 정본).
#   패널 6개 = master-sheet-v2 §V2 철칙(「패널 ≤ 6 · 더 넣으면 깨진다」) 준수.
TURN_SPECS = {
    "person": (" ONE CHARACTER TURNAROUND SHEET on a dark grey studio background: a LARGE 정면(FRONT)"
               " portrait filling the left side, and beside it 3/4 (45 degrees), 측면(SIDE) profile and"
               " 전신(FULL BODY) head to shoe; along the bottom 달리기(RUN) a full-body running pose with"
               " motion blur, and 표정(EXPRESSION) a row of 3 head close-ups (calm, alarmed, smiling)."
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

# ⚠⚠ 콘티 레인 인물 시트 = **견본이 정본**(운영자 260817 「인물보드는 샘플 따라하는게 맞아」) —
#   견본 두 판(`9-1`·`9-2`) 실측이 위 글 규격과 **두 자리에서 정면으로 어긋났다**:
#     ⓐ 배경이 스튜디오 회색이 아니라 **그 이야기 장면**이고 칸들이 하나의 배경으로 이어진다
#        (실측 = 비 오는 밤 편의점 앞·강변 · 젖은 머리·젖은 옷 상태까지 전 칸 동일)
#     ⓑ 다섯째 칸이 판마다 다르다(9-1 건네기(OFFER) · 9-2 처마밑(SHELTER)) = 「그 이야기의 핵심 동작」
#   → 그 **두 자리의 고정값만 뺀다**(값을 새로 지어내지 않고 「위 서술을 따르라」로 넘긴다).
#   ⚠ 칸 배치·큰 정면·번호는 **안 건드린다** — 견본끼리도 배치가 갈리고(9-1 상단 균등 · 9-2 전신
#     세로), 260814 에 「큰 정면 금지」로 적었다가 견본 실측으로 회수한 자리라 글로 또 뒤집으면
#     같은 축을 세 번째로 왕복한다. 배치는 **견본 그림이 정한다**(그림이 참조로 실려 있다).
#   ⚠ k 레인은 이 변형을 안 쓴다(위 `TURN_SPECS["person"]` 스튜디오 규격 그대로 = 무회귀).
TURN_SPEC_PERSON_SB = (
    " ONE CHARACTER TURNAROUND SHEET set INSIDE the story's own location and time of day as described"
    " above — NOT a studio backdrop: a LARGE 정면(FRONT) portrait filling the left side, and beside it"
    " 3/4 (45 degrees), 측면(SIDE) profile and 전신(FULL BODY) head to shoe; along the bottom one"
    " ACTION panel showing THIS character's key action from the description above (label that panel in"
    " Korean with the English in parentheses), and 표정(EXPRESSION) a row of 3 head close-ups."
    " Every panel shares one continuous background of that same scene, and the character's wardrobe,"
    " hair and its state (wet, dishevelled, carrying the same props) stay identical throughout."
    + _SHEET_COMMON)

# ── 콘티 레인(sb) 전용 축(운영자 260817) ─────────────────────────────────────
# ⓐ 「그림 산출은 항상 스토리보드 1 + 핵심 인물 시트 n **만**」 — 배경·장소·제품 슬롯은 콘티
#    레인에서 안 굽는다(환경 디자인은 스토리보드 시트에 녹인다 · 촬영 참조도 그 두 종만).
# ⓑ 「둘 다 샘플 참조」 — 인물 시트에 판형 견본(`apps/storyboard/샘플/캐릭터 시트 (1).png`)을
#    그림 참조로 싣는다. 구판은 견본 다섯 장을 **글로 옮긴 규격**(TURN_SPECS)만 썼고 그림
#    자체는 한 번도 안 실렸다(sb_sheet 견본 배선과 같은 병 = 한 정본을 두 층이 다르게 쓰던 자리).
# ⓒ 「콘티에 참조할 사진」 — 감독이 라벨에 `(사진 N)` 이라 **선언한 슬롯만** 그 사진을 얼굴
#    정본으로 싣는다(추측 0 = 다각도 시트 라벨 신청 원칙 동축 · 파일 = 같은 폴더 photo_N.jpg).
# ⚠ 전부 sb 레인 한정(REFGEN_PREFIX=sb_out) — k 레인은 종전 동작 무접촉(무회귀).
_PHOTO_LAB = re.compile(r"사진\s*([0-9]{1,2})")
PHOTO_CLAUSE = (
    "The FIRST attached image is a real photograph of this exact person, supplied by the operator. "
    "Treat it as the identity source: keep the face, hair, build and overall look of THIS person "
    "identical in every panel.\n\n")
SAMPLE_CLAUSE_P = (
    "The LAST attached image(s) are our house LAYOUT SAMPLES for a character turnaround sheet "
    "(several samples = variants of the SAME house format). Copy only their structure — the numbered "
    "panel grid, the four view panels across the top (front / three-quarter / side / full body), one "
    "story-specific ACTION panel and a row of three expression heads, the header label style and the "
    "way the panels share one continuous background. Do NOT copy the samples' person, wardrobe, "
    "colors, location or any text from them.\n\n")


def person_sample():
    """인물 시트 판형 견본 **목록** — 읽기 정본 = sb_sheet.sample_png(축소·재인코딩 한 벌 · 사본 0)."""
    try:
        from sb_sheet import sample_png  # noqa: PLC0415  지연 import — k 레인에 이 의존이 없어도 죽지 않게(fail-soft)
        return sample_png("person")
    except Exception as e:  # noqa: BLE001
        print("::warning::인물 시트 견본 읽기 실패(견본 없이 굽는다): {}".format(str(e)[:120]))
        return []


def photo_bytes(label, out_dir):
    """라벨의 (사진 N) 선언 → 운영자 사진 bytes(없으면 None) — 선언 없는 슬롯엔 안 싣는다."""
    m = _PHOTO_LAB.search(label or "")
    if not m:
        return None
    p = os.path.join(out_dir, "photo_{}.jpg".format(int(m.group(1))))
    if not os.path.exists(p):
        print("::warning::라벨이 사진 {}번을 가리키는데 파일이 없다({}) — 사진 없이 굽는다".format(m.group(1), p))
        return None
    try:
        return open(p, "rb").read()
    except OSError:
        return None


def lane_bake(lab, sb_lane):
    """이 슬롯을 굽나 — 콘티 레인은 인물만 True(운영자 260817 · k 레인은 전부 True = 무회귀)."""
    return (sheet_kind(lab) == "person") if sb_lane else True

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


_FENCE = re.compile(r'```[^\n]*\n(.*?)\n```', re.S)


def ref_pairs(md):
    """참조 절을 **순서대로 훑어** (라벨, 블록) 짝을 만든다.

    ⚠ 구판은 라벨과 블록을 **각자 findall** 해서 같은 인덱스로 짝지었다 — 블록 없는 라벨 평문이
      한 줄만 있어도(지침이 허용한다) 뒤 짝이 통째로 한 칸 밀려 **여자 인물 블록에 「배경」 라벨**이
      붙는다(평의회 260814 실측). 그러면 그 사람은 다각도 시트로 안 구워지고 밤 필터에 걸려
      편에서 빠진다. 짝은 **바로 다음 블록**에만 붙인다.
    ⚠ 절이 없으면 빈 목록이다 — 구판은 문서 전체를 뒤져 컷 본문의 각주를 유령 라벨로 물었다.
    """
    m = re.search(r'##\s*🖼\s*레퍼런스\s*\n(.*?)(?=\n##\s|\Z)', md, re.S)
    if not m:
        return []
    sec, out, lab = m.group(1), [], ""
    pos = 0
    for f in _FENCE.finditer(sec):
        head = sec[pos:f.start()]
        got = _REF_LABEL.findall(head)
        lab = got[-1].strip() if got else ""      # 블록 **직전** 라벨만이 그 블록의 이름이다
        if len(got) > 1:
            print("::warning::참조 절에 블록 없는 라벨이 있다({}) — 짝은 바로 앞 라벨로 붙인다".format(
                " · ".join(x.strip() for x in got[:-1])))
        out.append((lab, f.group(1).strip()))
        pos = f.end()
    return out[:7]


def ref_labels(md):
    """참조 절 라벨을 블록과 **같은 순서**로 돌려준다(사본 0 = 슬롯 번호가 갈릴 여지 0)."""
    return [lab for lab, _ in ref_pairs(md)]


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
    out = [b for _, b in ref_pairs(md) if b]
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
    sb_lane = (prefix == "sb_out")   # 콘티 레인 = 인물 시트만 + 견본·사진 참조(운영자 260817 · k 레인 무접촉)
    psample = person_sample() if sb_lane else None
    for i, ref in enumerate(refs, 1):
        lab = labels[i - 1] if i <= len(labels) else ""
        kind = sheet_kind(lab) if os.environ.get("REFGEN_SHEET") != "0" else None
        if not lane_bake(lab, sb_lane):
            # 콘티 레인 비인물 슬롯 = 값도 안 나가게 건너뛴다(환경 = 스토리보드 시트가 정본 ·
            # 감독 계약이 어긋나 배경 블록이 와도 여기가 2겹째 방어선) · 슬롯 번호는 보존(None).
            print("참조 {}번({}) = 콘티 레인 비인물 슬롯 — 안 굽는다(스토리보드가 환경 정본 · 260817)".format(i, lab or "무라벨"))
            slots.append(None)
            continue
        if kind:
            refps, clause = [], ""
            if kind == "person" and sb_lane:
                pb = photo_bytes(lab, out_dir)
                if pb:
                    refps.append(pb); clause += PHOTO_CLAUSE
                if psample:
                    # ⚠ 견본은 **여러 장**이다(sb_sheet.SAMPLES person = 9-1·9-2·종전판) —
                    #   append 로 두면 목록이 통째로 한 장 자리에 들어가 첨부가 깨진다.
                    refps.extend(psample); clause += SAMPLE_CLAUSE_P
            # 다각도 시트 한 장(한 컷 금지) · 가로 3:2 · 2K
            # ⚠ 콘티 레인 인물만 견본 정본 규격(스튜디오·달리기 고정 없음) — 나머지는 종전 그대로
            _spec = (TURN_SPEC_PERSON_SB if (kind == "person" and sb_lane) else TURN_SPECS[kind])
            png = tg.gemini_image(clause + ref + _spec, TURN_SIZE, tag="kref",
                                  aspect=TURN_ASPECT, ref_png=(refps or None))
            print("참조 {}번({}) = 다각도 시트로 굽는다({} 문법 · 한 페이지{}{})".format(
                i, lab, kind, " · 사진 정본" if (refps and clause.startswith("The FIRST")) else "",
                " · 판형 견본" if psample and kind == "person" else ""))
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
