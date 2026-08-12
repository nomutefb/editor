# 빗속의 의수 — 세운상가 야간 4초

## ⚙️ 설계 요약
의도: 밤 세운상가 육교 · 사이버 의수의 남자가 빗속을 걷는다 → 해석: 대사 없는 무드 피스 · 네온 보라·청록과 젖은 바닥 반사가 주인공인 사이버펑크 정조 · 걷기(전개)에서 의수 클로즈(피크)로 닫는 2박 아크
감독: Fable 5
촬영: grok
비율: 16:9
화질: 720p
프레임: 24fps
길이: 4s — 2컷 (배선 확인용 지시: 각 2초 고정)

## 🎬 시나리오
로그라인: 비 내리는 밤의 세운상가 육교 위, 사이버 의수를 단 남자가 홀로 걸어오다 난간 앞에 멈춰 의수를 편다.
컷1 = 설정·전개: 젖은 육교 원경에서 남자가 카메라 쪽으로 걸어온다 — 인물과 공간을 한 번에 심는다.
컷2 = 피크·여운: 난간 앞에 멈춘 남자의 의수가 네온 빛을 받으며 천천히 손가락을 편다 — 이 영상의 키비주얼.
전 컷 무대사 · 소리는 빗소리와 네온 험만.

### 컷1 · 0~2s · 빗속 육교를 걸어오는 남자
ACTION: 남자가 젖은 육교 보행로를 카메라 쪽으로 천천히 걸어온다. 코트 자락이 흔들리고, 바닥의 보라·청록 네온 반사가 발걸음마다 일렁인다.
CAMERA: wide shot, eye-level, locked static frame, deep perspective down the overpass
DIALOGUE: (없음)
MOTION: The man with the glowing cybernetic left arm walks slowly forward along the walkway, his coat hem swaying with each step; the camera stays locked, static; steady rain falls and hisses.

### 컷2 · 2~4s · 난간 앞, 의수가 빛을 받는다
ACTION: 남자가 난간 앞에 멈춰 서고, 사이버 의수를 가슴 높이로 들어 손가락을 한 번 천천히 편다. 의수 관절 이음새가 네온 빛을 받아 반짝인다.
CAMERA: medium close-up on the arm and torso, slow push in, shallow focus
DIALOGUE: (없음)
MOTION: The man with the glowing cybernetic left arm stops at the steel railing and raises the cybernetic hand to chest height, slowly spreading its metal fingers once; the camera pushes in slowly; rain patters on metal.

## 👤 캐릭터
① 사이버 의수의 남자 — 정체성 락:
```text
Korean man in his early 30s, short damp black hair pushed back by rain, sharp jawline, calm tired eyes. His entire left arm is a matte gunmetal cybernetic prosthetic with segmented plates and thin teal light seams glowing at the joints. He wears a long charcoal waterproof coat over a dark high-collar shirt, black trousers, black boots. Identity lock: the glowing cybernetic LEFT arm, the long charcoal coat, and the damp pushed-back hair stay identical in every shot.
```

## 🖼 레퍼런스
① 인물: 사이버 의수의 남자 (전신 · 정면 기준)
```text
Photoreal cinematic full-body portrait of a Korean man in his early 30s standing in night rain, short damp black hair pushed back, calm tired eyes. His entire left arm is a matte gunmetal cybernetic prosthetic with segmented plates and thin teal light seams glowing at the joints, hand relaxed at his side. He wears a long charcoal waterproof coat over a dark high-collar shirt, black trousers, black boots. Lit by purple and teal neon from off-frame, rain droplets on his shoulders, dark blurred night background. No text, no captions, no watermark, no logos.
```
② 배경: 밤의 세운상가 육교 (무인)
```text
Photoreal cinematic empty pedestrian overpass at Sewoon Sangga, Seoul, at night in heavy rain. A long straight elevated walkway with a weathered steel railing on both sides, wet concrete floor mirroring purple and teal neon glow from surrounding electronics-market buildings, glowing sign panels with no legible characters, scattered puddles rippling with raindrops, faint mist in the distance. No people in frame. No text, no captions, no watermark, no logos.
```

## 🎯 분해 추천
컷2 — 의수가 펴지는 순간이 이 영상의 유일한 키비주얼이라 손가락 관절·빛 반사의 초별 타이밍을 잡을 가치가 가장 크다. 진행 = "컷2 디테일하게"

## ⏭ 다음 단계
콘티 + 🖼 레퍼런스 2장이 sb_out/<id>/ 에 함께 앉는다 → grok_sb_video.py 가 컷마다 [Gemini 컷 그림 → 그 그림을 첫 장면으로 그록 영상]으로 발사한다 (컷당 청구액이 응답에 실려 화면에 표기된다).

## 📌 안내
추정 의수 위치: 왼팔 — 바꾸려면 "의수는 오른팔로"
추정 광고 모드: OFF (무드 피스로 판단, 키비주얼 컷 의무 미적용) — 바꾸려면 "[광고: ON]"
길이 4s는 폼 표준 범위(5~15s) 밖이나 배선 확인용 지시(2컷 × 2s)를 그대로 따랐다.
이 콘티로 만든 영상·이미지는 AI 생성물 표기 의무 대상이다.
