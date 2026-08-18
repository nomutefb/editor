# 조선소는 멈췄고, 1층은 못 멈췄다

**[프롬프트 설계]**
- 화풍: A 한국웹툰 수채화 — 사망자가 나온 재난이라 극화의 고발 톤이 참사를 키운다. 번짐과 여백이 새벽 비·젖은 흙의 정조를 그대로 옮긴다.
- 분위기: 차갑고 젖은 새벽의 정적. 비명이 아니라, 뒤늦게 밝아오는 빛의 씁쓸함. thumb_dispatch의 새벽 한색 톤(젖은 노면 반사·황량한 정적)과 부재의 정조를 키노트로 계승한다.
- 연출 방향: 이 기사를 가장 강하게 읽을 사람은 비탈이나 옹벽 아래 저층에 사는 사람, 그리고 '오늘은 나오지 마라'고 대신 정해주는 회사가 없는 자리에서 일해본 사람이다. 그래서 멈추게 하는 것은 참혹한 현장이 아니라 **높이의 비대칭** — 흙이 닿는 첫 번째 면인 1층 창턱, 그 위층에 아무 일 없이 켜진 창 하나, 그리고 비 속에 멈춰 선 크레인. 얼굴을 정면으로 파헤치는 대신 손끝·뒷모습·창의 불빛으로 감정을 맺어, 피해를 전시하지 않고도 "저 층이 내 집일 수 있다"에 닿게 한다. 전 카드가 공유하는 키노트 = 한 프레임에 어둠을 깔고 따뜻한 빛 한 점만 살린다.
- 독자 동선: **발단** 카드1(사흘의 비와 새벽 2시 10분 문자)→**전개** 카드2~3(문자에 목적지가 없었다 → 두 시간 뒤 비탈이 무너졌다)→**피크** 카드4(구조와 사망)→**해소** 카드5~6(거제 전체의 그 새벽 → 회사만 하루를 접었다)→**시사점** 카드7 · 훅=카드1 끝(예고형: 문자 한 통이 갔다)+카드2 끝(단서형: 그 문장 안에 없던 것) · 착지 한 줄 요지 = 회사엔 대신 정해주는 곳이 있었고 비탈 아래 1층 집엔 없어서, 나갈지 말지를 문자 한 줄로 혼자 정해야 했다.
- 연속성 앵커: 반복 인물 (없음) / 반복 장소 — Recurring location - a low-rise apartment block on a hillside slope in a small Korean port city, its first-floor windows half buried in wet brown soil. (카드 3·7 Scene에 그대로 복사)

### [카드 1]
**텍스트**
```text
경남 거제에 사흘 동안 782.5㎜,
*그중 400㎜가 하룻밤 사이에 몰렸다*
8월 17일 새벽 2시 10분,
거제시가 전 시민에게 문자를 보냈다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: one amber-lit window high on a dark apartment block, the only warm point anywhere in the frame. Heavy rain falls in dense diagonal sheets over a small Korean port city at night, and the low street below has flooded until parked cars sit half submerged with only their roofs breaking the water. Hillside apartment blocks rise behind the flooded street with nearly every window dark. Nobody is outside, and the flooded street runs away toward the right edge of the frame.
Camera: extreme long shot from a bird's-eye overhead angle, shot on a 14mm ultra-wide lens
Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground, desolate stillness
Accent: monochrome desaturated base with a single color accent (the story's symbolic color, the warm amber glow of the one lit window), film-noir low-key lighting, deep shadows, the accent kept as one soft point within the pastel wash.
Text handling: avoid incidental lettering entirely - no shop signage text, no street sign characters, no banner text; any surface that would carry writing is cropped, turned away from the camera, or dissolved into rain blur.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the flooded street surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 폭우 도로 침수
```

### [카드 2]
**텍스트**
```text
"안전한 지역으로 대피하여"
그 새벽 도시 전체로 간 문장이다
그런데 안전한 지역이 어디인지는
*그 문장 안에 적혀 있지 않았다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a hand lit only by the pale glow of a phone screen, the fingers gone still instead of scrolling. A resident lies awake in a dark room, propped on one elbow under a thin summer blanket, holding the phone close and looking down at it, with only the jaw and the lit hand inside the frame. Rain streaks the window behind and the corners of the room fall away into black. The screen carries no readable characters at all, only a soft blurred band of pale light spilling toward the right edge of the frame.
Camera: close-up shot from a high angle looking down, shot on a 100mm macro lens
Lighting/mood: cold blue screen under-glow lighting the hand from below in a dark room, restless unease
Accent: monochrome desaturated base with a single color accent (the story's symbolic color, a warm amber light source in the scene), film-noir low-key lighting, deep shadows, the accent kept as one soft point within the pastel wash.
Text handling: the phone screen must show no glyphs, no letters and no numbers - render it as a soft blurred rectangle of pale light only; no other lettering anywhere in the room.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the crumpled bedding surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제시 재난문자
```

### [카드 3]
**텍스트**
```text
두 시간 남짓 뒤인 새벽 4시 반쯤
*거제시 옥포동에서 산비탈이 무너졌다*
쏟아진 토사가 아파트 1층을 파묻었고
그 집 안에 사람들이 있었다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the blunt edge of the mudslide where it stops dead against a first-floor window frame, half the glass already gone under wet brown soil. Recurring location - a low-rise apartment block on a hillside slope in a small Korean port city, its first-floor windows half buried in wet brown soil. The hillside behind the block has given way and poured down, dragging broken branches and a snapped young tree into the pile, and one parked car at the edge is buried up to its hood. Rain is still falling, and a single upper window burns amber far above the dark buried ground floor.
Camera: wide shot from a ground-level worm's-eye angle, shot on a 20mm wide lens
Lighting/mood: a single pool of hard light isolating the buried facade in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single color accent (the story's symbolic color, the warm amber glow of the one lit upper window), film-noir low-key lighting, deep shadows, the accent kept as one soft point within the pastel wash.
Text handling: no building name plate, no unit numbers, no signage characters anywhere - keep every lettering-bearing surface buried in soil, cropped out, or turned away from the camera.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the sheet of wet brown soil) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 옥포동 산사태
```

### [카드 4]
**텍스트**
```text
구조된 50대 여성은 왼팔이 부러졌다
그 옆에서 꺼낸 20대 남성은
심정지 상태로 병원에 실려 갔고
*끝내 숨졌다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a rescuer's mud-caked gloved hand gone completely still on the wet soil, fingers spread where they stopped digging. The hand fills most of the frame at the edge of a buried doorway, and just behind it, thrown far out of focus, sit the shoulder and helmet rim of a second worker and the narrow beam of a handlight angled down into the mud. A folded emergency blanket lies unopened at the edge of the frame. Rain still beads on the glove and on the churned soil around it.
Camera: extreme close-up from an eye-level angle, shot on a 100mm macro lens
Lighting/mood: cold blue dim light, heavy and suffocating, faint trembling tension
Accent: monochrome desaturated base with a single color accent (the story's symbolic color, the warm amber beam of the handlight), film-noir low-key lighting, deep shadows, the accent kept as one soft point within the pastel wash.
Text handling: no lettering on the helmet, no unit markings, no equipment labels, no characters anywhere in the frame.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the churned wet soil surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
산사태 매몰 소방 구조
```

### [카드 5]
**텍스트**
```text
*그 새벽 거제 전체가 같은 상태였다*
차와 집에 갇힌 주민 20명 넘게
소방에 구조를 요청했고
아주동에서는 100여 명이 대피했다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: an older woman's grip closing on a younger neighbour's forearm as they climb, knuckles pale with the effort. About a dozen residents in raincoats and slippers walk up a steep wet alley away from the hillside, carrying almost nothing, and several glance back over their shoulders toward the slope behind them. A firefighter at the corner waves them forward with a handlight. The rain has thinned and the sky over the rooftops has turned pale grey.
Camera: full shot from an eye-level angle, shot on a 35mm lens
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single color accent (the story's symbolic color, the warm amber beam of the firefighter's handlight), muted daylight contrast, the accent kept as one soft point within the pastel wash.
Text handling: no signage text, no shop lettering, no uniform lettering, no characters on any surface - keep alley walls plain and any sign turned away or blurred.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the wet sloping alley surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 아주동 주민 대피
```

### [카드 6]
**텍스트**
```text
같은 날 한화오션과 삼성중공업은
*도로가 통제됐다며 출근을 막았다*
그 시각 거제 시내에선
도로 26곳이 차량 통행 불가 상태였다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a shipyard worker standing alone at the closed gate, shoulders dropped, his phone still in his hand after reading the notice. A plastic barricade and a chain shut the gate across the road, and behind it enormous unmarked gantry cranes stand motionless in the rain with their outlines softened by mist. Further back a second worker has already turned to walk home. Water runs along the road and an overturned traffic cone lies where the flooding pushed it, and no company name or logo appears anywhere in the frame.
Camera: wide shot from a low angle looking up, shot on a 24mm wide lens
Lighting/mood: flat cold even light, no shadow no warmth, detached and watchful
Accent: monochrome desaturated base with a single color accent (the story's symbolic color, a warm amber light source in the scene such as a lit guard booth window), muted daylight contrast, the accent kept as one soft point within the pastel wash.
Text handling: absolutely no company logos, no brand marks, no gate signage characters, no notice board text - the gate sign is turned away from the camera and carries no lettering.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the wet road surface in front of the gate) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 조선소 크레인
```

### [카드 7]
**텍스트**
```text
회사에는 오늘은 나오지 말라고
대신 정해주는 곳이 있었다
잠든 새벽 1층 집에는 그런 곳이 없었다
*나갈지 말지는 문자 한 줄로 혼자 정했다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a resident's face turned straight to the camera, eyes steady and tired, a dark dead phone held loosely at her side. Recurring location - a low-rise apartment block on a hillside slope in a small Korean port city, its first-floor windows half buried in wet brown soil. She stands in front of that buried first-floor window in the morning, a raincoat pulled over sleepwear and mud past her ankles, facing the viewer without moving. Above and behind her the upper-floor windows are open and entirely ordinary, and a shovel leans untouched against the wall.
Camera: medium shot from an eye-level front-on angle, shot on a 50mm standard lens
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: monochrome desaturated base with a single color accent (the story's symbolic color, the warm amber morning light falling on the buried window), muted daylight contrast, the accent kept as one soft point within the pastel wash.
Text handling: no building name plate, no unit numbers, no phone screen glyphs, no signage characters anywhere in the frame.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the mud-covered ground surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
산사태 아파트 1층 토사
```
