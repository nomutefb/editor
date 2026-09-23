# 파이프라인 모델 단일 원천 (source 전용 · 14인 평의회 260702 SYS-08).
#
# 왜: MODEL="claude-opus-5-5" 하드코딩이 7개 스크립트(analyze·ask·cardmake·kmake·lymake·revise·revise-cards)에
#   분산돼 있어 모델 교체 시 한 곳만 누락돼도 단계별 이종 모델이 무음으로 섞였다(계측 왜곡 포함).
#   여기 한 곳(또는 워크플로 env PIPE_MODEL 오버라이드)만 바꾸면 전 파이프라인 일괄/카나리 전환.
# ⚠️ 생성/하드작업은 opus 5.5 유지가 운영자 정본(CLAUDE.md §🤖) — 이 파일은 '교체를 쉽게'지 '내리라'가 아님.
#   판정(gate/breaking)은 별도 축(GATE_MODEL·BREAKING_MODEL — sonnet 운영)이라 여기 안 탄다.
PIPE_MODEL="${PIPE_MODEL:-claude-opus-5-5}"
# 페이블 티어 = 중요 창작(품질 차이가 큰 일: AI 이미지 프롬프트·클링·음원·번역카드·콘티 감독·쇼츠 컷·테이크 · 운영자 260721~22).
# 호출처(models.json tiers.fable.sites)는 이 변수만 쓴다 — ID를 직접 박으면 대행(다른 티어 모델을 대신 씀)·복귀 때 그 자리만
# 남는다(check_model_ids 차단). 값 = apply_models.py가 키로 옮긴다(손 수정 금지 · 정본 = models.json tiers.fable).
FABLE_MODEL="${FABLE_MODEL:-claude-fable-5}"
