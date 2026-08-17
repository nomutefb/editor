# AI가 써도 된다는 상, 왜 문이 닫히나

**[프롬프트 설계]**
- 화풍: B 극화 — 감정 사건이 아니라 제도·비용 구조가 축이라, 종이 결과 그림자를 날카로운 선으로 잡는 극화가 사실성을 준다
- 분위기: 흐린 낮의 편집부 — 누구도 화내지 않는데 조용히 감당 못 하게 되는 무게, 사람 없는 지면 위에 종이만 쌓인 정조
- 연출 방향: 독자훅은 '보낸 적 있는 사람'의 허탈함이다 — 반칙한 사람이 하나도 없는데 문이 닫힌다는 낙차. 그래서 카드마다 '적발되는 얼굴'을 찾지 않고 **종이 더미의 높이·요강 한 줄·읽는 손**만 붙든다. 강조점은 셋: 두 배로 솟은 원고 기둥(양), 요강의 허용 문구(반칙 부재), 그 원고를 한 장씩 넘기는 사람 손(비용). 과녁을 AI를 쓴 사람이 아니라 비용을 안 정해 둔 설계에 두려면 카메라가 사람 얼굴을 심문하지 않아야 한다
- 독자 동선: **발단** 카드1(두 배로 들어온 원고)→**전개** 카드2~3(AI 추정·서식 버릇이라는 유일한 단서)→**피크** 카드4(요강에 이미 허용이라 적혀 있다)→**해소** 카드5(깨진 균형 = 쓰는 비용 0, 읽는 비용 그대로)→**시사점** 카드6(통로가 닫히는 값은 몇 년 뒤 청구된다) · 훅=카드1 끝(단서형 — '두세 편'이라는 미완 수치를 다음 장이 즉시 회수)+카드3 끝(예고형 — 그 단서가 사라진다) · 착지 = 문을 여는 비용이 감당 밖이 됐는데 누가 낼지는 아무도 안 정했다
- 연속성 앵커: (없음)

### [카드 1]
**텍스트**
```text
원고가 1,012편 들어왔다
지난해 484편의 두 배가 넘는다
예년엔 400편 안팎이던 상이다
편집부는 *열 편 중 두세 편을 의심한다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the sheer height of the paper stacks, cropped off by the top edge so the top is never shown. Rows of thick paper manuscript bundles stand on a long editorial desk in an empty publishing office, the front bundle catching a narrow shaft of light that reveals the grain of the cut paper edges while the rear rows recede into darkness. A few loose sheets have slid off the front bundle and hang half over the desk edge. No people are present. The paper surfaces carry no letters, no seals, no logos, only grain and shadow.
Camera: wide shot, full desk and rows of bundles, from low angle shot, looking up, exaggerating the height of the stacks, shot on 24mm wide lens, cinematic wide shot, spatial context
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood, one narrow shaft picking out the front bundle
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the exposed cut edge of the front paper bundle, muted daylight contrast
Text handling: no readable text anywhere; all paper is blank with only fiber grain and shadow. Avoid signage, avoid nameplates.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the long editorial desktop) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
공모전 응모 원고 더미 편집부 책상
```

### [카드 2]
**텍스트**
```text
늘어난 건 이 상만이 아니다
미스터리 공모전은 461편에서 731편
전격소설대상은 40% 늘었고
*신초신인상은 30% 늘었다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: four separate paper stacks of uneven height standing side by side on one continuous floor, read at a glance as one repeated problem. Seen from directly above, four bundles of manuscript paper sit in a row on a bare office floor, each tied with plain string, three of them clearly taller than the fourth. No people are present. Every sheet is blank, carrying only paper grain and the shadow each bundle casts across the floor.
Camera: full shot of all four bundles, from overhead shot, bird's-eye view, top-down angle, layout, geometry, shot on 35mm lens, natural documentary perspective, minimal distortion
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood, even flat light across the floor
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the string binding the tallest bundle, muted daylight contrast
Text handling: no readable text anywhere; no labels on the bundles, no numbers, blank paper only. Avoid signage.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the bare office floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
이 미스터리가 대단하다 대상 공모전 응모작
```

### [카드 3]
**텍스트**
```text
AI를 알아본 단서는 글솜씨가 아니었다
앞부분엔 단락 사이 공백이 한 줄씩 있다가
뒷부분에서 문체가 갑자기 매끄러워지며
*그 공백이 사라진다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a fingertip pressing down on the blank gap between two blocks of paper texture, as if the gap itself were the evidence. A single hand enters from the upper left and holds one sheet flat against the desk, the finger stopped on an empty horizontal band across the middle of the sheet, the eye of the reader implied just outside the frame. The sheet shows only ruled fiber texture and that one wider empty band; there are no letters, no words, no printed characters on it. Only the hand and the sheet are lit.
Camera: extreme close-up, single detail, hand and one sheet, from high angle shot, looking down at the desk, shot on 100mm macro lens, fine detail, shallow depth of field, precise texture
Lighting/mood: warm soft desk-lamp light, quiet wistful tone, deep shadow beyond the small pool of light
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) faintly tracing the empty band under the fingertip, film-noir low-key lighting, deep shadows
Text handling: the sheet must stay blank — render paper fiber and ruling texture only, no letters or characters of any kind. Avoid document body text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the desktop with the single sheet lying on it) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
원고 교정 손 원고지 여백
```

### [카드 4]
**텍스트**
```text
그런데 이 상은 AI를 금지한 적이 없다
응모 요강에 *이용도 가능하다*고 적혀 있다
반칙한 사람이 없는데 상이 흔들린다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: one folded corner of a single guideline sheet standing upright, the crease catching the only light in the room. A lone sheet of paper leans upright against a dark wall, its lower corner folded back on itself so the fold reads as the line someone stopped at. Nothing else occupies the space; the surrounding desk is bare and swallowed by shadow, and no people are present. The sheet is blank apart from paper grain, the fold's shadow, and faint ruling.
Camera: tight close-up, the upright sheet filling the frame, from eye-level shot, neutral perspective, realistic, side view, profile shot, clear silhouette, shot on 85mm portrait lens, soft background separation
Lighting/mood: single hard side-light cutting across the subject, deep chiaroscuro shadows, tense atmosphere, the darkest frame of the sequence
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) burning along the folded crease, film-noir low-key lighting, deep shadows
Text handling: keep the sheet blank — paper grain and ruling only, no letters, no clauses, no printed characters. Avoid document body text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the dark desktop the sheet stands on) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
하야카와 SF 콘테스트 응모 요강
```

### [카드 5]
**텍스트**
```text
깨진 건 오래된 균형이다
한 편에 몇 달이 든다는 전제로
출판사는 응모료를 안 받고 다 읽어 왔다
*쓰는 비용만 0이 됐고 읽는 값은 그대로다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the distance between one seated reader's hands and the wall of unread bundles still waiting beside them. A single editor sits at the far end of a long desk turning one sheet, seen from behind so the face is not visible, while the manuscript bundles stacked beside and above them dwarf the small lit area where the hands work. The reader's gaze is angled down at the sheet in their hands. No other people are present, and every sheet in the room is blank, showing only grain and shadow.
Camera: wide shot, full body of the seated reader and the surrounding bundles, from eye-level shot, neutral perspective, back shot, rear view, subject from behind, solitude, shot on 35mm lens, natural documentary perspective, balanced subject and background
Lighting/mood: single pool of hard light isolating the figure in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the one sheet held in the reader's hands, film-noir low-key lighting, deep shadows
Text handling: all paper stays blank — fiber grain only, no letters, no headings, no printed characters anywhere. Avoid signage.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the long desktop running the depth of the room) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
출판사 편집자 원고 심사 책상
```

### [카드 6]
**텍스트**
```text
신인상은 학력도 인맥도 안 보고
원고만 보는 유일한 문이었다
그 문을 여는 값이 감당 밖이 됐는데
*누가 낼지는 아무도 안 정했다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the narrowing gap of a door left half open, with light falling on the empty threshold nobody is standing in. A tall office door stands ajar at the end of a bare corridor, and a thin band of diffused daylight spills across the floor through the opening toward the viewer. One loose sheet of paper lies on the threshold where it slipped from someone's hands. No people are present, and the sheet and the walls carry no letters, no plates, no logos, only texture and shadow.
Camera: medium shot, waist-height framing of the doorway and threshold, from front-on shot, direct symmetrical composition, facing the door, shot on 50mm standard lens, minimal distortion, natural cinematic composition
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy, a single band of light released across the floor
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the edge of the sheet lying on the threshold, muted daylight contrast
Text handling: no readable text — the sheet, walls and door carry no letters, no nameplates, no numbers. Avoid signage.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the corridor floor running to the doorway) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
출판사 편집부 문 복도
```
