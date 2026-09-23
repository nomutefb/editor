#!/usr/bin/env python3
"""자막 폰트 줄 배치 수치 산출기(운영자 260923 "미리보기 글자 크기 맞춰줘") — ly_burn.BOX_K · viewer/edit.html FONT_PV{lh,dsc,bk} 의 생성 코드.

  lh  = (usWinAscent + usWinDescent) / unitsPerEm   — libass 는 자막 크기를 이 줄 높이로 정규화한다(글자 본체 = 크기 ÷ lh)
  dsc = usWinDescent / (usWinAscent + usWinDescent)  — 기준선 = 줄 상자 아랫변에서 dsc × 크기 위
  bk  = ((윈어센트 − 잉크 위) − (윈디센트 − 잉크 아래)) / (2 × 줄 높이) — 줄 상자 가운데 대비 한글 잉크 가운데(+ = 아래)
        잉크 = KS X 1001 상용 한글 2,350자 글리프 윗변·아랫변의 75% 분위 — 실제 자막(viewer/ly_out 1,674줄 · 러너 청킹 뒤 한 줄 3~10자)의
        줄별 값 중앙값과 전 폰트 ≤0.12px@1920(90% 분위 = 긴 줄 편향 ≤0.66px · 260923 평의회 2 대조) · 폰트 파일만으로 재현(말뭉치 불요)
  emb = 1/(128 × lh) — 굵은 면이 없어 libass 가 합성 굵게를 거는 폰트(usWeightClass + 150 < 700)만: FreeType 굵게(em/64)는 윗변만 올려
        잉크 가운데가 em/128 위로 간다(실렌더 윗변 −0.9~−1.0px@fs72 · 아랫변 0) → 러너 BOX_K 에서만 뺀다(크롬 합성 굵게는 위아래 대칭 = 미리보기 bk 는 그대로)
  lf  = (영문 하강부 g·j·p·q·y 최대 깊이 ÷ 줄 높이) − dsc — 끝 줄에 하강부 글자가 있으면 러너가 박스 오프셋을 lf × 크기 아래로 막는다
        (= 박스 아랫변 ≥ 하강부 + pad/2 · 한글 중심 보정이 박스를 올리는 폰트에서 g·p·y 가 아랫변에 닿지 않게 · ly_burn.LAT_K)

폰트 파일 = **러너가 실제로 고르는 파일**(libass fontselect 로그로 대조 · 굵은 면이 없는 폰트는 러너도 그 파일에 합성 굵게).
사용: python3 shared/sub_font_metrics.py [키=폰트파일[#ttc번호] ...] [--check]
      fontTools 필요(개발용 · CI 밖) · 기본 경로 = 러너(ubuntu apt + 레포 동봉) · 없는 파일은 건너뛴다
      --check = 저장소 값(ly_burn.BOX_K · edit.html FONT_PV)과 대조(허용 ±0.0005 · 불일치 = 종료코드 1)
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBS = os.path.join(ROOT, "assets", "fonts", "subs")
NOTO = "/usr/share/fonts/opentype/noto"
NANUM = "/usr/share/fonts/truetype/nanum"
FONTS = {   # 키 = ly_burn.FONT_FAMILY 키 · 값 = (파일, ttc 번호)
    "pretendard": (os.path.join(SUBS, "Pretendard-Bold.otf"), 0),
    "gothic": (os.path.join(NOTO, "NotoSansCJK-Bold.ttc"), 1),        # ttc 1번 = Noto Sans CJK KR
    "serif": (os.path.join(NOTO, "NotoSerifCJK-Bold.ttc"), 1),
    "paper": (os.path.join(SUBS, "Paperlogy-5Medium.ttf"), 0),
    "nanum": (os.path.join(NANUM, "NanumGothicExtraBold.ttf"), 0),   # fonts-nanum-extra 가 있으면 libass 는 굵게 = ExtraBold 를 고른다
    "pen": (os.path.join(NANUM, "NanumPen.ttf"), 0),                  # fonts-nanum-extra(구글 웹폰트판과 윤곽 같고 줄 높이만 다름)
    "barun": (os.path.join(NANUM, "NanumBarunGothicBold.ttf"), 0),
    "plex": (os.path.join(SUBS, "IBMPlexSansKR-Bold.ttf"), 0),
    "jua": (os.path.join(SUBS, "Jua-Regular.ttf"), 0),
    "gowun": (os.path.join(SUBS, "GowunDodum-Regular.ttf"), 0),
}


def ks_hangul():
    out = []
    for hi in range(0xB0, 0xC9):
        for lo in range(0xA1, 0xFF):
            try:
                out.append(bytes([hi, lo]).decode("cp949"))
            except UnicodeDecodeError:
                pass
    return out


def metrics(path, index=0, q=0.75):
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.ttLib import TTFont
    f = TTFont(path, fontNumber=index)
    upem = f["head"].unitsPerEm
    os2 = f["OS/2"]
    a, d = os2.usWinAscent / upem, os2.usWinDescent / upem
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    tops, bots = [], []
    for ch in ks_hangul():
        g = cmap.get(ord(ch))
        if not g:
            continue
        pen = BoundsPen(gs)
        gs[g].draw(pen)
        if pen.bounds:
            tops.append(pen.bounds[3] / upem)
            bots.append(-pen.bounds[1] / upem)
    tops.sort()
    bots.sort()
    t, b = tops[int(len(tops) * q)], bots[int(len(bots) * q)]
    lat = []
    for ch in "gjpqy":
        g = cmap.get(ord(ch))
        if g:
            pen = BoundsPen(gs)
            gs[g].draw(pen)
            if pen.bounds:
                lat.append(-pen.bounds[1] / upem)
    ld = max(lat) if lat else 0.0
    syn = os2.usWeightClass + 150 < 700   # libass 합성 굵게 조건(요청 700 > 면 굵기 + 150)
    return {"lh": round(a + d, 3), "dsc": round(d / (a + d), 4), "bk": round(((a - t) - (d - b)) / (2 * (a + d)), 4),
            "lf": round(ld / (a + d) - d / (a + d), 4), "emb": round(1 / (128 * (a + d)), 4) if syn else 0.0}


def repo_values():
    sys.path.insert(0, os.path.join(ROOT, ".github", "scripts"))
    sys.path.insert(0, os.path.join(ROOT, "shared"))
    os.environ.setdefault("OPTS", "{}")
    import ly_burn
    with open(os.path.join(ROOT, "viewer", "edit.html"), encoding="utf-8") as fh:
        html = fh.read()
    pv = {k: {"lh": float(a), "dsc": float(b), "bk": float(c)}
          for k, a, b, c in re.findall(r"\n  (\w+):\{lbl:'[^']*',lh:([0-9.]+),dsc:([0-9.]+),bk:(-?[0-9.]+),", html)}
    return ly_burn.BOX_K, ly_burn.EMB_K, ly_burn.LAT_K, pv


def main(argv):
    fonts = dict(FONTS)
    check = "--check" in argv
    for arg in argv:
        if "=" in arg:
            k, p = arg.split("=", 1)
            path, _, idx = p.partition("#")
            fonts[k] = (path, int(idx or 0))
    got = {}
    for k, (path, idx) in fonts.items():
        if not os.path.exists(path):
            print("  %-10s 건너뜀(파일 없음: %s)" % (k, path))
            continue
        got[k] = metrics(path, idx)
        print("  %-10s lh=%.3f dsc=%.4f bk=%+.4f emb=%.4f lf=%+.4f" % (k, got[k]["lh"], got[k]["dsc"], got[k]["bk"], got[k]["emb"], got[k]["lf"]))
    print("BOX_K = {%s}" % ", ".join('"%s": %s' % (k, v["bk"]) for k, v in got.items()))
    print("EMB_K = {%s}" % ", ".join('"%s": %s' % (k, v["emb"]) for k, v in got.items() if v["emb"]))
    print("LAT_K = {%s}" % ", ".join('"%s": %s' % (k, v["lf"]) for k, v in got.items()))
    if not check:
        return 0
    box_k, emb_k, lat_k, pv = repo_values()
    bad = []
    for k, v in got.items():
        if k in box_k and abs(box_k[k] - v["bk"]) > 0.0005:
            bad.append("BOX_K[%s] %s ≠ %s" % (k, box_k[k], v["bk"]))
        if abs(emb_k.get(k, 0.0) - v["emb"]) > 0.0005:
            bad.append("EMB_K[%s] %s ≠ %s" % (k, emb_k.get(k, 0.0), v["emb"]))
        if k in lat_k and abs(lat_k[k] - v["lf"]) > 0.0005:
            bad.append("LAT_K[%s] %s ≠ %s" % (k, lat_k[k], v["lf"]))
        for m in ("lh", "dsc", "bk"):
            if k in pv and abs(pv[k][m] - v[m]) > 0.0005:
                bad.append("FONT_PV.%s.%s %s ≠ %s" % (k, m, pv[k][m], v[m]))
    print("\n".join(bad) if bad else "✅ 저장소 값 = 산출값(%d폰트)" % len(got))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
