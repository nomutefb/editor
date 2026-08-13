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
import io
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shared"))
import thumb_gen as tg          # noqa: E402  gemini_image · r2_upload · R2_ON (k_refgen 과 같은 배관)
import lane as ln               # noqa: E402  촬영 통로 **계약** 정본(설계 M3 §2·§3)
import k_refgen as kr           # noqa: E402  extract_refs = 참조 블록 파서 단일정본(사본 0 · 순서 = ref.json 순서)
import sb_cost as sc            # noqa: E402  벤더별 값 원장(제미나이 그림값까지 합산 = 운영자 260811)

# ⚠ 통로(촬영 레인) = 이 러너는 벤더를 직접 부르지 않는다. 계약만 부르고 구현은 통로 파일이 채운다
#   (설계 M3 · 페이블 3인 검증 = 벤더 결합이 직접 5지점 + 간접 10곳으로 흩어져 있어 두 번째 통로를
#    붙이는 순간 한 곳만 빠져도 조용히 다른 동작이 되는 상태였다).
LANE = ln.pick()                                           # SB_LANE env · 기본 grok

# ⚠ **빈 값과 없는 값은 다르다** — 발사 폼이 「안 정함」을 빈 글자로 보내는데, 없을 때만 기본값을
#   쓰는 방식이면 빈 글자가 그대로 숫자 변환으로 들어가 **러너가 첫 줄에서 죽는다**(260812 실사고
#   = 콘티·참조 그림은 다 나왔는데 영상만 0편 · 이 줄이 함수 밖이라 아래 fail-soft 그물에도 안 걸렸다).
#   같은 모양이 이 레인에 5곳 있었고 전부 「빈 값이면 기본값」으로 바꿨다.
CUT_MAX = int(os.environ.get("GROK_SB_CUT_MAX") or "12")     # 한 번에 굽는 컷 상한(비용·시간 가드)
SEC_MAX = LANE.SEC_MAX                                     # 엔진 허용 상한(통로 값 · SHOT_SEC 과 다른 축)
# ⚠ **컷 1개 = 10초 고정**(운영자 260812 「고정임 더 짧을수도 없고 그냥 고정」 ·
#   「보드를 항상 10초를 기준으로 구성해서 10초짜리를 여러개 만드는거로」).
#   구판은 콘티가 적은 `0~2s` 를 그대로 썼는데, 그 컷 수 규칙이 **종이 콘티용**이라
#   15초를 12칸으로 나눴고 결과가 1.2초 조각 열두 개였다(260811 실측). 칸 수는 종이에선
#   정상이지만 칸마다 영상을 뽑는 순간 호흡이 통째로 끊긴다 → 길이 축을 코드가 고정한다.
#   총 길이 = 10 × 컷 수. 콘티는 컷을 10초 단위로만 나눈다(prompts/sb-make.md 동기).
CUT_SEC = LANE.SHOT_SEC                                    # 한 발 단위 초(통로 값)
SEC_FALLBACK = CUT_SEC                                     # 콘티가 시각을 안 적었을 때도 같은 값

# 참조 그림 상한(운영자 260811 "3개 초과해서 만들면 실패고, 2개가 베스트야. 3개 뽑을 때는 이유가 있어야 해").
# ⚠ 통로 기술 한도(LANE.REF_CAP_TECH · 그록 7)는 우리 계약이 아니다.
#   그림 1장마다 제미나이 값이 나가고, 참조가 늘수록 「이 얼굴을 지켜라」의 힘이 오히려 흩어진다.
#   2장 = 인물 1 + 장소 1 이 기본이고, 3장은 **등장인물이 둘일 때만** 정당하다.
REF_CAP, REF_BEST = 3, 2

# 참조 그림을 **바이트로 실어 보낸다**(운영자 260812 「애초에 실패를 안 하게 어떻게든 조치하는 게 우선」).
# ⚠ 실사고 = 260812 `260812-bushouse-lib` 영상1이 `image_download_error=image_download_interrupted`
#   로 죽었다 — 우리가 보낸 건 **주소**였고, 그 주소를 내려받는 주체는 **xAI 서버**다. 그 다운로드가
#   중간에 끊기면 우리 코드·프롬프트가 전부 정상이어도 그 편이 통째로 실패한다(같은 그림으로 영상2·3은
#   성공 = 그림도 주소도 멀쩡했다 = 남의 회선 딸꾹질 하나에 10초가 날아간다).
#   → 바이트를 요청 본문에 실으면 **그 다운로드 자체가 없어져** 이 실패 종류가 구조적으로 사라진다
#     (`grok_api._imgref` 가 이미 원바이트를 `data:` 형태로 정규화한다 = 새 배관 0).
# ⚠ 대가 = 본문이 커진다(그림 1장 ≈ 0.9MB → base64 ≈ 1.2MB). 상한을 넘는 장은 **줄여서** 싣는다
#   (참조 모드 산출이 720p 상한이라 긴 변 1280 이면 충분 · 품질은 레포 계약 q90).
# ⚠ 몸집 축으로 거절당하면(413·payload) 재시도가 **주소 방식으로 갈아타** 종전 동작으로 착지한다.
REF_EMBED = (os.environ.get("GROK_REF_EMBED", "1") != "0")          # 롤백 레버 = env 1줄
#   ⚠ 몸집 상한·축소 규격은 **통로 값**이다(lane_grok.EMBED_MAX·EMBED_SIDE) — 벤더마다 다르다.

# 실패한 **그 편만** 1회 자동 재시도(운영자 260812 「1회는 실패한 부분만 다시 쏘는 배선을 하고,
# 초과해서 실패 시 사용자에게 알리게」). 구판은 재시도 0이었다(260811 판단) — 그 판단의 전제는
# 「다시 쏘면 돈이 또 나간다」였는데, 실측상 **실패한 호출은 청구가 0**이라(260812 = 실패 1편의
# cost 필드 자체가 없다) 전제가 틀렸다. 성공했을 때만 돈이 나가므로 1회 재시도는 공짜에 가깝다.
# ⚠ 재시도는 **그 편만** 다시 쏜다 — 이미 성공한 편은 손대지 않는다(돈·시간 재지출 0).
# ⚠ 다시 쏴도 같은 벽인 축(검열·자격·통로)은 재시도하지 않는다 = `_retryable()`.
RETRY_ONCE = (os.environ.get("GROK_RETRY", "1") != "0")
RETRY_WAIT = int(os.environ.get("GROK_RETRY_WAIT") or "20")           # 서버가 숨 돌릴 틈(초)
# ⚠⚠ **재시도의 전제는 통로마다 다르다**(260812 페이블 검증 = 치명 2건 중 하나).
#   위 문단의 「공짜에 가깝다」는 **그록 실측**이고, 그 사실을 통로가 `FAIL_COSTS` 로 말한다.
#   그런데 재시도 분기가 그 값을 **한 번도 안 읽고 있었다** = 계약이 선언만 되고 강제가 없는 상태.
#   값을 모르는 통로(시댄스 = 환불 여부 미확인)에서 이 전제를 그대로 쓰면 두 가지로 돈이 샌다 —
#   ⓐ 실패분이 환불 안 되면 재시도가 곧 두 배 청구 ⓑ 더 나쁜 축 = 「실패로 보이지만 **제출은
#   성공**」한 경우(작업 번호를 못 읽음·기다리기 시한)가 재시도의 주 고객이라, 환불과 무관하게
#   **성공한 발사 두 개** 값이 나간다. → 실패가 공짜라고 **통로가 말한 경우에만** 자동 재시도.
RETRY_PAID = (os.environ.get("SB_RETRY_PAID") == "1")               # 값이 나가도 재시도(손 레버)

# 컷 머리 = `### 컷3 · 4~7s · 한 줄 설명`(sb-make.md 출력 형식) — 시각 표기는 없을 수도 있다
_CUT = re.compile(r"^###\s*컷\s*(\d+)\s*(?:·\s*([\d.]+)\s*~\s*([\d.]+)\s*s)?\s*(?:·\s*(.*))?$", re.M)
_FIELD = re.compile(r"^(ACTION|CAMERA|DIALOGUE|MOTION|SFX)\s*:\s*(.*)$", re.M)

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
            "sec": max(1, min(SEC_MAX, sec or 2)),   # 콘티가 적은 값 그대로(묶기가 10초를 만든다)
            "desc": (m.group(4) or "").strip(),
            "action": f.get("ACTION", ""),
            # MOTION = 촬영=grok 전용 **영어** 동작 줄(감독이 쓴다). 없으면 ACTION 폴백.
            # ⚠ 왜 별도 필드인가 = ACTION 은 운영자가 화면에서 읽는 한국어인데, 그록 프롬프트는
            #   영어가 안전하다(정본 §4-4). 한 필드에 둘을 겸하게 하면 화면이 영어가 되거나
            #   프롬프트가 한국어가 된다 — 둘 다 손해라 축을 가른다.
            "motion": f.get("MOTION", ""),
            "camera": f.get("CAMERA", ""),
            "dialogue": f.get("DIALOGUE", ""),
            # SFX = 그 컷에서 실제로 나는 소리(영어 · 감독이 적는다). 없으면 뭉뚱그린 지시로 폴백한다.
            "sfx": f.get("SFX", ""),
        })
    return out


def group_shots(cuts, sec=None):
    """콘티 컷을 **10초짜리 영상**으로 묶는다 — 이게 이 레인의 발사 단위다.

    ⚠ 운영자 260812 = 「10초가 1컷이라기보다는 **10초가 하나의 영상**이고, 그 안에 다채로운
      컷을 감독 프롬프트에 따라 구성할 수 있는 거다. 2초마다 카메라 구도를 바꿔 10초 안에
      2초컷이 5개 들어가는 느낌을 만들었다면 **한 번에 5컷**일 수 있다.」
    ⚠ 그래서 「컷」과 「영상」은 다른 축이다 — 컷은 카메라가 바뀌는 지점이고, 영상은 한 번 쏘는
      단위다. 구판은 둘을 겸하게 해서 **컷 하나가 곧 호출 하나**였고, 그 결과 종이 콘티 칸 수를
      그대로 받아 1.2초 조각이 열두 개 나왔다(260811 실측).
    ⚠ 값도 이쪽이 싸다 — 호출당 $0.03 이 붙으므로 30초를 3발로 쏘면 12발보다 $0.27 아낀다.
      다만 **값이 이 설계의 이유는 아니다**(그건 어제 내가 잘못 판단했던 축이다) — 이유는
      한 클립 안에서 흐름이 이어지는 것이고, 클립 사이는 모델이 앞을 못 봐서 늘 끊긴다.

    반환 = [{"n": 영상번호, "sec": 10, "cuts": [그 안의 컷들]}]
    """
    sec = sec or CUT_SEC
    shots, cur, acc = [], [], 0
    for c in cuts:
        cur.append(c)
        acc += c["sec"]
        if acc >= sec:
            shots.append({"n": len(shots) + 1, "sec": sec, "cuts": cur, "cut_sec": acc})
            cur, acc = [], 0
    if cur:   # 꼬리 = 10초에 못 미쳐도 한 편으로 쏜다(길이는 늘 10초 = 10의 배수 계약)
        shots.append({"n": len(shots) + 1, "sec": sec, "cuts": cur, "cut_sec": acc})
    return shots


def receipt(out_dir, rec):
    """발사 영수증을 **기다리기 전에** 파일로 떨군다.

    ⚠ 왜 필요했나(260813 실사고) = 30초 한 발이 19분을 돌던 중 러너가 시간 벽에 잘렸다.
      값은 이미 나갔는데 산출은 마지막에 한 번에 쓰는 구조라 **작업 번호가 어디에도 안 남았다**
      = 다 만들어진 영상을 우리 손으로는 영영 못 찾는다(벤더 화면을 사람이 열어야만 보인다).
    ⚠ 그래서 「번호를 아는 순간」과 「결과를 아는 순간」을 가른다 — 앞의 것은 즉시 적는다.
      잘리든 죽든 이 파일은 남고, 다음 판이 그 번호로 결과만 받아 올 수 있다.
    """
    try:
        path = os.path.join(out_dir, "jobs.json")
        try:
            with open(path, encoding="utf-8") as f:
                cur = json.load(f)
        except Exception:  # noqa: BLE001
            cur = {"lane": LANE.NAME, "jobs": []}
        cur["jobs"] = [x for x in cur.get("jobs", []) if x.get("n") != rec["n"]] + [
            {"n": rec["n"], "job": rec.get("job"), "sec": rec.get("sec")}]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cur, f, ensure_ascii=False)
        print("  · 영수증 {}편 = {}".format(rec["n"], rec.get("job")))
    except Exception as e:  # noqa: BLE001
        print("::warning::영수증 기록 실패(비치명): {}".format(str(e)[:140]))


def board_fit(shots):
    """콘티 컷 경계가 이 통로의 한 발 길이와 맞물리나 — 안 맞으면 **이름을 대고 경고**한다.

    ⚠ 왜 필요했나 = 콘티 규약이 컷을 10초 단위로 쓰는데, 통로에 따라 한 발이 15초일 수 있다.
      그러면 20초어치 컷이 15초 클립 하나로 들어가 프롬프트가 「10~20초에 이 일이 벌어진다」고
      적힌 채 15초짜리로 나간다 = 모델에게 앞뒤가 안 맞는 지시를 주는 것이고, 증상은 「좀
      이상하게 나왔다」뿐이라 사람 눈이 유일한 검출기가 된다.
    """
    bad = [s for s in shots if abs((s.get("cut_sec") or s["sec"]) - s["sec"]) > 0.5]
    if bad:
        print("::warning::콘티 컷 경계가 한 발 {}초와 안 맞는다 — {}편이 어긋난다({}). "
              "컷 초 합을 {}의 배수로 짠 콘티를 쓰거나 한 발이 {}초인 프리셋으로 쏴라".format(
                  CUT_SEC, len(bad),
                  " · ".join("영상{} 컷합 {}초→{}초".format(s["n"], s.get("cut_sec"), s["sec"]) for s in bad[:3]),
                  CUT_SEC, int(bad[0].get("cut_sec") or CUT_SEC)))
    return not bad


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
    urls = list(d.get("urls") or [])
    if not any(urls) and d.get("url"):
        urls = [d["url"]]
    return urls          # ⚠ 실패 슬롯 None 을 **그대로** 남긴다 = 콘티 참조 절 번호와 1:1(ref_slots 가 짝짓는다)


# 참조 슬롯 라벨 = 콘티 `## 🖼 레퍼런스` 절의 「① 인물:」·「② 배경:」·「③ 배경(밤):」
_REF_LABEL = re.compile(r"^\s*[①-⑳]\s*([^\n:：]{1,30})\s*[:：]", re.M)
# 밤 축 어휘 — 시간대가 갈리는 자리(콘티 라벨·참조 문장 어느 쪽에 적혀도 잡는다)
_NIGHT = re.compile(r"night|nocturnal|after\s*dark|밤|야간|야경|심야", re.I)


# 콘티 머리의 `비율: 16:9` 한 줄 — 감독이 선언하는 화면 규격
_RATIO = re.compile(r"^비율\s*[:：]\s*(\d+\s*:\s*\d+)", re.M)


def ratio_of(md):
    """콘티가 선언한 비율을 그대로 읽는다.

    ⚠ 실사고(260812 발견) = 구판은 이 줄을 **아예 안 읽었다**. 콘티 머리에 `비율: 9:16` 이라
      적어도 러너가 전달을 안 해서 통로 기본값(가로)으로 나갔다 — 세로로 만들 방법이 코드에
      없었던 것이다. 참조 그림은 세로로 굽고 있었으므로(레퍼런스 기본 9:16) **그림은 세로 ·
      영상은 가로**로 갈린 채 살아 있었다. 쇼츠(세로 30초)가 산출 규격이 되는 순간 이건
      그대로 사고다.
    ⚠ 값 창작 0 = 콘티가 적은 값을 그대로 쓰고, 통로가 못 받는 값이면 기본값으로 내려앉되
      **그 사실을 남긴다**(조용한 강등 금지).
    """
    m = _RATIO.search(md)
    if not m:
        return None
    r = m.group(1).replace(" ", "")
    if r not in LANE.RATIOS:
        print("::warning::콘티 비율 {} 는 통로가 안 받는다(허용 {}) — 기본값으로 간다".format(r, LANE.RATIOS))
        return None
    return r


def is_night(x):
    """이 컷(또는 참조 문장)이 밤을 말하는가."""
    if isinstance(x, dict):
        x = " ".join(str(x.get(k, "")) for k in ("desc", "action", "motion", "camera"))
    return bool(_NIGHT.search(str(x)))


def ref_slots(md, out_dir):
    """참조 슬롯 = [{url, label, block, night, bg}] — ref.json 순서 ≡ 콘티 참조 절 순서.

    ⚠ 구판은 `refs_of` 가 실패 슬롯(None)을 **걸러서** 반환하고 정체 문장은 콘티 앞에서부터 n개를
      떼어 썼다 — 1번 그림이 실패하면 슬롯 번호가 통째로 한 칸 밀려 `<IMAGE_0>` 이 엉뚱한 인물을
      가리킨다(대명사 뒤바뀜 사고와 같은 축). 여기서 **번호로 짝지어** 그 구멍을 막는다.
    """
    urls = refs_of(out_dir)
    sec = md.split("## 🖼", 1)[-1].split("\n## ", 1)[0] if "## 🖼" in md else md
    labels = _REF_LABEL.findall(sec)
    blocks = kr.extract_refs(md)
    out = []
    for i, u in enumerate(urls):
        if not u:
            continue                                   # 그림이 실패한 슬롯 = 보낼 게 없다
        lab = labels[i].strip() if i < len(labels) else ""
        blk = blocks[i] if i < len(blocks) else ""
        out.append({"url": u, "label": lab, "block": blk,
                    "night": is_night(lab) or is_night(blk),
                    "bg": ("배경" in lab or "장소" in lab)})
    return out[:REF_CAP]


def pick_refs(slots, shot):
    """이 **편**에 실을 참조를 고른다 — 밤 컷이면 밤 배경, 아니면 낮 배경(인물은 늘 간다).

    ⚠ 왜 필요했나(260812 실측) = 배경 참조가 **해질녘 한 장뿐**이었는데 콘티 3편 중 마지막이
      밤이었다. 참조는 얼굴·옷만이 아니라 **조명·시간대까지** 잠그므로 밤 컷이 해질녘으로 나왔다
      (운영자 「콘티에 밤 있으면 그것도 해야지」). 참조를 시간대별로 나눠 두고 편마다 골라 쓰면
      **한 편에 실리는 장수는 그대로 2장**이라 장수 계약(2 기본)도 안 깨진다.
    ⚠ 밤 참조가 없으면 종전 동작 = 전부 그대로 보낸다(무회귀).
    """
    if not any(s["night"] for s in slots):
        return slots
    night = any(is_night(c) for c in shot["cuts"])
    return [s for s in slots if not s["bg"] or s["night"] == night]


# 참조 문장 앞머리 상투구 — 잘라내야 「무엇을 잠그는 그림인지」가 첫 낱말로 온다(창작 0 · 잘라내기만)
_REF_LEAD = re.compile(
    r"^(?:a\s+|an\s+|the\s+)?(?:cinematic\s+|editorial\s+|photoreal\w*\s+|moody\s+)*"
    r"(?:portrait|photograph|photo|shot|still|image|render)\s+of\s+", re.I)


def ref_ids(blocks):
    """고른 참조들을 **정체 문장**으로 묶는다 — `<IMAGE_0> 은 의수를 단 남자다` 식.

    ⚠ 왜 필요했나(260811 실측 사고) = 참조 모드는 얼굴·옷·장소를 잠그지만 「이 컷에서 **누가**
      움직이나」는 안 잠근다. 그 정보는 프롬프트 문장에만 있는데, 감독이 쓴 문장은 인물을
      `He` · `She` 로만 가리킨다. 인물 참조가 둘이면 대명사는 둘 중 누구든 될 수 있고,
      실제로 컷7에서 **남자가 응사하는 장면이 여자가 쏘는 장면으로 뒤집혔다**.
      → 슬롯 번호에 정체를 못 박아 대명사가 갈 곳을 하나로 만든다.

    출처 = board.md `## 🖼 레퍼런스` 절의 영어 문장 그대로(k_refgen 과 **같은 파서·같은 순서**라
    슬롯 번호가 어긋날 수 없다). 새 문장 창작 0 · 앞머리 상투구만 잘라 짧게 만든다.

    ⚠ 번호는 **이 편에 실제로 실리는 순서**로 매긴다 — 편마다 배경 참조가 갈리므로(밤·낮)
      콘티 전체 번호를 그대로 쓰면 `<IMAGE_1>` 이 안 보낸 그림을 가리킨다.
    """
    outs = []
    for i, b in enumerate(blocks):
        if not b:
            continue
        one = " ".join(b.split())
        one = _REF_LEAD.sub("", one)
        cut = one[:150]
        if len(one) > 150:                      # 낱말 중간이 아니라 쉼표에서 끊는다
            cut = cut[:cut.rfind(",")] if "," in cut else cut.rsplit(" ", 1)[0]
        # ⚠ 슬롯 지목 문법은 **통로마다 다르다** — 그록은 `<IMAGE_0>` 로 번호를 부르고, 시댄스는
        #   그 문법을 받는지 미확인이라 순서말(첫 번째 참조)로 쓴다. 러너가 그록 문법을 박고
        #   있으면 통로가 일부러 뺀 문법이 되살아난다(260812 페이블 검증).
        outs.append(LANE.ref_id_clause(i, cut.rstrip(" .,")))
    return outs


def vid_prompt(shot, sound=True, nrefs=0, ids=None):
    """영상 **한 편**(10초)의 프롬프트 — 그 안의 컷을 시간순으로 이어 쓴다.

    ⚠ 자리 = 등장 인물표 → 잠금 → **컷 시퀀스** → 소리(정본 `prompts/grok-make.md`).
      인물표가 맨 앞인 이유는 이미지 엔진이 앞에서 뒤로 읽어서다 — 뒤에 두면 `He` 를 읽는
      시점에 가리킬 대상이 없다(260811 실측 = 남녀가 뒤바뀌었다).
    ⚠ 컷이 여러 개면 **시각을 붙여 시간순으로** 쓴다(`0-2s: … 2-4s: …`). 한 클립 안의 전환은
      모델이 그 시각에 맞춰 끊어 준다 = 운영자가 말한 「10초 안에 2초컷 5개」가 이 형태다.
    ⚠ 컷이 하나면 시각을 안 붙인다 — 한 호흡짜리에 눈금을 치면 오히려 끊어 그린다.
    ⚠ 장면 묘사(구도·조명·색)는 **일부러 뺀다** — 참조 그림이 이미 쥐고 있어 재묘사는 희석이다.
    """
    parts = []
    cuts = shot.get("cuts") or [shot]
    if nrefs:
        parts.extend(ids or [])
        parts.append(LANE.ref_lock_clause(nrefs))   # 참조 잠금 절 = 통로 문법(벤더마다 다르다)

    multi, t = len(cuts) > 1, 0
    for c in cuts:
        seg = []
        mv = c.get("motion") or c.get("action") or ""
        if mv:
            seg.append(mv.rstrip(". ") + ".")
        if c.get("camera"):
            seg.append(c["camera"].rstrip(". ") + ".")
        if seg:
            body = " ".join(seg)
            parts.append("{}-{}s: {}".format(t, t + c["sec"], body) if multi else body)
        t += c["sec"]

    # 소리 절 = 통로 문법. 끄기의 확실한 수단은 프롬프트가 아니라 산출 트랙 제거이고,
    # 그 판단(무엇을 문장으로 쓰고 무엇을 후처리로 막나)이 벤더마다 다르다.
    sfx = [c.get("sfx", "").strip().rstrip(". ") for c in cuts if (c.get("sfx") or "").strip()]
    parts.extend(LANE.sound_clause(sound, sfx))
    return " ".join(parts)


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


def stitch(paths, out_path):
    """컷 조각을 **한 편으로 이어붙인다** — 외부 호출 0 = 추가 과금 0.

    ⚠ 왜 필요했나 = 이 레인의 산출이 지금까지 **조각 12개**였다. 운영자가 화면에서 받으면
      12번 받아서 직접 붙여야 했고, 그건 「여기서 끝까지 간다」는 콘티 레인의 성격과 어긋난다
      (첫 실호출 18.5초 완본도 사람이 손으로 붙인 것이지 레인이 낸 게 아니었다).
    ⚠ 왜 흐름 복사가 아니라 다시 굽나 = 그록 산출에는 표지 그림 트랙(mjpeg)이 같이 들어 있어
      복사 이어붙이기가 그 트랙에서 깨진다(실측). 영상·소리 첫 줄만 집어 다시 굽는다.
    ⚠ 조각은 그대로 둔다 — 컷 단위로 다시 쓰거나 한 컷만 갈아 끼우는 게 이 레인의 쓰임이다.
    """
    if len(paths) < 2:
        return None
    lst = out_path + ".txt"
    try:
        with open(lst, "w", encoding="utf-8") as f:
            for p in paths:
                f.write("file '{}'\n".format(os.path.abspath(p).replace("'", "'\\''")))
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                            "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart", out_path], capture_output=True)
        if r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return out_path
        print("::warning::이어붙이기 실패(조각은 그대로 산다): {}".format(
            r.stderr.decode("utf-8", "replace")[:220]))
    except Exception as e:  # noqa: BLE001
        print("::warning::이어붙이기 예외(비치명): {}".format(str(e)[:200]))
    finally:
        try:
            os.remove(lst)
        except OSError:
            pass
    return None


MSG_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shared", "msg.py")
# 조치문 규약(👉 문단) — 알림 리포트의 조치주체 분류(`viewer/index.html _rptWho`)는 **👉 문단이 있어야**
#   「운영자가 할 일」로 가른다. 없으면 폴백이 「클로드가 볼 일」이라, 코드로는 못 고치는 이 건
#   (= 벤더 쪽 일시 실패라 다시 쏘는 것 말고 할 게 없다)이 클로드 칸에 앉아 진짜 코드 건을 가린다.
#   문법은 `yt_cookie_health.COOKIE_TODO` 100% 계승(창작 0).
# ⚠ 재시도 여부는 **건마다 다르다** — 값이 나갈 수 있는 통로는 자동 재시도를 안 하고(`RETRY_PAID`),
#   `retryable=False` 실패도 재시도 없이 바로 온다. 구판은 이 문구가 고정이라 **재시도한 적 없는 건에도
#   "한 번 자동으로 다시 쏴 보고도 막혔다"고 단언**했다(260813 실측 = 참조 올리기 실패 건은 재시도 0회).
#   그러면 운영자가 「기계가 두 번 해봤는데도 안 됐구나」로 읽어 다시 쏘기를 포기한다 = 조치를 막는 거짓말.
VID_TODO_RETRIED = ("\n\n👉 네가 할 일: 콘티 화면에서 같은 콘티를 다시 쏘면 돼. "
                    "여기까지 온 건 **한 번 자동으로 다시 쏴 보고도** 막힌 건이라, 코드가 더 할 수 있는 게 없어.")
VID_TODO_ONCE = ("\n\n👉 네가 할 일: 콘티 화면에서 같은 콘티를 다시 쏘면 돼. "
                 "이 건은 **자동 재시도를 안 하는 종류**라(값이 나갈 수 있거나 다시 해도 같은 자리에서 막히는 실패) "
                 "한 번 더 쏘는 건 네 손이 필요해.")


def notify(stem, items):
    """재시도까지 실패한 편이 있으면 **웹앱 알림**(운영자 260812 「기사 실패처럼 알림 오게」).

    ⚠ 왜 필요했나 = 260812 실사고에서 3편 중 1편이 죽었는데 **화면에는 아무 표시도 없었다** —
      실패 사유는 `video.json` 안에만 있고 그 파일은 운영자가 열 일이 없다. 20초짜리가 나왔으니
      「그냥 짧게 나왔나 보다」로 보이는 게 이 실패의 생김새다(= 조용히 나빠지는 축).
    ⚠ id 는 **콘티마다 회전**시킨다 — 고정 id 면 메시지함을 한 번 연 순간 그 알림이 읽음으로
      굳어 다음 실패가 영영 재점등되지 않는다(brk_misfire 실측 교훈).
    ⚠ 전건 성공이면 옛 알림을 끈다 = 다시 쏴서 해결된 건이 화면에 남아 있지 않는다.
    """
    bad = [r for r in items if not r.get("ok")]
    mid = "sb-video-fail-" + re.sub(r"[^A-Za-z0-9._-]", "_", stem)
    try:
        if not bad:
            subprocess.run([sys.executable, MSG_PY, "clear", mid], check=False)
            return
        lines = ["콘티 「{}」 영상 {}편이 안 나왔어(전체 {}편).".format(stem, len(bad), len(items))]
        for r in bad:
            lines.append("· 영상{} (컷 {}) — {}{}".format(
                r["n"], ", ".join(str(x) for x in r.get("cuts") or []),
                r.get("fail") or "사유 미기록", " · 자동 재시도 1회 후에도 실패" if r.get("retried") else ""))
            # ⚠ 창구 회신 **원문**을 알림에 싣는다(260813 실사고) — 산출 파일엔 `fail_body` 로 남기면서
            #   알림엔 우리말 요약만 실었더니, 「참조 그림을 창구에 못 올렸다(회신에 번호가 없다)」라고 말한
            #   그 회신 안에 **번호가 버젓이 들어 있었다**(실측 = "Pass media_id 6b474adc-… as medias[].value").
            #   원문이 없으면 운영자도 세션도 「벤더가 거절했나 보다」로 읽고 다시 쏘는 것 말고 할 게 없어지는데,
            #   실제로는 우리 파서가 못 읽은 것이라 **고칠 수 있는 코드 결함**이었다(= 조치 주체를 통째로 오도).
            #   이 레포가 반복해 겪은 「관측이 지워지는 병」과 같은 축(스레드 1차 실측·틱톡 _e1·요약 실패 _fk=code).
            if r.get("fail_body"):
                lines.append("  창구 회신 원문: {}".format(str(r["fail_body"])[:300]))
        ok = [r for r in items if r.get("ok")]
        if ok:
            lines.append("나온 {}편은 그대로 살아 있어(결과 레일에서 볼 수 있어).".format(len(ok)))
        todo = VID_TODO_RETRIED if any(r.get("retried") for r in bad) else VID_TODO_ONCE
        subprocess.run([sys.executable, MSG_PY, "set", mid, "\n".join(lines) + todo, "warn"], check=False)
        print("알림 발행 = {}".format(mid))
    except Exception as e:  # noqa: BLE001
        print("::warning::알림 발행 실패(비치명): {}".format(str(e)[:160]))


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: grok_sb_video.py <board.md> <out_dir>")
    md_path, out_dir = sys.argv[1], sys.argv[2]
    md = open(md_path, encoding="utf-8").read()
    stem = os.path.basename(os.path.normpath(out_dir))
    prefix = os.environ.get("REFGEN_PREFIX", "sb_out")
    sound = (os.environ.get("GROK_SOUND", "1") != "0")

    cuts = cuts_of(md)
    if not cuts:
        print("::warning::컷을 못 찾았다(board.md 형식 확인) — 영상 생략")
        return 0
    shots = group_shots(cuts)[:CUT_MAX]   # 발사 단위 = 영상 1편(10초) · 상한도 편 수로 센다
    ratio = ratio_of(md)                  # 콘티가 선언한 비율(없거나 통로가 못 받으면 None = 통로 기본값)
    print("콘티 컷 {}개 → 영상 {}편 × {}초 = 합 {}초 · 비율 {} · 소리 {}".format(
        len(cuts), len(shots), CUT_SEC, len(shots) * CUT_SEC,
        ratio or "통로 기본", "켜기" if sound else "끄기"))
    for sh in shots:
        print("  영상{} ← 컷 {}".format(sh["n"], [c["n"] for c in sh["cuts"]]))
    board_fit(shots)   # 컷 경계와 한 발 길이가 어긋나면 그 자리에서 이름을 대고 경고

    if not tg.KEY:
        print("::warning::GEMINI_API_KEY 미등록 — 컷 그림을 못 굽는다(영상 생략)")
        return 0
    try:
        token = LANE.fresh_token()
    except ln.LaneError as e:
        # 자격 실패는 여기서 끝낸다 — 사유를 원문 그대로 남긴다(추적 가능성 = 이 레포 계약).
        print("::warning::촬영 자격 실패({}) — 영상 생략".format(e.why))
        return 0

    slots = ref_slots(md, out_dir)
    # 참조 장수 계약(운영자 260811) — 2장이 기본 · 3장은 이유가 있을 때만 · 3장 초과는 실패다.
    #   이유 = 「인물이 몇 명인가」로 기계 판정한다(콘티 참조 절이 「인물:」·「배경:」으로 라벨을 단다).
    #   ⚠ 시간대가 갈리면(낮 배경 + 밤 배경) 만드는 장수는 3이어도 **한 편에 실리는 건 2장**이다.
    people = len(re.findall(r"^\s*[①-⑦]\s*인물\s*[:：]", md, re.M))
    nights = sum(1 for s in slots if s["night"])
    if len(slots) > REF_BEST:
        reason = ("시간대 2종(낮·밤 배경) + 인물 {}명 = 만든 장수 {} · 한 편에 {}장".format(
            people, len(slots), REF_BEST) if nights
            else "등장인물 {}명 + 장소 1 = 슬롯 {}".format(people, len(slots)) if people >= REF_BEST
            else "인물 {}명뿐인데 참조가 {}장이다 — 줄일 여지가 있다".format(people, len(slots)))
    else:
        reason = "기본({}장 이하)".format(REF_BEST)
    if not slots:
        # ⚠ 콘티가 그림을 안 구웠으면(레퍼런스 OFF·Gemini 실패·R2 미설정) 참조가 0장이다.
        #   그래도 발사는 한다 — 그록이 컷 설명만으로 첫 장면을 스스로 만든다(텍스트→영상).
        #   다만 인물·화풍이 컷마다 흔들리므로 그 사실을 남긴다.
        print("::warning::참조 그림 0장(ref.json 없음) — 인물·화풍이 컷마다 흔들린다")
    else:
        print("참조 {}장 · 사유 {}{}".format(
            len(slots), reason, " · 편마다 시간대에 맞는 배경을 고른다" if nights else ""))

    # ── 발사 전 견적 검문(과금 0) ──────────────────────────────────────────────
    # ⚠ 구판은 통로가 내주는 견적을 **한 번도 안 불렀다** — 12편 × 30초짜리 판이 아무 검문 없이
    #   통째로 나갈 수 있는 구조였다. 견적을 못 재는 통로(그록)는 None 을 주므로 그때는 종전대로.
    plan_sec = sum(c["sec"] for c in shots)
    try:
        one = LANE.estimate(shots[0]["sec"], ratio) if shots else None
    except Exception as e:  # noqa: BLE001
        one, _ = None, print("::warning::견적 실패(발사는 진행): {}".format(str(e)[:160]))
    if one is not None:
        # 편마다 길이가 다를 수 있으므로 초당으로 환산해 총액을 센다(길이 비례 = 실측 요율 문법).
        tot = one * (plan_sec / float(shots[0]["sec"] or 1))
        unit_nm = "크레딧" if LANE.COST_KIND == "credit" else "달러"
        print("견적 = {}편 {}초 = 약 {:.1f} {}(발사 전 · 크레딧 소모 0)".format(
            len(shots), plan_sec, tot, unit_nm))
        cap = float(os.environ.get("SB_COST_CAP") or 0)
        if cap and tot > cap:
            print("::warning::견적 {:.1f} {}가 상한 {:.0f}을 넘는다 — 발사하지 않는다"
                  "(SB_COST_CAP 을 올리거나 콘티를 줄여라)".format(tot, unit_nm, cap))
            return 0

    items, spent, locals_ = [], 0.0, []   # locals_ = 이어붙이기 재료(업로드 뒤에도 마지막까지 들고 있는다)
    stop = False
    for c in shots:
        # ⚠ 편마다 자격을 새로 받는다 — 접속 열쇠 수명이 **한 편 기다리는 시간보다 짧을 수 있다**
        #   (시댄스 실측 수명 15분 · 폴 상한 20분). 한 번 받아 끝까지 쓰면 뒤쪽 편이 자격 축으로
        #   죽고, 자격 축은 「남은 편도 전부 같은 벽」이라 멀쩡한 편까지 중단시킨다.
        #   통로가 아직 살아 있는 열쇠를 들고 있으면 그대로 돌려주므로 왕복 비용은 0에 가깝다.
        try:
            token = LANE.fresh_token()
        except ln.LaneError as e:
            print("::warning::자격 갱신 실패 — 남은 영상 중단: {}".format(e.why))
            break
        use = pick_refs(slots, c)                       # 이 편에 실을 참조(밤·낮이 갈리면 여기서 갈린다)
        ids = ref_ids([s["block"] for s in use]) if use else []
        rec = {"n": c["n"], "sec": c["sec"], "refs": len(use), "video": None,
               "cuts": [x["n"] for x in c["cuts"]],
               "desc": " / ".join(x["desc"] for x in c["cuts"] if x.get("desc"))}
        if use and any(s["night"] for s in slots):
            rec["ref_labels"] = [s["label"] or "?" for s in use]
        embed = REF_EMBED
        # ⚠ 발사 1회 + **실패한 그 편만** 1회 재시도(운영자 260812). 성공한 편은 손대지 않는다.
        for attempt in (1, 2):
            try:
                payload, mode = LANE.refs_payload([s["url"] for s in use], embed) if use else ([], "없음")
                rec["ref_mode"] = mode
                rid = LANE.start(vid_prompt(c, sound, len(use), ids), token=token,
                                 refs=payload or None, seconds=c["sec"], ratio=ratio, sound=sound)
                # ⚠ 작업 번호를 그 자리에서 남긴다 — 구판은 지역변수로 끝나서, 발사는 됐는데
                #   결과를 못 읽은 경우 **우리 산출물로는 회수할 길이 아예 없었다**(벤더 화면을
                #   사람이 열어야만 보였다). 나간 돈의 영수증 번호라 성패와 무관하게 적는다.
                rec["job"] = str(rid)[:80]
                receipt(out_dir, rec)   # ⚠ **기다리기 전에** 파일로 떨군다(아래 주석 참조)
                v = LANE.wait(rid, token=token)
                # ⚠ 컷별 값을 적는다(운영자 260811 「최적의 순간을 찾는다」) — 합계만 적혀 있으면
                #   「호출 1번에 고정인가 · 초당인가」를 영영 못 가른다(첫 판 실측 = 1초 6개 + 2초 6개
                #   합 $2.88 이 고정 $0.24 와 초당 $0.16 양쪽에 다 맞아떨어져 판별 불가였다).
                #   컷 길이가 서로 다른 판에서 컷별 값을 나란히 놓으면 그 자리에서 답이 나온다.
                one = float(v.get("cost") or 0)
                rec["cost"] = round(one, 4)
                rec["got_sec"] = v.get("duration")   # 서버가 실제로 만든 길이(요청 길이와 대조)
                spent += one
                raw = LANE.fetch(v["url"])
                local = os.path.join(out_dir, "shot{:02d}.mp4".format(c["n"]))
                open(local, "wb").write(raw)
                if not sound:
                    strip_audio(local)
                vkey = "{}/{}/shot{:02d}.mp4".format(prefix, stem, c["n"])
                rec["video"] = tg.r2_upload(open(local, "rb").read(), vkey, "video/mp4") if tg.R2_ON else None
                rec["ok"] = True   # ⚠ 성패 판정 축 = **영상을 손에 넣었나**(주소가 아니다) — 구판은
                #   `video`(R2 주소) 유무로 갈라서, 저장소가 꺼진 판에선 멀쩡히 나온 편도 실패로 세고
                #   실패 알림까지 발행했다(260812 오프라인 실측). 주소는 배달 축이라 성패와 별개다.
                locals_.append(local)   # ⚠ 지우는 건 이어붙인 **뒤**다(구판은 여기서 바로 지워 완본을 만들 재료가 없었다)
                rec.pop("fail", None)   # 1차가 죽고 2차가 살면 실패 표식을 지운다(산출은 성공이다)
                print("영상{} ✓ {}초 · ${} · 참조 {} · {}".format(
                    c["n"], c["sec"], rec["cost"], rec.get("ref_mode"), rec["video"] or local))
                break
            except ln.LaneError as e:
                rec["fail"] = e.why
                # ⚠ 회신 **원문**을 산출에 남긴다 — 통로가 body 에 원문을 실어 주는데 러너가
                #   그걸 버려서, 「작업 번호를 못 찾았다」류 실패에서 그 번호가 든 유일한 종이가
                #   사라지고 있었다(= 돈은 나갔는데 무엇이 나갔는지 회수 불가).
                if getattr(e, "body", ""):
                    rec["fail_body"] = str(e.body)[:600]
                free = (LANE.FAIL_COSTS is False) or RETRY_PAID
                if attempt == 1 and RETRY_ONCE and e.retryable and not free:
                    # 값이 나갈 수 있는 통로 = 자동 재시도 금지. 사유를 남겨 손으로 판단하게 한다.
                    print("::warning::영상{} 실패 — 이 통로는 실패분 값이 {}라 자동 재시도를 안 한다"
                          "(손으로 다시 쏘려면 SB_RETRY_PAID=1): {}".format(
                              c["n"], "미확인" if LANE.FAIL_COSTS is None else "청구됨", rec["fail"]))
                    rec["retry_skipped"] = "실패분 청구 미확인"
                if attempt == 1 and RETRY_ONCE and e.retryable and free:
                    # ⚠ 실패한 호출은 청구가 0이다(260812 실측) → 재시도 값 = 성공했을 때만 나간다.
                    #   몸집 축이면 방식을 갈아탄다(바이트 → 주소) = 두 실패 종류가 서로를 메운다.
                    if LANE.too_big(e) and embed:
                        embed = False
                        print("::warning::영상{} 본문이 크다고 거절 — 주소 방식으로 1회 다시 쏜다".format(c["n"]))
                    else:
                        print("::warning::영상{} 1차 실패 — 그 편만 1회 다시 쏜다: {}".format(c["n"], rec["fail"]))
                    rec["retried"] = True
                    time.sleep(RETRY_WAIT)
                    continue
                print("::warning::영상{} 실패({}차) — {}".format(c["n"], attempt, rec["fail"]))
                if e.auth_dead:
                    # 자격 축이면 남은 컷도 전부 같은 이유로 죽는다 → 돈·시간을 더 쓰지 않는다.
                    print("::warning::자격 축 실패 — 남은 영상 중단")
                    stop = True
                break
        items.append(rec)
        if stop:
            break

    done = sum(1 for r in items if r.get("ok"))
    for r in items:
        if not r.get("ok") and not r.get("fail"):
            r["fail"] = r.get("fail") or "그림 단계에서 막혔다(위 경고 참조)"
    # 완본 = 조각을 한 편으로(외부 호출 0 · 과금 0). 실패해도 조각은 그대로 살아 있다.
    full_url = None
    if len(locals_) >= 2:
        fp = stitch(locals_, os.path.join(out_dir, "full.mp4"))
        if fp:
            try:
                full_url = tg.r2_upload(open(fp, "rb").read(),
                                        "{}/{}/full.mp4".format(prefix, stem), "video/mp4") if tg.R2_ON else None
            except Exception as e:  # noqa: BLE001
                print("::warning::완본 업로드 실패(조각은 산다): {}".format(str(e)[:200]))
            if full_url:
                os.remove(fp)
            print("완본 {}컷 이어붙임 → {}".format(len(locals_), full_url or fp))
    for lp in locals_:   # R2 로 간 조각은 레포에 안 남긴다(레포 비대 0 = k_refgen 관례)
        if tg.R2_ON and os.path.exists(lp):
            try:
                os.remove(lp)
            except OSError:
                pass

    # ⚠ 값의 **단위**를 통로에서 받아 그대로 적는다 — 크레딧을 달러 칸에 적으면 화면이
    #   「청구 $195」라고, 그것도 실측인 척(est=False) 말한다(260812 페이블 검증 치명 1).
    sc.add(out_dir, LANE.NAME, "video", done, usd=spent, est=False, unit=LANE.COST_KIND)
    money = ({"cost_cr": round(spent, 2)} if LANE.COST_KIND == "credit"
             else {"cost_usd": round(spent, 4)})
    json.dump({"cuts": items, "shots": len(shots), "board_cuts": len(cuts),
               "done": done, "total": len(shots), "sound": sound,
               "cost_unit": LANE.COST_KIND, "lane": LANE.NAME,
               "refs": len(slots), "ref_reason": reason,
               "ratio": ratio,
               "full": full_url, **money},
              open(os.path.join(out_dir, "video.json"), "w", encoding="utf-8"), ensure_ascii=False)
    notify(stem, items)   # 재시도까지 실패한 편이 있으면 웹앱 알림 · 전건 성공이면 옛 알림을 끈다
    # 과금 단위 판별 — 컷 길이가 두 종류 이상이면 그 자리에서 답이 나온다(길이별 값이 같으면
    # 호출당 고정 · 길이에 비례하면 초당). 표본이 한 길이뿐이면 「판별 불가」라고 쓴다(추측 금지).
    by = {}
    for r in items:
        if r.get("cost") is not None:
            by.setdefault(r["sec"], []).append(r["cost"])
    unit = "판별 불가(컷 길이가 한 종류)"
    if len(by) >= 2:
        avg = {s: sum(v) / len(v) for s, v in by.items()}
        lo, hi = min(avg), max(avg)
        unit = ("호출당 고정" if abs(avg[hi] - avg[lo]) < 0.02
                else "초당 비례" if abs(avg[hi] / avg[lo] - hi / lo) < 0.25 else "혼합·불명")
        unit += " (" + " · ".join("{}초 ${:.4f}".format(s, avg[s]) for s in sorted(avg)) + ")"
    print("영상 {}/{}편 · 청구 {} {}(편당 평균 {}) · 과금 단위 = {}".format(
        done, len(shots), round(spent, 4), "크레딧" if LANE.COST_KIND == "credit" else "달러",
        round(spent / done, 4) if done else 0, unit))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        # ⚠ 전면 fail-soft = 영상이 실패해도 콘티·레퍼런스 산출은 그대로 살아야 한다.
        print("::warning::grok_sb_video 예외(비치명): {}".format(str(e)[:300]))
        sys.exit(0)
