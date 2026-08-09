#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""과거 편집 산출물 포스터 백필 — 작업 내역 타일이 <img> 한 장으로 뜨게 만드는 1회성 채움기.

▷ 왜 필요한가(운영자 260810 "썸네일 불러오는게 항상 그렇게 폰이 뜨거워져야돼? 그때 썸네일이 만들어지는것도
  아니고" → "아니면 영상 제작시 썸네일을 따로만들게 하던가"):
  신규분은 `ly_burn.poster_jpg`가 제작 때 굽지만, 이미 만들어진 과거 산출물엔 포스터가 없다. 그대로 두면
  과거 타일이 전부 빈 플레이트가 되거나(화면 후퇴) 구판처럼 영상 본체를 받아야 한다(발열 = 애초 그 지적).
  → R2에 살아 있는 결과 영상에서 **첫 프레임만** 뽑아 git에 채운다.

▷ 핵심 = ffmpeg에 R2 URL을 직접 물린다. `-ss 0.1 -frames:v 1`이면 파일 전체가 아니라 앞부분만 받는다
  (실측: 71MB .mov 건도 프레임 1장에 수 초). 로컬 다운로드 → 추출 → 삭제 왕복이 없다.

▷ 산출 = viewer/ly_out/<id>/poster.jpg (JPEG q90 · 640px 상한 = gen_image.post_process 정본 동값)
  ⚠ 신규분은 R2로 가고(레포 용량 0) 이 백필분만 git에 남는다 — 인덱서(build-viewer.mjs)가 둘 다 인식한다.

사용: python3 shared/ly_poster_backfill.py [--limit N] [--force]
"""
import concurrent.futures as cf
import io
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LY = os.path.join(ROOT, "viewer", "ly_out")
MAXW = 640          # 타일 실측 최대폭 178.7px의 여유 배수(원본이 더 작으면 그대로)
TIMEOUT = 180       # 큰 원본(실측 71MB .mov)도 첫 프레임은 앞부분만 받는다


def to_jpg90(png_bytes):
    """PNG → JPEG q90·4:4:4 (CONTRACT: check_image_format — thumb_gen.to_jpg90 / gen_image.post_process 정본 동값)."""
    from PIL import Image
    im = Image.open(io.BytesIO(png_bytes))
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=90, optimize=True, subsampling=0)
    return buf.getvalue()


def src_url(v):
    """포스터를 뜯을 미디어 = 결과물 우선(화면에 뜨는 그림과 같아야 한다) → 알파 미리보기 → 원본.
    ⚠ 브라우저 재생 가능 여부는 따지지 않는다 — ffmpeg는 .mov도 읽는다(그 제약은 <video> 축이었다)."""
    for k in ("url", "preview", "src"):
        u = v.get(k)
        if isinstance(u, str) and u.startswith("http"):
            return u
    return ""


def one(job):
    jid, url, dst = job
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "0.1", "-i", url, "-frames:v", "1",
                            "-vf", "scale='min({},iw)':-2".format(MAXW), tmp],
                           capture_output=True, timeout=TIMEOUT)
        if r.returncode != 0 or not os.path.getsize(tmp):
            return (jid, False, (r.stderr.decode("utf-8", "replace") or "")[:110])
        with open(tmp, "rb") as f:
            jpg = to_jpg90(f.read())
        with open(dst, "wb") as f:
            f.write(jpg)
        return (jid, True, "{} KB".format(len(jpg) // 1024))
    except Exception as e:
        return (jid, False, str(e)[:110])
    finally:
        try:
            if tmp and os.path.isfile(tmp):
                os.remove(tmp)
        except Exception:
            pass


def main():
    force = "--force" in sys.argv
    limit = 0
    for i, a in enumerate(sys.argv):
        if a == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
    jobs = []
    for jid in sorted(os.listdir(LY), reverse=True):
        d = os.path.join(LY, jid)
        vp = os.path.join(d, "video.json")
        if not os.path.isdir(d) or not os.path.isfile(vp):
            continue
        dst = os.path.join(d, "poster.jpg")
        if os.path.isfile(dst) and not force:
            continue
        try:
            v = json.load(open(vp, encoding="utf-8"))
        except Exception:
            continue
        if v.get("poster"):          # 이미 R2 포스터 보유(신규분) = git 사본 불필요
            continue
        u = src_url(v)
        if u:
            jobs.append((jid, u, dst))
    if limit:
        jobs = jobs[:limit]
    print("· 백필 대상 {}건".format(len(jobs)))
    ok = bad = 0
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for jid, good, note in ex.map(one, jobs):
            if good:
                ok += 1
                print("  ✅ {} {}".format(jid, note))
            else:
                bad += 1
                print("  ⚠ {} — {}".format(jid, note))
    print("· 완료 = 성공 {} · 실패 {}".format(ok, bad))
    return 0                          # fail-soft: 일부 실패해도 나머지는 채운다(타일은 플레이트로 강등·무해)


if __name__ == "__main__":
    sys.exit(main())
