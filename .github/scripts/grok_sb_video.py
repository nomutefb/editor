#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""grok_sb_video.py — 콘티(board.md)를 컷마다 그림 → 영상으로 굽는다(촬영=grok 레인).

  grok_sb_video.py <board.md> <out_dir>

운영자 260811 확정 흐름:
  ① 운영자가 상황을 말한다(글 · 사진)
  ② **감독**(Fable 5 / Opus 5 / GPT 5.6 Sol)이 콘티를 짠다 = `sbmake.sh` 가 이미 하는 일
     → board.md 에 컷마다 `### 컷N · a~b s` + ACTION / CAMERA / DIALOGUE
  ③ **이 파일** = 컷마다 그림(Gemini) → 그 그림을 **첫 장면**으로 그록 영상
  ④ 결과가 sb_out/<id>/ 에 앉는다

⚠ 왜 컷마다 그림을 새로 굽나 = `## 🖼 레퍼런스` 절의 그림은 **인물·배경·키비주얼 몇 장**이지
  컷 그림이 아니다(sb-make.md 규약). 그록 이미지→영상은 **컷의 첫 프레임**을 요구하므로
  컷 수만큼 그림이 있어야 한다. 이 그림들이 곧 「스토리보드 컷」이기도 하다.

⚠ 컷 길이는 우리가 정하지 않는다 — **콘티가 이미 `0~2s` 로 적는다.** 그 값을 그대로 쓴다
  (운영자 260810 「10초 고정」은 **단독 영상 1편** 축이고, 콘티 컷은 컷마다 다르다 =
  10초를 컷에 그대로 박으면 12컷이 120초가 된다).

⚠ 프롬프트 조립 규칙 = `prompts/grok-make.md` 정본. 특히 §3 — 첫 프레임이 구도·조명·색을
  이미 확정하므로 프롬프트는 **무엇이 움직이는지만** 쓴다(재묘사는 희석).

CONTRACT: check_grok_sb_chain

fail-soft = 컷 하나가 죽어도 나머지는 간다. 전부 죽어도 콘티·레퍼런스는 그대로 남는다.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shared"))
import thumb_gen as tg          # noqa: E402  gemini_image · r2_upload · R2_ON (k_refgen 과 같은 배관)
import grok_api as gk           # noqa: E402  구독 자격 통로
import k_refgen as kr           # noqa: E402  extract_refs = 참조 블록 파서 단일정본(사본 0 · 순서 = ref.json 순서)

CUT_MAX = int(os.environ.get("GROK_SB_CUT_MAX", "12"))     # 한 번에 굽는 컷 상한(비용·시간 가드)
SEC_MIN, SEC_MAX = 1, 15                                   # 공식 허용 범위
SEC_FALLBACK = 5                                           # 콘티가 시각을 안 적었을 때

# 참조 그림 상한(운영자 260811 "3개 초과해서 만들면 실패고, 2개가 베스트야. 3개 뽑을 때는 이유가 있어야 해").
# ⚠ 그록 API 자체는 7장까지 받지만(gk.REF_MAX) 그건 기술 한도이지 우리 계약이 아니다.
#   그림 1장마다 제미나이 값이 나가고, 참조가 늘수록 「이 얼굴을 지켜라」의 힘이 오히려 흩어진다.
#   2장 = 인물 1 + 장소 1 이 기본이고, 3장은 **등장인물이 둘일 때만** 정당하다.
REF_CAP, REF_BEST = 3, 2

# 컷 머리 = `### 컷3 · 4~7s · 한 줄 설명`(sb-make.md 출력 형식) — 시각 표기는 없을 수도 있다
_CUT = re.compile(r"^###\s*컷\s*(\d+)\s*(?:·\s*([\d.]+)\s*~\s*([\d.]+)\s*s)?\s*(?:·\s*(.*))?$", re.M)
_FIELD = re.compile(r"^(ACTION|CAMERA|DIALOGUE|MOTION)\s*:\s*(.*)$", re.M)

def cuts_of(md):
    """board.md → [{n, sec, desc, action, camera, dialogue}] (문서 순)."""
    out, ms = [], list(_CUT.finditer(md))
    for i, m in enumerate(ms):
        body = md[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(md)]
        f = {k: v.strip() for k, v in _FIELD.findall(body)}
        sec = SEC_FALLBACK
        if m.group(2) and m.group(3):
            try:
                sec = round(float(m.group(3)) - float(m.group(2)))
            except ValueError:
                sec = SEC_FALLBACK
        out.append({
            "n": int(m.group(1)),
            "sec": max(SEC_MIN, min(SEC_MAX, sec or SEC_FALLBACK)),
            "desc": (m.group(4) or "").strip(),
            "action": f.get("ACTION", ""),
            # MOTION = 촬영=grok 전용 **영어** 동작 줄(감독이 쓴다). 없으면 ACTION 폴백.
            # ⚠ 왜 별도 필드인가 = ACTION 은 운영자가 화면에서 읽는 한국어인데, 그록 프롬프트는
            #   영어가 안전하다(정본 §4-4). 한 필드에 둘을 겸하게 하면 화면이 영어가 되거나
            #   프롬프트가 한국어가 된다 — 둘 다 손해라 축을 가른다.
            "motion": f.get("MOTION", ""),
            "camera": f.get("CAMERA", ""),
            "dialogue": f.get("DIALOGUE", ""),
        })
    return out


def refs_of(out_dir):
    """참조 그림 목록 = 콘티가 이미 구운 것들(`ref.json`). 추가 과금 0.

    운영자 260811 = 「어짜피 시트가 저화질이여도 캐릭터가 비슷하게 나오면 됨 · 첨부가 2개면
    시트 + 등장인물 고화질 표 두 개를 넣던지」 — 이게 정확히 그록 **참조 모드**다.
    참조 1장이 **한 축을 잠근다**(얼굴 · 물건 · 장소) · 최대 7장.

    ⚠ 왜 첫 프레임 모드를 안 쓰나 = 첫 프레임은 **1장뿐**이고 그 그림이 그대로 1프레임이 된다.
      컷 수만큼 그림을 새로 구워야 해서 그림 값이 컷 수배로 뛴다(운영자 지적 = 「의미없이 열
      몇 장을 만들어야 하잖아, 비용적으로 너무 손해」). 참조 모드는 **그림 몇 장을 컷 전체가
      공유**하므로 콜이 컷 수와 무관해진다.
    ⚠ 저화질 시트가 괜찮은 이유도 여기 있다 — 참조는 1프레임으로 박히는 게 아니라 「이 얼굴을
      유지하라」는 잠금이라 해상도 요구가 첫 프레임보다 낮다(운영자 판단과 일치).
    ⚠ 대가 = 구도는 고정되지 않는다. 그 컷의 구도는 프롬프트가 정한다.
    """
    try:
        d = json.load(open(os.path.join(out_dir, "ref.json"), encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    urls = [u for u in (d.get("urls") or []) if u]
    if not urls and d.get("url"):
        urls = [d["url"]]
    return urls[:REF_CAP]


# 참조 문장 앞머리 상투구 — 잘라내야 「무엇을 잠그는 그림인지」가 첫 낱말로 온다(창작 0 · 잘라내기만)
_REF_LEAD = re.compile(
    r"^(?:a\s+|an\s+|the\s+)?(?:cinematic\s+|editorial\s+|photoreal\w*\s+|moody\s+)*"
    r"(?:portrait|photograph|photo|shot|still|image|render)\s+of\s+", re.I)


def ref_ids(md, n):
    """참조 슬롯 n개를 **정체 문장**으로 묶는다 — `<IMAGE_0> 은 의수를 단 남자다` 식.

    ⚠ 왜 필요했나(260811 실측 사고) = 참조 모드는 얼굴·옷·장소를 잠그지만 「이 컷에서 **누가**
      움직이나」는 안 잠근다. 그 정보는 프롬프트 문장에만 있는데, 감독이 쓴 문장은 인물을
      `He` · `She` 로만 가리킨다. 인물 참조가 둘이면 대명사는 둘 중 누구든 될 수 있고,
      실제로 컷7에서 **남자가 응사하는 장면이 여자가 쏘는 장면으로 뒤집혔다**.
      → 슬롯 번호에 정체를 못 박아 대명사가 갈 곳을 하나로 만든다.

    출처 = board.md `## 🖼 레퍼런스` 절의 영어 문장 그대로(k_refgen 과 **같은 파서·같은 순서**라
    슬롯 번호가 어긋날 수 없다). 새 문장 창작 0 · 앞머리 상투구만 잘라 짧게 만든다.
    """
    outs = []
    for i, b in enumerate(kr.extract_refs(md)[:n]):
        one = " ".join(b.split())
        one = _REF_LEAD.sub("", one)
        cut = one[:150]
        if len(one) > 150:                      # 낱말 중간이 아니라 쉼표에서 끊는다
            cut = cut[:cut.rfind(",")] if "," in cut else cut.rsplit(" ", 1)[0]
        outs.append("<IMAGE_{}> shows {}.".format(i, cut.rstrip(" .,")))
    return outs


def vid_prompt(c, sound=True, nrefs=0, ids=None):
    """컷 영상 프롬프트 — 정본 `prompts/grok-make.md` 규칙 적용.

    ⚠ **바뀌는 것만 쓴다**(§3-1). 첫 프레임이 구도·조명·색을 이미 쥐고 있어서 그걸 다시 쓰면
      강화가 아니라 희석이다. 그래서 desc(장면 묘사)는 **일부러 뺀다** — ACTION(무엇이 움직이나)과
      CAMERA(어떻게 보나) 둘만 간다.
    ⚠ 어순 = 시간순(§0-②). 동작을 첫 문장에 둔다.
    ⚠ 소리 = 안 적으면 제네릭 배경음악이 붙는다(§0-③) → 켜기면 명시, 끄기면 4수법(§4-3).
    """
    parts = []
    if nrefs:
        # 참조 지목 = **0부터** 센다(공식 2거처 일치 · 260810 확인). 첫 장이 <IMAGE_0>.
        # 잠금 지시문은 묘사가 아니라 명령이라 희석 축에 안 걸린다(정본 §3-1 예외).
        # ⚠ **맨 앞이 자리다.** 그록 이미지 엔진은 앞에서 뒤로 읽어 나가므로(자기회귀 · 정본 §0-①)
        #   등장 인물표를 동작 문장 **뒤에** 두면 `He` 를 읽는 시점에 그 낱말이 가리킬 대상이
        #   아직 없다. 260811 실측에서 컷7 이 정확히 그렇게 뒤집혔다(남자 응사 → 여자 사격).
        parts.extend(ids or [])
        tags = ", ".join("<IMAGE_{}>".format(i) for i in range(nrefs))
        parts.append("Keep the people, wardrobe, and setting identical to {}.".format(tags))
    mv = c.get("motion") or c["action"]   # 영어 줄 우선 · 없으면 한국어라도 보낸다(fail-soft)
    if mv:
        parts.append(mv.rstrip(". ") + ".")
    if c["camera"]:
        parts.append(c["camera"].rstrip(". ") + ".")
    if sound:
        # 컷이 대사를 적었어도 **말소리는 넣지 않는다** — 이미지→영상은 립싱크가 구조적으로
        # 불리하고(§4-3), 실존 인물 축 위험도 여기서 함께 차단된다(§7-3 ①).
        parts.append("Sound: ambient room tone and the natural sounds of the action, no music.")
    else:
        # 끄기 = 4수법을 순서대로(마지막 부정문만 단독으로 쓰면 역효과 · §4-3)
        parts.append("Lips still and sealed, calm neutral expression.")
        parts.append("The only sounds are faint ambient room tone. No spoken words.")
    return " ".join(parts)


def _why(e):
    """실패 사유를 **사람 말로** 옮긴다 — 코드만 남기면 운영자가 다음 수를 못 정한다.

    ⚠ 이 레포가 세 번 봉합한 병(사유 0자 경보)과 같은 축이라, 분류를 못 해도 원문을 싣는다.
    """
    b = str(e.body)
    if e.where == "video-moderated" or "moderat" in b.lower():
        return "검열에 걸렸다 — 같은 문장으로 다시 쏴도 안 풀린다. 컷 내용을 바꿔야 한다(사람·폭력·실사 어휘 축)"
    if e.tier_blocked:
        return "구독은 살아 있는데 xAI 가 영상 통로를 이 계정에 안 열어줬다(403) — 재시도 무의미"
    if e.dead_auth:
        return "자격이 죽었다 — 판정기를 다시 돌려 열쇠를 새로 받아야 한다"
    if e.code == 429:
        return "한도에 걸렸다 — 잠시 뒤 손으로 다시 시도하면 된다"
    if e.where == "video-timeout":
        return "15분 안에 안 끝났다 — 서버가 밀린 상태다. 손으로 다시 시도"
    if e.code in (500, 502, 503, 504) or e.code == 0:
        return "서버·회선 일시 장애({}) — 손으로 다시 시도하면 대개 풀린다".format(e.code or "연결 실패")
    return "HTTP {} · {}".format(e.code, b[:160])


def strip_audio(path):
    """소리 끄기 = 산출 트랙을 버린다.

    ⚠ 프롬프트 무음 지시에 기대지 않는다 — 그록 영상 API 에 오디오 끄기 값이 없고,
      xAI 스스로 「무음 프롬프트가 실패할 수 있다」고 인정했다(정본 §4-1). 이게 확실한 수단이다.
    """
    out = path[:-4] + "_mute.mp4"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-c", "copy", "-an", out],
                       capture_output=True)
    if r.returncode == 0 and os.path.getsize(out) > 0:
        os.replace(out, path)
        return True
    print("::warning::소리 제거 실패(원본 유지): {}".format(r.stderr.decode("utf-8", "replace")[:200]))
    return False


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: grok_sb_video.py <board.md> <out_dir>")
    md_path, out_dir = sys.argv[1], sys.argv[2]
    md = open(md_path, encoding="utf-8").read()
    stem = os.path.basename(os.path.normpath(out_dir))
    prefix = os.environ.get("REFGEN_PREFIX", "sb_out")
    sound = (os.environ.get("GROK_SOUND", "1") != "0")

    cuts = cuts_of(md)[:CUT_MAX]
    if not cuts:
        print("::warning::컷을 못 찾았다(board.md 형식 확인) — 영상 생략")
        return 0
    print("컷 {}개 · 소리 {}".format(len(cuts), "켜기" if sound else "끄기"))

    if not tg.KEY:
        print("::warning::GEMINI_API_KEY 미등록 — 컷 그림을 못 굽는다(영상 생략)")
        return 0
    try:
        token = gk.fresh_token()
    except gk.GrokError as e:
        # 자격 실패는 여기서 끝낸다 — 사유를 원문 그대로 남긴다(추적 가능성 = 이 레포 계약).
        print("::warning::그록 자격 실패({}) — 영상 생략".format(e))
        return 0

    refs = refs_of(out_dir)
    ids = ref_ids(md, len(refs)) if refs else []
    # 참조 장수 계약(운영자 260811) — 2장이 기본 · 3장은 이유가 있을 때만 · 3장 초과는 실패다.
    #   이유 = 「인물이 몇 명인가」로 기계 판정한다(콘티 참조 절이 「인물:」·「배경:」으로 라벨을 단다).
    people = len(re.findall(r"^\s*[①-⑦]\s*인물\s*[:：]", md, re.M))
    if len(refs) > REF_BEST:
        reason = ("등장인물 {}명 + 장소 1 = 슬롯 {}".format(people, len(refs)) if people >= REF_BEST
                  else "인물 {}명뿐인데 참조가 {}장이다 — 줄일 여지가 있다".format(people, len(refs)))
    else:
        reason = "기본({}장 이하)".format(REF_BEST)
    if not refs:
        # ⚠ 콘티가 그림을 안 구웠으면(레퍼런스 OFF·Gemini 실패·R2 미설정) 참조가 0장이다.
        #   그래도 발사는 한다 — 그록이 컷 설명만으로 첫 장면을 스스로 만든다(텍스트→영상).
        #   다만 인물·화풍이 컷마다 흔들리므로 그 사실을 남긴다.
        print("::warning::참조 그림 0장(ref.json 없음) — 인물·화풍이 컷마다 흔들린다")
    else:
        print("참조 {}장 공유(컷 수와 무관 = 그림 값 고정) · 사유 {}".format(len(refs), reason))
        for s in ids:
            print("  · {}".format(s))

    items, spent = [], 0.0
    for c in cuts:
        rec = {"n": c["n"], "sec": c["sec"], "desc": c["desc"], "refs": len(refs), "video": None}
        try:
            rid = gk.start_video(vid_prompt(c, sound, len(refs), ids), token=token,
                                 refs=refs or None, seconds=c["sec"])
            v = gk.wait_video(rid, token=token)
            spent += float(v.get("cost_usd") or 0)
            raw = gk.fetch(v["url"])
            local = os.path.join(out_dir, "cut{:02d}.mp4".format(c["n"]))
            open(local, "wb").write(raw)
            if not sound:
                strip_audio(local)
            vkey = "{}/{}/cut{:02d}.mp4".format(prefix, stem, c["n"])
            rec["video"] = tg.r2_upload(open(local, "rb").read(), vkey, "video/mp4") if tg.R2_ON else None
            if rec["video"]:
                os.remove(local)   # R2 로 갔으면 레포에 안 남긴다(레포 비대 0 = k_refgen 관례)
            print("컷{} ✓ {}초 · {}".format(c["n"], c["sec"], rec["video"] or local))
        except gk.GrokError as e:
            # ⚠ 자동 재시도 없음(운영자 260811) — 다시 쏘면 돈이 또 나가고, 검열 차단은
            #   같은 프롬프트로 몇 번을 쏴도 안 풀린다. 대신 **막힌 이유를 사람 말로 남겨**
            #   운영자가 보고 손으로 다시 시도할지 정한다.
            rec["fail"] = _why(e)
            print("::warning::컷{} 영상 실패 — {}".format(c["n"], rec["fail"]))
            if e.tier_blocked or e.dead_auth:
                # 자격 축이면 남은 컷도 전부 같은 이유로 죽는다 → 돈·시간을 더 쓰지 않는다.
                print("::warning::자격 축 실패 — 남은 컷 중단")
                items.append(rec)
                break
        items.append(rec)

    done = sum(1 for r in items if r.get("video"))
    for r in items:
        if not r.get("video") and not r.get("fail"):
            r["fail"] = r.get("fail") or "그림 단계에서 막혔다(위 경고 참조)"
    json.dump({"cuts": items, "done": done, "total": len(cuts), "sound": sound,
               "cost_usd": round(spent, 4), "refs": len(refs), "ref_reason": reason},
              open(os.path.join(out_dir, "video.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("영상 {}/{}컷 · 청구 {} 달러(컷당 {})".format(
        done, len(cuts), round(spent, 4), round(spent / done, 4) if done else 0))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        # ⚠ 전면 fail-soft = 영상이 실패해도 콘티·레퍼런스 산출은 그대로 살아야 한다.
        print("::warning::grok_sb_video 예외(비치명): {}".format(str(e)[:300]))
        sys.exit(0)
