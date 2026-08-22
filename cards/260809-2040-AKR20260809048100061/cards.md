# 청소하러 들어간 연유 탱크, 50대 2명이 함께 쓰러졌다

**[프롬프트 설계]**
- 화풍: B 극화 — 수십 년째 같은 모양으로 반복돼 온 밀폐공간 재해의 구조를 고발하는 사건이라 사실성과 무게가 먼저다
- 분위기: 위생을 위해 반짝이게 닦인 스테인리스 설비의 차가운 표면과, 그 안으로 사람이 직접 들어가야만 끝나는 작업 사이의 온도차. 절차적이고 건조하되 바닥에 무력감이 깔린 톤
- 연출 방향: 뉴스 안 보는 독자도 "둘이 함께 쓰러졌다"는 한 문장 앞에서는 멈춘다 — 개인의 실수라는 설명이 그 자리에서 무너지기 때문이다. 그래서 카드 전체가 **좁은 원통형 탱크의 맨홀 입구 하나**를 계속 다시 잡는다: 들어가는 순서(카드1) → 들여다보는 순서(카드2) → 실려 나오는 순서(카드3) → 그 안에서 벌어진 일(카드4) → 뒤늦게 재는 순서(카드5·7). 같은 입구를 매번 다른 높이·거리에서 보게 해, 독자가 "왜 매번 확인이 나중인가"를 이미지만으로 체감하게 한다. thumb_dispatch의 임상 형광 톤(LGT12)과 '부재·사후'의 정조를 전 카드 베이스로 깔되 앵글은 카드마다 흩는다
- 독자 동선: **발단** 카드1→**전개** 카드2~3→**피크** 카드4→**해소** 카드5→**시사점** 카드6~7 · 훅=카드1 끝(단서형: 두 사람 다 제 발로 못 나왔다는 사실만 던지고 경위는 유보)+카드3 끝(단서형: 원인 미확정 예고, 카드4가 정황으로 즉시 회수) · 착지 한 줄 요지 = 막는 목록은 짧고 오래됐는데, 그 확인은 늘 사람이 실려 나온 뒤에 시작된다
- 연속성 앵커: Recurring subject — a Korean man in his 50s in a navy blue work uniform with reflective stripes and black rubber boots, close-cropped graying hair (카드1·3) / 반복 장소 = a tall cylindrical stainless steel storage tank inside a cold Korean food-processing plant hall

### [카드 1]
**텍스트**
```text
높이 3.4m, 지름 1.9m 연유 탱크
청소를 하려면 사람이 안에 들어간다
그날 오후 두 사람이 들어갔고
*둘 다 제 발로 나오지 못했다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a gloved hand gripping the cold rim of the narrow tank hatch, knuckles taut. Recurring subject — a Korean man in his 50s in a navy blue work uniform with reflective stripes and black rubber boots, close-cropped graying hair — climbs a steel ladder toward the open hatch of a tall cylindrical stainless steel storage tank, seen from behind. A second worker in the same uniform waits below, holding a coiled washing hose and looking up at the hatch. The tank towers over both of them inside a cold food-processing plant hall.
Camera: wide shot from a low angle, shot on 24mm wide lens
Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Korean industrial setting: Korean factory interior conventions, Korean-style work uniforms and safety gear.
Text handling: avoid incidental lettering; no signage text, no labels on equipment, no printed documents in view.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the stainless steel tank wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
식품공장 저장탱크 맨홀
```

### [카드 2]
**텍스트**
```text
8월 9일 오후 2시 58분, 공장 직원이
*탱크 안에 쓰러져 있는 두 사람을 봤다*
경기 평택 매일유업 공장, 연유 저장 탱크
둘은 곧바로 병원으로 실려 갔다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the plant employee's widened eyes and the hand frozen flat on the hatch frame as he leans over the opening. He is a Korean man in his 40s in a white sanitary coat and hairnet, bent at the waist over the open hatch of the stainless steel tank, shouting down into it with his other arm flung back toward the aisle. Two coworkers in the same white coats run in from the right side of the frame toward him. The wet floor around the tank base is empty.
Camera: MS from eye-level at a three-quarter angle, shot on 35mm lens
Lighting/mood: cold blue dim interior light, heavy and suffocating, faint trembling tension
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows
Korean industrial setting: Korean factory interior conventions, Korean-style sanitary work wear.
Text handling: avoid incidental lettering; no signage text, no labels on equipment, no printed documents in view.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the factory floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
매일유업 평택공장
```

### [카드 3]
**텍스트**
```text
A씨는 병원에서 끝내 숨졌다
함께 발견된 다른 50대는 경상을 입었다
경찰은 탱크 청소 중 쓰러진 것으로 본다
*원인은 아직 확정되지 않았다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: an oxygen mask fogging over the surviving worker's face, his eyes half open and unfocused. Recurring subject — a Korean man in his 50s in a navy blue work uniform with reflective stripes and black rubber boots, close-cropped graying hair — lies on the first stretcher being loaded into an ambulance in the factory yard while a paramedic steadies the mask. Behind them a second stretcher is pushed toward another ambulance, covered and still, attended by two paramedics with their heads down. Coworkers stand back at the edge of the yard and watch.
Camera: full shot from eye-level in profile, shot on 40mm lens
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Korean industrial setting: Korean factory yard, Korean ambulance and paramedic uniform conventions.
Text handling: avoid incidental lettering; no signage text, no labels on vehicles, no printed documents in view.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the asphalt of the factory yard) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
산업재해 구급차 공장 이송
```

### [카드 4]
**텍스트**
```text
*한 명이 아니라 두 명이었다*
같은 자리에서 나란히 쓰러졌다
부주의로는 설명되지 않는 모양이다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the small gap between two motionless silhouettes lying side by side at the bottom, close enough to touch. Looking straight down through the open hatch into the narrow cylindrical interior of the tank, two workers in navy work uniforms lie collapsed on the curved steel floor, faces turned away and unlit, one still holding a cleaning brush and the other a hose nozzle. A single shaft of light from the hatch above lands on the floor between them. The curved stainless wall wraps the rest of the frame in blackness.
Camera: wide shot from a bird's eye view looking straight down, shot on 16mm wide lens
Lighting/mood: single pool of hard light isolating the figures in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows
Korean industrial setting: Korean food-plant tank interior conventions, Korean-style work uniforms.
Text handling: avoid incidental lettering; no signage text, no labels on equipment, no printed documents in view.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the curved interior wall and floor of the cylindrical tank) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
밀폐공간 질식재해 탱크 내부
```

### [카드 5]
**텍스트**
```text
경찰은 작업 내용과 사고 경위,
*안전 수칙을 지켰는지를 조사한다*
부검으로 사인도 확인하기로 했다
사건은 중대재해수사팀으로 넘어간다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: an investigator's pen stopping mid-line on the clipboard as he tilts his head up toward the tank hatch. Three Korean police investigators in dark jackets and latex gloves work at the base of the same stainless steel tank, one measuring the hatch opening with a tape, one photographing it, one writing. A plant manager in a white sanitary coat stands slightly apart with his arms at his sides, watching them and saying nothing. Yellow tape runs across the aisle behind them.
Camera: MS from a low angle, shot on 35mm lens
Lighting/mood: flat cold even surveillance light, no shadow no warmth, detached and watchful
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Korean industrial setting: Korean police investigation conventions, Korean factory interior, Korean-style sanitary coats.
Text handling: avoid incidental lettering; no signage text, no labels on tape or equipment, no printed documents in view.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the concrete factory floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
중대재해 경찰 현장 감식
```

### [카드 6]
**텍스트**
```text
10년간 밀폐공간 질식사고가 154건
*사상자는 315명, 41.9%가 숨졌다*
이틀 전에는 이 도시 다른 공장에서
근로자가 설비에 끼여 숨졌다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the same round hatch repeated on tank after tank, every one of them shut, receding into the heat haze. A high wide view over a Korean industrial complex at midday, rows of identical cylindrical stainless tanks and factory sheds packed side by side. In one yard far below, a small cluster of investigators stands around a taped-off machine; in another yard further back, two workers in navy uniforms carry a hose toward yet another tank. Heat shimmer flattens the whole complex into repeating geometry.
Camera: extreme long shot from a high angle, shot on 200mm telephoto lens
Lighting/mood: harsh overexposed midday sunlight, hard shadows, oppressive heat
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Korean industrial setting: Korean industrial complex layout, Korean factory sheds and work uniforms.
Text handling: avoid incidental lettering; no signage text, no company names, no building numbers rendered.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the industrial complex ground seen from above) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
평택 산업단지 공장 전경
```

### [카드 7]
**텍스트**
```text
막는 방법은 이미 다 나와 있다
들어가기 전에 공기를 재고, 환기하고
밖에 한 사람을 세워두면 된다
*확인은 늘 사람이 실려 나온 뒤였다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a worker's steady gaze straight into the viewer, tired and unblinking, standing beside gear that arrived too late. A Korean man in his 50s in a navy work uniform stands front-on beside the now-closed hatch of the stainless steel tank in a quiet morning factory yard. Laid out neatly on the concrete beside him are a gas detector on a tripod, a portable ventilation duct, a coiled safety rope and a harness, all unused and clean. The tank behind him is sealed and the aisle is empty.
Camera: MS from eye-level, front-on, shot on 50mm standard lens
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Korean industrial setting: Korean factory yard, Korean-style safety equipment and work uniform.
Text handling: avoid incidental lettering; no signage text, no labels on the detector or duct, no printed documents in view.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the concrete yard surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
밀폐공간 산소농도 측정기 환기장치
```
