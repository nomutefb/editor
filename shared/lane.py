#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lane.py — 촬영 통로 **계약** 단일정본(설계 M3 §2·§3).

러너(`grok_sb_video.py`)는 벤더를 직접 부르지 않는다. 이 파일이 정의한 계약만 부르고,
벤더별 구현(`lane_grok.py` · 앞으로 `lane_seedance.py`)이 그 계약을 채운다.

⚠ 왜 필요했나(260812 페이블 3인 검증) = 러너에 벤더 결합이 **직접 5지점 + 간접 10곳**으로
  흩어져 있었다. 두 번째 통로를 붙이려면 그 15곳을 매번 갈라 써야 하는데, 그러면 한 곳만
  빠져도 조용히 다른 동작이 된다(이 레포가 반복해 겪은 미러 드리프트 축).

## 통로가 채워야 하는 계약

**상수 8**
  NAME          값 원장·화면에 쓰는 통로 이름
  SHOT_SEC      한 발(영상 1편) 단위 초 — 콘티 컷을 이 초로 묶는다
  SEC_MAX       엔진이 한 발에 허용하는 상한 초 (⚠ SHOT_SEC 과 **다른 값**)
  RATIOS        받아주는 비율 목록
  REF_CAP_TECH  참조 그림 기술 상한(우리 운영 계약 REF_CAP 과 별개)
  EMBED_MAX     참조를 바이트로 실을 때 이 크기를 넘으면 줄인다
  FAIL_COSTS    실패한 호출에 돈이 나가는가 (재시도 정책의 전제)
  COST_KIND     값 단위 — 'usd'(실청구) | 'credit'(크레딧)

**함수 9**
  fresh_token()                     자격 한 줄
  refs_payload(urls, embed)         참조 수송 → (실어 보낼 것, 방식 이름)
  start(prompt, token, refs, seconds, ratio)   발사 → 작업 번호
  wait(job_id, token)               완료 대기 → {url, duration, cost}
  fetch(url)                        결과 바이트
  classify(exc)                     벤더 예외 → LaneError(3속성)
  ref_lock_clause(n)                프롬프트의 참조 잠금 절(벤더 문법)
  sound_clause(on, sfx)             프롬프트의 소리 절(벤더 문법)
  estimate(seconds, ratio)          발사 전 견적 — 못 재면 None(그록)

## 예외 3속성 공통 계약

러너의 분기(재시도할까 · 남은 편을 끊을까 · 뭐라고 남길까)는 **이 세 속성으로만** 갈린다.
  retryable   다시 쏘면 풀릴 축인가
  auth_dead   자격·통로 축인가(참이면 남은 편도 전부 같은 벽 → 중단)
  why         사람말 사유(원문 포함)
⚠ **no_credit 은 제3의 축이다** — 자격도 통로도 살아 있는데 돈이 없는 상태이고, 조치가
  「재승인」도 「통로 교체」도 아닌 「충전」이라 위 둘 어디에도 안 들어간다.

CONTRACT: check_grok_sb_chain
"""
import importlib
import os

LANES = {
    "grok": "lane_grok",
    # "seedance": "lane_seedance",   # ②단계에서 붙는다
}
DEFAULT = "grok"


class LaneError(Exception):
    """통로 무관 실패. 러너는 이 3속성으로만 분기한다(벤더 필드 직독 금지)."""

    def __init__(self, why, *, retryable=True, auth_dead=False, no_credit=False, body=""):
        super().__init__(why)
        self.why = why
        self.retryable = retryable
        self.auth_dead = auth_dead
        self.no_credit = no_credit
        self.body = body


def pick(name=None):
    """이름으로 통로를 고른다. 모르는 이름이면 **명시 실패**한다.

    ⚠ 조용한 폴백 금지 — 오타 하나로 엉뚱한 통로에 돈이 나가는 것보다 그 자리에서 죽는 게 싸다.
    """
    name = (name or os.environ.get("SB_LANE") or DEFAULT).strip().lower()
    mod = LANES.get(name)
    if not mod:
        raise LaneError("모르는 촬영 통로 '{}' (아는 것 {})".format(name, sorted(LANES)),
                        retryable=False, auth_dead=True)
    return importlib.import_module(mod)
