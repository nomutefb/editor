# 세운상가 야우(夜雨) — 빗속의 보행

## ⚙️ 설계 요약
의도: 밤 세운상가 육교 · 빗속을 걷는 검은 전술복 여자 · 무대사 → 해석: 네온 느와르 무드피스. 서사보다 공기 — 보라·청록 네온과 젖은 바닥 반사가 주인공이고, 인물은 그 속을 가로지르는 실루엣. 아크 = 원경(공간 제시) → 근접(인물 확정).
감독: 페이블 5
촬영: grok
비율: 16:9
화질: 720p
프레임: 24fps
길이: 4s — 2컷 (컷 길이 지시에 따라 각 2초)

## 🎬 시나리오
비 내리는 세운상가 육교의 네온 불빛 아래, 검은 전술복의 여자가 말없이 걸어 카메라 앞을 지나간다.
컷1 = 공간이 먼저 말한다: 무인의 육교, 보라·청록 네온, 젖은 바닥의 빛 반사.
컷2 = 인물이 들어온다: 빗속을 일정한 보폭으로 걷는 여자, 카메라가 낮게 따라붙는다.
대사·자막 없음 — 빗소리와 발소리만.

### 컷1 · 0~2s · 무인의 육교 — 네온과 비가 공간을 연다
ACTION: 비 내리는 세운상가 육교 원경. 보라·청록 네온 간판이 젖은 바닥에 길게 반사되고, 빗줄기가 조명을 스치며 떨어진다. 사람 없음.
CAMERA: wide static locked shot, slightly low angle, deep focus — neon signs and wet-floor reflections fill the frame
DIALOGUE: (없음)
MOTION: Rain falls steadily through the neon light, ripples spreading across the puddles on the walkway floor. No people in frame. Camera locked, static. Sound of rain on concrete.

### 컷2 · 2~4s · 그녀가 지나간다 — 낮은 트래킹
ACTION: 검은 전술복의 여자가 육교를 일정한 보폭으로 걸어온다. 카메라가 바닥 반사를 앞에 두고 낮게 옆에서 따라붙고, 얼굴엔 네온 보라·청록이 번갈아 스친다.
CAMERA: low-angle lateral tracking shot, medium-full, shallow focus on subject — wet-floor neon reflection in foreground
DIALOGUE: (없음)
MOTION: The woman in the black tactical suit with the slick wet ponytail walks forward at a steady pace, boots striking the wet floor, then passes the pillar of the overpass railing as the camera tracks alongside her at a low angle. Sound of rain and footsteps.

## 👤 캐릭터
여자 — 검은 전술복의 보행자
```text
Korean woman in her late 20s, sharp calm expression, pale skin glossed with rain.
Hair: black, pulled into a single low ponytail, slicked wet against her head.
Outfit (LOCKED): matte-black tactical suit — high-collar jacket zipped to the throat,
fitted tactical pants with thigh strap, black combat boots. No logos, no weapons.
Silhouette: slim, upright, steady stride. Neon purple and teal light plays across
the wet fabric. Identical face, hair and outfit in every shot.
```

## 🖼 레퍼런스
① 인물: 검은 전술복 여자 (전신 · 정체성 락)
```text
Photoreal full-body night portrait of a Korean woman in her late 20s, sharp calm
expression, black hair in a single slicked-wet low ponytail. She wears a matte-black
tactical suit: high-collar zipped jacket, fitted tactical pants with a thigh strap,
black combat boots. Standing upright in falling rain, lit by neon purple and teal
from off-frame, wet fabric catching the light. Dark blurred night background.
Clean scene only — no text, no captions, no watermark, no logos.
```
② 배경: 밤의 세운상가 육교 (빈 공간)
```text
Photoreal empty night scene of a Korean pedestrian overpass at Sewoon Sangga, Seoul,
in heavy rain. Concrete walkway with metal railing and railing pillars, neon signs
in purple and teal glowing on both sides, long streaks of neon reflected in the wet
floor puddles, rain visible against the lights. City lights bokeh in the distance.
No people in frame. Clean scene only — no text, no captions, no watermark, no logos.
```

## 🎯 분해 추천
컷2 — 인물·카메라 무브·반사가 한 컷에 겹치는 유일한 연기 컷이라 트래킹 속도와 네온 스침 타이밍을 초별로 굳힐 가치가 가장 크다. 진행 = "컷2 디테일하게"

## ⏭ 다음 단계
콘티 확정 후 → 같은 잡의 러너(grok_sb_video.py)가 컷마다 [Gemini 컷 그림 → 그 그림을 첫 장면으로 그록 영상]을 자동 발사하고 sb_out/<id>/ 에 착지한다. 🖼 레퍼런스 2장이 인물·배경 정체성 참조로 함께 실린다. (컷당 청구가 응답 실값으로 화면에 표기된다.)

## 📌 안내
- 추정 인물 세부: 20대 후반 한국인 · 낮은 포니테일 — 바꾸려면 "인물을 짧은 단발로"
- 추정 아크: 컷1 무인 원경 → 컷2 인물 트래킹 — 바꾸려면 "컷1부터 인물 등장으로"
- 컷수 2컷 = [컷 길이 지시] 명시값 적용(밴드 로직 6컷 미적용 · 길이 4s는 폼 표준 5~15s 밖의 배선 확인용 값)
- 이 영상은 AI 생성물로, 게시 시 AI 생성 표기가 필요하다.
