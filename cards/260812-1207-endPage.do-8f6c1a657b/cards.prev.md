# 중앙분리대는 있었다, 사고 난 그 지점만 없었다

**[프롬프트 설계]**
- 화풍: A 한국웹툰 수채화 — 20대 셋이 한 차에서 모두 숨진 #추모 사안이라, 선을 세우는 극화 대신 번지는 물감으로 먹먹함만 남긴다
- 분위기: 새벽의 정적과 절제 — 충돌하는 순간이 아니라 충돌이 지나간 뒤의 빈자리를 그린다. 파란 새벽에서 흐린 아침으로 옮겨가는 한 편의 시간
- 연출 방향: 독자가 멈추는 지점은 사고 경위가 아니라 "촬영 끝내고 집에 가던 길"이라는 대목이다(남 일 같지 않음). 그래서 사람을 그리지 않고 **두 사물**에 의도를 몰아준다 — ① 넘어간 자리를 말해주는 황색 중앙선 ② 이어져 오다 뚝 잘린 콘크리트 끝단. 화면에서 사람을 비우는 만큼 "여기 누가 있었는가"가 강해지고, 마지막에 그 도로가 아침 빛 속에 그대로 남아 있는 것으로 시사점을 시각화한다
- 독자 동선: **발단** 카드1→**전개** 카드2→**피크** 카드3→**해소** 카드4~6→**시사점** 카드7 · 훅=카드1 끝(단서형 "그중 한 대에 세 사람")+카드4 끝(단서형 "남은 건 둘뿐") · 착지 한 줄 = 세 사람은 촬영을 끝내고 가던 길이었다 · 감정 최저점은 카드3(3줄·최암·유일 최타이트), 꺾임 접속은 카드5 첫 줄 "그 사이 확정된 건"
- 연속성 앵커: 인물 (없음) · 반복 장소 = `Recurring location - a four-lane Korean rural national highway with a concrete median barrier running down the center, a crosswalk and a small side-road junction where the barrier stops.`

### [카드 1]
**텍스트**
```text
새벽 4시 50분, 안성에서 촬영이 끝났다
스무 명 남짓이 각자 차에 올랐다
학교 앞 38번 국도로 나가는 길이었다
*그중 한 대에 세 사람이 타고 있었다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the tired droop of a shoulder as a hand folds down a light stand in the dark. Five or six young adults in hoodies carry film equipment toward parked cars at the edge of a rural campus lot, all seen from behind and far enough away that no face is readable. One of them has already turned toward the exit road with car keys in hand, body and gaze angled to the right edge of the frame. A single battery-powered film light still glows on its stand, the last thing left standing on the empty asphalt.
Camera: wide shot from eye-level, shot on 35mm lens, nose room on the right
Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground, desolate stillness
Accent: monochrome desaturated base with a single warm amber accent (the glow of the last film light, the story's symbolic color of mourning), film-noir low-key lighting, deep shadows
Korean setting: Korean young adults, Korean rural campus surroundings, Korean road conventions with left-hand driver seat and Korean lane markings.
Text handling: no readable text anywhere; every equipment label and sign is turned away, cropped out, or lost in shadow.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the asphalt parking lot surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
대학생 단편영화 촬영 현장 장비
```

### [카드 2]
**텍스트**
```text
차는 알 수 없는 이유로 중앙선을 넘었다
맞은편엔 덤프트럭이 오고 있었다
*두 차는 정면으로 부딪혔다*
60대 트럭 운전자는 다쳐 병원으로 갔다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: one dark tire scar that crosses the center line and never returns to its own lane. Recurring location - a four-lane Korean rural national highway with a concrete median barrier running down the center, a crosswalk and a small side-road junction where the barrier stops. The road is seen from far above in the moments just after impact, with scattered glass and plastic fragments spread across both directions. A heavy dump truck sits stopped at an angle on the far side, its headlights still burning and aimed back down the road. No people are visible anywhere in the frame.
Camera: extreme long shot from a bird's-eye view, shot on 20mm wide lens
Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground, desolate stillness
Accent: monochrome desaturated base with a single warm amber accent (the yellow center line and the truck's standing headlights, the story's symbolic color), film-noir low-key lighting, deep shadows
Korean setting: Korean rural national highway, Korean lane markings and road conventions with left-hand driver seat.
Text handling: no readable text anywhere; no license plates, no signboards, no painted lettering on the road.
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
안성 삼죽면 38번 국도
```

### [카드 3]
**텍스트**
```text
*그 차에 탄 세 사람은 모두 숨졌다*
운전자 A씨와 B씨, C씨 모두 20대였다
스무 명이 흩어진 그 새벽이었다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: three small fragments of windshield glass lying apart from one another inside a single narrow pool of light. Recurring location - a four-lane Korean rural national highway with a concrete median barrier running down the center, a crosswalk and a small side-road junction where the barrier stops. The view looks straight down at the wet asphalt from close range, so only the grain of the road surface and those three fragments are legible. Everything beyond the pool of light is swallowed in black, and nothing else - no people, no vehicles, no debris field - enters the frame.
Camera: extreme close-up from a high angle, shot on 100mm macro lens
Lighting/mood: single pool of hard light isolating the subject in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single warm amber accent at its strongest here (the amber light caught inside the glass, the story's symbolic color of mourning), film-noir low-key lighting, deep shadows
Korean setting: Korean rural national highway asphalt with Korean road surface texture.
Text handling: no readable text anywhere; nothing printed, stamped, or painted appears on any fragment.
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
교통사고 도로 유리 파편
```

### [카드 4]
**텍스트**
```text
*그럼 왜 넘어갔나. 그걸 볼 수단이 없다*
승용차는 부서져 블랙박스 유무도 모른다
덤프트럭엔 처음부터 달려 있지 않았다
남은 건 사고기록장치와 CCTV뿐이다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: an empty black windshield mount with nothing left clipped into it. A gloved investigator's hand enters from the right edge and lifts the bracket clear of a dust-covered strip of interior trim laid out on a plain steel examination table. Beside it rest a sealed evidence bag and a small memory-card reader, arranged in a neat row. The damaged parts appear only as dull, cleaned fragments on the table, never as a wrecked vehicle, and no injured person or victim is shown.
Camera: close-up from eye-level, shot on 85mm portrait lens, nose room on the right
Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single warm amber accent (the paper evidence tag on the bag, the story's symbolic color), muted daylight contrast
Korean setting: Korean police forensic examination room, Korean vehicle interior parts.
Text handling: no readable text anywhere; the evidence tag and the bag are blank or angled away so no lettering is legible.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the steel examination table top) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
차량 사고기록장치 EDR
```

### [카드 5]
**텍스트**
```text
그 사이 확정된 건 도로 하나다
그 국도엔 중앙분리대가 있었다
*사고가 난 그 지점만 끊겨 있었다*
횡단보도와 교차로가 맞붙은 자리여서다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the blunt sawn end of the concrete median barrier where it simply stops in the middle of the road. Recurring location - a four-lane Korean rural national highway with a concrete median barrier running down the center, a crosswalk and a small side-road junction where the barrier stops. Seen from ground level right beside the road surface, the barrier runs away toward the horizon on the left and ends abruptly near the center of the frame. Past that cut end the two directions of traffic face each other with nothing between them, and the white bars of a crosswalk cross the open gap. No vehicles and no people appear.
Camera: wide shot from a ground-level worm's-eye view, shot on 24mm wide lens
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single warm amber accent (the yellow center line running up to the cut end, the story's symbolic color), muted daylight contrast
Korean setting: Korean rural national highway, Korean concrete median barrier and Korean lane markings.
Text handling: no readable text anywhere; no road signs, no painted lettering, no markers with characters.
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
국도 콘크리트 중앙분리대 끝단
```

### [카드 6]
**텍스트**
```text
사람이 건너야 하니 끊을 수밖에 없다
*다만 넘어온 차를 막을 것도 없었다*
경찰도 그래서 대형 사고가 됐다고 본다
원인은 조사 중이고 분리대는 그대로다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the wide unguarded stretch of bare asphalt where the barrier should have continued. Recurring location - a four-lane Korean rural national highway with a concrete median barrier running down the center, a crosswalk and a small side-road junction where the barrier stops. The view sits at eye level in profile to the road and looks straight across the opening, with the cut end of the barrier on the left and the same barrier resuming far away on the right. Between them lie only painted lines and open ground, and a pedestrian crossing signal pole stands at the edge as the reason the gap exists. No vehicles and no people appear.
Camera: medium shot from eye-level, profile side view of the road, shot on 50mm standard lens
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single warm amber accent (the yellow line dissolving into the bare gap, the story's symbolic color), muted daylight contrast
Korean setting: Korean rural national highway, Korean pedestrian signal pole and Korean lane markings.
Text handling: no readable text anywhere; the signal pole and roadside posts carry no lettering or numbers.
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
중앙분리대 개구부 교차로 횡단보도
```

### [카드 7]
**텍스트**
```text
이 사고의 원인이 끝내 밝혀지지 않으면
유족에게 남는 게 없다는 것도 문제지만
도로를 고칠 근거까지 같이 흐려진다
*세 사람은 촬영을 끝내고 가던 길이었다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the first warm light of morning reaching the empty road exactly where the barrier ends. Recurring location - a four-lane Korean rural national highway with a concrete median barrier running down the center, a crosswalk and a small side-road junction where the barrier stops. The frame faces straight down the highway from the center of the lane at eye level, the road running away from the viewer toward a low wooded hill. A quiet campus gate sits small and far off to the right, and the gap in the barrier rests in the middle distance. The road is completely empty, with no vehicles and no people anywhere.
Camera: wide shot from eye-level, front-on symmetrical composition, shot on 35mm lens
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: monochrome desaturated base with a single warm amber accent (the yellow center line catching the first morning light, the story's symbolic color), muted daylight contrast
Korean setting: Korean rural national highway, Korean campus gate architecture, Korean lane markings.
Text handling: no readable text anywhere; the distant gate bears no name or lettering and no road sign is legible.
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
동아방송예술대 정문 38번 국도
```
