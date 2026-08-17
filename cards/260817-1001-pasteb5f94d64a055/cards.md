# 도크는 잠겼고, 그는 집에서 숨졌다

**[프롬프트 설계]**
- 화풍: A 한국웹툰 수채화 — 사망자가 있는 재난이라 극화의 고발 톤으로 참사를 키우지 않고, 한 발 물러선 붓결로 정황만 남긴다
- 분위기: 사흘 내내 젖어 무거워진 흙과 새벽의 찬 공기, 소리 없이 일이 끝난 뒤의 정적. 파스텔 안에서 채도를 내리고 한 점만 남긴다
- 연출 방향: 뉴스 안 보는 독자가 멈추는 자리는 "회사는 오늘 나오지 말라고 정해주는데, 집은 아무도 정해주지 않는다"는 감각이다. 그래서 카드마다 **경계**를 눈에 쥐여준다 — 잠긴 게이트, 물이 멈춘 도크 수면, 토사가 닿은 창틀 높이. 사람은 구조·대피·점검처럼 '움직이는 자리'에만 넣고, 죽음이 놓인 자리는 비워 부재로 말한다(thumb_dispatch SG-09 계승). 조명은 LGT02의 찬 새벽 톤을 키노트로 삼아 흐린 낮에서 출발해 轉에서 가장 어둡게 떨어뜨리고 마지막 카드에서만 아침빛으로 푼다
- 독자 동선: **발단** 카드1 → **전개** 카드2~3 → **피크** 카드4 → **해소** 카드5~6 → **시사점** 카드7 · 훅=카드1 끝(예고형 — 흙이 이미 이틀치 물을 머금었다는 단서)+카드3 끝(회사의 조치를 던지고 카드4가 그 경계를 즉시 받음)+카드5 끝(나가라는 문장과 막힌 도로의 미완 대비) · 착지 한 줄 = 회사가 닫을 수 있는 문은 정문까지였다
- 연속성 앵커: (없음)

### [카드 1]
**텍스트**
```text
경남 거제에 사흘 동안 비가 왔다
기상청 집계로 805.6㎜였다
*그중 400㎜는 마지막 밤에 몰렸다*
흙은 이미 이틀치 물을 머금고 있었다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the water-heavy hillside leaning over the low-rise apartment blocks beneath it. Rain has been falling for three days on a small southern Korean shipbuilding city, and the slope behind the housing rows is dark and swollen with runoff. Thin threads of muddy water run down the slope face and gather in the drainage channel at its foot, with the saturated upper slope anchored in the upper-center of the frame. Two or three windows in the blocks are still lit while every other window stays dark, and far behind the rooftops the outlines of shipyard gantry cranes stand blurred in the rain. No people are visible.
Camera: extreme long shot from a bird's-eye view, shot on 16mm wide lens
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Set in South Korea: Korean low-rise apartment blocks, Korean street layout and road markings. No company name, logo, or lettering anywhere in the frame.
Text handling: no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the rain-soaked hillside and the ground below it) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 집중호우 산비탈
```

### [카드 2]
**텍스트**
```text
17일 새벽 4시 반쯤 옥포동에서
아파트 뒤 비탈이 무너져 내렸다
토사가 1층을 그대로 파묻었다
*20대 남성이 숨지고 2명이 다쳤다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a rescue worker's gloved fingertips stopped just short of a window frame half buried in mud. Three or four emergency workers in helmets and rain gear stand and crouch at the base of a low-rise Korean apartment block, all of them facing the same buried ground-floor window while one reaches toward it. A wall of collapsed earth and broken branches has pushed against the building up to the height of that window, and the buried window frame sits in the upper-center of the frame. Rain is still falling and a handheld work light throws one narrow beam across the mud. No injured person, no body and no victim is visible anywhere in the frame.
Camera: wide shot from eye-level, shot on 35mm lens
Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground, desolate stillness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows
Set in South Korea: Korean low-rise apartment block exterior, Korean emergency rain gear. No company name, logo, or lettering anywhere in the frame.
Text handling: no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the mud-covered ground at the base of the building) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 옥포동 산사태 아파트 매몰
```

### [카드 3]
**텍스트**
```text
경찰 조사에서 그의 직업이 확인됐다
*삼성중공업 조선소 근로자였다*
그날 그 회사는 일부 도크가 잠겼고
특근 노동자에게 나오지 말라고 알렸다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the black still water surface where the working floor of the dock used to be. A shipyard dry dock stands completely empty of people, its stepped concrete floor swallowed by dark standing water that has climbed to the lower rungs of the access ladders. A gantry crane frame and a partly built hull section rise above the waterline in the upper-center of the frame, their reflections broken by rings of falling rain. Coiled cables and an abandoned toolbox sit on the highest step still above the water. No people are visible.
Camera: full shot from a high angle, shot on 24mm wide lens
Lighting/mood: cold blue dim interior light, heavy and suffocating, faint trembling tension
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows
Set in South Korea: Korean shipyard dry dock structure. No company name, logo, or lettering anywhere in the frame.
Text handling: no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the flooded dock floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
삼성중공업 거제조선소 도크
```

### [카드 4]
**텍스트**
```text
*회사는 야드 문을 닫을 수 있었다*
집 뒤 비탈을 닫아줄 곳은 없었다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the chain and padlock hanging dead still across the closed yard gate. A heavy steel shipyard entrance gate is shut and wrapped with a chain, seen from close and from below so its bars rise above the viewer, with the chained latch anchored in the upper-center of the frame. Past the bars and beyond a stretch of wet asphalt, the ground climbs into a dark saturated hillside with low residential rooftops packed at its foot, and that slope has no gate, no fence and no barrier of any kind. Rain falls in continuous vertical lines across both the locked gate and the open slope. No people are visible.
Camera: tight close-up from a low angle, shot on 35mm lens
Lighting/mood: single pool of hard light isolating the subject in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows
Set in South Korea: Korean industrial yard gate, Korean hillside housing rooftops. No company name, logo, or lettering anywhere in the frame.
Text handling: no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the wet asphalt of the yard entrance running back to the slope) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 조선소 정문 출입구
```

### [카드 5]
**텍스트**
```text
거제시가 새벽 2시 10분 문자를 보냈다
안전한 지역으로 대피하라고 했다
*어디로 가라는 말은 없었다*
오전 6시 반 거제 도로 26곳이 막혔다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the pale phone-screen light caught on one resident's fingertips in the dark. A single Korean resident in a rain poncho stands at the edge of a flooded street before dawn, holding a phone whose blank glowing screen is the brightest thing in the frame, head turned toward the water ahead of them. Beyond the resident the road disappears under brown water, a traffic barrier and a half-submerged car block the way forward, and one streetlight reflects long on the wet surface. The raised phone and the resident's face sit in the upper-center of the frame. The phone screen shows no readable characters at all.
Camera: medium shot from eye-level, shot on 50mm standard lens
Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground, desolate stillness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows
Set in South Korea: Korean street layout, Korean road markings and traffic barrier. No company name, logo, or lettering anywhere in the frame.
Text handling: no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the flooded road surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 장평동 도로 침수 차량
```

### [카드 6]
**텍스트**
```text
경남도는 전날 이미 비상 2단계였다
급경사지를 더 살피겠다고 했다
그런데 거제도 통영도 사면이 무너졌다
*그 비탈이 목록에 있었는지는 모른다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the few steps of gap left between two inspectors as they both tilt their heads back at the same slope. Two Korean officials in rain gear stand on a narrow road at the foot of a steep wet embankment, one half a step ahead of the other, both looking up the slope face and neither looking at the other. A concrete retaining wall runs along the base and a drainage channel carries muddy water past their boots. The dark rain-soaked upper slope fills the upper-center of the frame and towers over both of them. No lettering appears on their gear or anywhere in the frame.
Camera: full shot from a low angle, shot on 28mm lens
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Set in South Korea: Korean hillside retaining wall and drainage channel, Korean road markings. No company name, logo, or lettering anywhere in the frame.
Text handling: no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the wet slope face running down into the road at its foot) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
급경사지 산사태 취약지역 점검
```

### [카드 7]
**텍스트**
```text
공장은 그날 하루를 멈추기로 정했다
출근을 막은 건 출근길을 지킨 조치였다
그가 잠든 1층엔 그런 조치가 없었다
*회사가 닫을 수 있는 문은 정문까지였다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the mud line stopped exactly at the height of a ground-floor window sill, and the emptiness behind that glass. Thin morning light breaks through a still-overcast sky onto the front of a low-rise Korean apartment block, seen straight on and level. Drying mud, broken branches and scattered debris cover the ground and reach halfway up the ground-floor window, while the windows on the floors above stand ordinary and intact with one of them lit. That buried ground-floor window and the lit window above it sit in the upper-center of the frame. Far behind the rooftops the faint outline of shipyard cranes is just visible. No people are visible.
Camera: wide shot from eye-level, shot on 35mm lens
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Set in South Korea: Korean low-rise apartment block facade, Korean residential ground layout. No company name, logo, or lettering anywhere in the frame.
Text handling: no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the mud-covered ground in front of the building) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
산사태 토사 아파트 1층 수습
```
