# 사람 없는 판에서 잃고, 사람 없는 가게를 털었다

**[프롬프트 설계]**
- 화풍: B 극화 — 범죄·구조 고발 축이고, 금속·유리·형광등의 차가운 질감을 선으로 잡아야 사람 없는 밤의 무게가 선다
- 분위기: 사람이 하나도 없는 밤. 기계만 깨어 있고, 그 기계가 뜯긴 자리에 남은 허탈
- 연출 방향: 무인점포 점주와 부모가 "내 가게, 우리 애"로 읽는 자리에서 독자가 멈춘다. 전하려는 건 지키는 일은 기계에 맡겼는데 잡는 일은 사람이 했다는 것 — 그래서 카메라를 사람의 얼굴이 아니라 **뜯긴 결제 단말기와 그 위에 남은 초록 LED**에 계속 두고, 사람 없는 판(화면 빛)과 사람 없는 가게(단말기 빛)를 같은 한 색으로 이어 붙인다. 인물은 얼굴 없이 손·실루엣·뒷모습으로만 들이고, 얼굴이 정면으로 서는 건 마지막 점주 한 사람뿐이다. thumb_dispatch의 멸균 형광 톤과 부재 정조를 키노트로 계승(앵글은 카드마다 분산)
- 독자 동선: **제시** 카드1(세 시간·일곱 곳·87만원)→**발단** 카드2(도박 빚)→**전개** 카드3(공구·키오스크·장물 오토바이·무면허)→**피크** 카드4(카메라는 찍었으나 알린 장치는 없었다)→**해소** 카드5(신고→도주로 예상→추격 검거)→**시사점** 카드6~7(반복되는 형태 6 · 착지 7) · 훅=카드1 끝(예고형 "갈 곳은 이미 정해져 있었다")+카드2 끝(단서형 "공구") · 카드4 무훅 · 착지 한 줄 요지=열 번을 털어 쥔 87만원으로 갚을 빚이었나, 부서진 것은 점주들에게 남았다
- 연속성 앵커: Recurring subject - a slim figure of small build in a dark hooded jacket with the hood up, face never visible, always shown from behind or in silhouette. (카드 2·3·5) / 반복 장소 = the interior of the same unmanned self-service store, fluorescent-lit, shelves full and untouched

### [카드 1]
**텍스트**
```text
지난 7월 초 세 시간 동안 고양에서
무인점포 일곱 곳이 잇달아 털렸다
가져간 현금은 다 합쳐 87만원이었다
*그 돈이 갈 곳은 이미 정해져 있었다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the empty aisle running straight to the half-open front door, with not one person standing in it. The interior of an unmanned self-service store, seen head-on down the center aisle at night. On the counter to the right, a payment terminal has its front panel pried off and its cash drawer pulled out and empty, with a few plastic shards and screws scattered on the floor tiles below it. The shelves on both sides are full and untouched, every item still facing forward, and the composition leaves open space at the right edge with the line of the aisle drawing the eye toward it.
Camera: wide shot showing the full interior and its surrounding environment, from eye-level neutral perspective, shot on 35mm lens with natural documentary perspective and minimal distortion
Lighting/mood: flat sterile clinical fluorescent light from the ceiling, cold even greenish-white, emotionless institutional, no warmth anywhere
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) glowing on the terminal status LEDs and the door light, muted flat contrast
Korean context: a Korean neighborhood self-service shop interior, Korean-style shelving and counter, no brand logos and no shop names of any kind.
Text handling: avoid incidental lettering entirely - signage, price tags, screens and packaging are rendered as blank surfaces, color blocks or pictogram shapes rather than characters. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the store floor tiles) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
무인점포 심야 내부
```

### [카드 2]
**텍스트**
```text
갈 곳은 도박 빚이라고 그는 말했다
열여섯 살, 사이버도박으로 진 빚이었다
도박으로 잡힌 10대는 4년 새 6.7배다
*빚을 갚겠다며 그가 고른 건 공구였다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: two bare hands cupped around a phone on a desk, thumbs stopped mid-motion, the only thing lit in a pitch-dark room. Recurring subject - a slim figure of small build in a dark hooded jacket with the hood up, face never visible, always shown from behind or in silhouette. Only the hands and one shoulder edge of this figure enter the frame from the bottom left, the rest of the body swallowed by darkness. The phone screen is a blank field of light with no characters or images on it, throwing its glow up onto the fingers and the bare desk surface and onto nothing else, with open space left at the right edge of the frame.
Camera: close-up shot centered on the hands, from a high angle looking down at the desk, shot on 85mm portrait lens with soft background separation
Lighting/mood: cold blue screen under-glow lighting the hands from below in a dark room, restless paranoid unease
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) in the screen glow spilling across the fingertips, film-noir low-key lighting, deep shadows
Korean context: a small Korean domestic desk, plain and worn, no brand logos of any kind.
Text handling: avoid incidental lettering entirely - the phone screen and every surface are rendered as blank glowing planes or pictogram shapes rather than characters. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the dark desk top) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
청소년 사이버도박 스마트폰
```

### [카드 3]
**텍스트**
```text
공구로 키오스크를 부수고 돈을 꺼냈다
*세 시간 동안 일곱 곳, 열 차례였다*
타고 다닌 오토바이는 장물이었다
면허도 없이 그 길을 돌아다녔다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a gloved hand still resting on the pried-open panel, in the instant after the casing gave way. Recurring subject - a slim figure of small build in a dark hooded jacket with the hood up, face never visible, always shown from behind or in silhouette. The figure stands at the store counter with its back to the camera, one hand holding a short pry tool lowered at its side and the other flat on the terminal casing, head turned down toward the cash drawer that has slid open. Behind the counter the shelving runs unbroken across the frame, stocked and untouched, and the whole action sits in the upper half of the picture.
Camera: medium shot, waist-up framing with the hands and gesture visible, from a canted Dutch angle slightly above the subject with a tilted horizon, shot on 24mm wide lens for spatial context
Lighting/mood: single hard side-light cutting across the subject, deep chiaroscuro shadows, tense atmosphere
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the terminal LED still lit beside the torn panel, film-noir low-key lighting, deep shadows
Korean context: a Korean neighborhood self-service shop counter and shelving, no brand logos and no shop names of any kind.
Text handling: avoid incidental lettering entirely - the terminal face, shelf labels and packaging are rendered as blank surfaces, color blocks or pictogram shapes rather than characters. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the wall of store shelving behind the counter) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
키오스크 현금함 파손
```

### [카드 4]
**텍스트**
```text
*카메라는 그 세 시간을 다 찍고 있었다*
털리는 중이라고 알린 장치는 없었다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the unblinking lens in the ceiling corner, recording a room that nobody is watching. A dome surveillance camera mounted where two ceiling planes meet fills the upper half of the frame, seen from directly beneath it. Reflected in miniature across the curved glass of the lens are the empty aisle and the counter with its terminal torn open. Not one person is present anywhere in the scene, and everything around the camera housing falls away into deep black.
Camera: extreme close-up on a single detail, from a low angle looking straight up, shot on 100mm macro lens with fine detail and shallow depth of field
Lighting/mood: flat cold even surveillance light, no shadow no warmth, detached and watchful, everything beyond the lens housing sinking into black
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the camera's recording indicator light, film-noir low-key lighting, deep shadows
Korean context: a Korean shop ceiling with an exposed conduit line, no brand logos and no shop names of any kind.
Text handling: avoid incidental lettering entirely - the camera housing and every reflected surface carry no characters, only blank planes and pictogram shapes. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the store ceiling plane) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
무인점포 천장 CCTV
```

### [카드 5]
**텍스트**
```text
"금고가 털렸다"는 신고가 먼저였다
받고 보니 다른 점포도 털려 있었다
일산서부경찰서는 도주로를 예상했다
*추격 끝에 오토바이 운전자를 잡았다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the narrowing gap between one small tail lamp and the patrol lights closing on it. Recurring subject - a slim figure of small build in a dark hooded jacket with the hood up, face never visible, always shown from behind or in silhouette. Seen from high above, this figure rides a small scooter alone down an empty four-lane road wearing a plain dark helmet, while behind and to the left a police car sweeps into the same lane and gains on it. Streetlights lay evenly spaced pools of light along the asphalt, the surrounding blocks are dark and still, and both vehicles sit in the upper half of the frame.
Camera: extreme long shot with a tiny subject in a vast environment, from a bird's-eye overhead angle looking down, shot on 200mm telephoto lens with strong compression
Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground, desolate stillness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the scooter's tail lamp, every other light rendered as cold desaturated white, film-noir low-key lighting, deep shadows
Korean context: a Korean city road with Korean lane markings and right-hand traffic conventions, Korean-style crosswalk and streetlight forms, no brand logos and no signage text of any kind.
Text handling: avoid incidental lettering entirely - road signs, plates and shopfronts are rendered as blank surfaces, color blocks or pictogram shapes rather than characters. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the asphalt road surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
일산서부경찰서 오토바이 추격
```

### [카드 6]
**텍스트**
```text
*이 장면은 처음이 아니었다*
넉 달 전 인천에서도 10대들이
훔친 차로 무인점포 일곱 곳을 털었다
전국 무인점포 절도는 4년 새 세 배다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the same pried-open terminal repeating doorway after doorway, as if one night had been copied down the whole street. A view from ground level looking up along a night street lined with identical unmanned store entrances receding toward a vanishing point, each doorway lit by the same cold ceiling light. In the two nearest entrances a payment terminal stands with its panel hanging open, and that same shape repeats smaller and smaller down the row. No person stands anywhere in the street, and the doorways are held in the upper half of the frame.
Camera: wide shot with full environmental context, from a ground-level worm's-eye view near the pavement, shot on 20mm wide lens with documentary realism
Lighting/mood: flat sterile clinical fluorescent light in every doorway, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the terminal LEDs repeating down the row, film-noir low-key lighting, deep shadows
Korean context: a Korean low-rise commercial street with Korean-style shopfront framing, no brand logos and no shop names of any kind.
Text handling: avoid incidental lettering entirely - every sign board, window decal and terminal face is rendered as a blank surface, color block or pictogram shape rather than characters. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the wet pavement of the street, running unbroken from the bottom edge to the vanishing point) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
인천 무인점포 절도 10대
```

### [카드 7]
**텍스트**
```text
열 번을 털어 손에 쥔 건 87만원이었다
그 돈으로 갚을 수 있는 빚이었을까
진술이 사실이라도 빚은 줄지 않았고
*부서진 키오스크는 점주들에게 남았다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the shop owner's hand resting flat on the broken casing, not lifting it. A Korean shop owner in a worn work jacket, in their fifties, stands behind the counter of the unmanned store in morning light, facing the camera and looking down at the payment terminal whose front panel is torn off and whose cash drawer hangs open. The shoulders are lowered, one hand rests on the ruined casing and the other holds a phone at their side without raising it. The stocked shelves run unbroken behind them, and both the face and the broken terminal sit in the upper half of the frame.
Camera: medium shot, waist-up framing with face and gestures visible, from eye-level in a front-on symmetrical composition facing camera, shot on 85mm portrait lens with soft background separation
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the one status LED still blinking on the broken terminal, muted daylight contrast
Korean context: a Korean neighborhood self-service shop interior, Korean-style shelving and counter, no brand logos and no shop names of any kind.
Text handling: avoid incidental lettering entirely - the terminal face, shelf labels and packaging are rendered as blank surfaces, color blocks or pictogram shapes rather than characters. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the wall of store shelving behind the counter) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
무인매장 점주 피해
```
