# 📚 '모든 동물은 평등하다'는 왜 한 줄 덧붙여 무너졌나

**[프롬프트 설계]**
- 화풍: B 극화 — 권력이 언어를 고쳐 쓰는 과정을 다루는 우화라, 한국 웹툰 극화의 굵은 먹선과 명암 낙차로 무게를 잡는다
- 분위기: thumb_dispatch의 차가운 새벽(LGT02) 정조를 이어받는다 — 아무 일도 없었던 듯 조용한데 이미 무언가 바뀌어 있는 서늘함, 그 서늘함이 마지막 카드에서만 아침으로 풀린다
- 연출 방향: 뉴스 대신 피드를 보는 고등학생이 멈추는 자리는 '책은 다 읽었는데 쓸 게 없는 손'이다 — 그 손에서 출발해 소설 안으로 들어갔다가 같은 책상으로 돌아온다. 전할 관점은 대응표가 시험은 통과시키지만 오웰이 보여준 건 벽의 문장이 밤새 한 줄 길어지는 *과정*이라는 것. 그래서 의도를 ①멈춘 펜 끝 ②단상 위 돼지가 벽에 던지는 사람 모양 그림자 ③아직 젖어 번들거리는 마지막 한 줄 ④그 줄을 올려다보는 늙은 말의 충혈된 눈에 몰고, 마지막엔 학생의 눈이 독자를 마주 본다. 악센트 #0FFD02는 '덧붙은 한 줄'의 계보(빈 괘선 → 돼지 눈 → 젖은 페인트 → 단상 조명 → 밑줄)에만 얹어 시선을 한 갈래로 끈다
- 독자 동선: **발단** 카드1 → **전개** 카드2 → **피크** 카드3 → **해소** 카드4 → **시사점** 카드5 · 훅 = 카드1 끝(단서형 — 줄거리를 건너뛴 글, 그럼 뭘 쓰나)+카드2 끝(예고형 — 표는 깔끔한데 소설은 안 그랬다) · 착지 = 불편해진 쪽이 진짜 읽은 문장이다
- 연속성 앵커: 학생 = `Recurring subject — a Korean high school student, a girl in her late teens, shoulder-length black hair tied back, wearing a dark navy school blazer over a white shirt`(카드1·5) / 늙은 짐말 = `Recurring animal subject — an old grey-brown draft horse with a heavy neck, a white blaze down his face and a frayed rope halter`(카드2·3) / 반복 장소 = `the same weathered plank wall inside the barn`(카드2·3)

### [카드 1]
**텍스트**
```text
책은 진작에 다 읽어 뒀는데
*생기부 칸 앞에서 손이 멈춘다*
동물농장을 세특용으로 푼 글은
줄거리를 통째로 건너뛰었다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: her pen tip hovering a centimeter above an empty ruled box, held there too long, not touching the paper. Recurring subject — a Korean high school student, a girl in her late teens, shoulder-length black hair tied back, wearing a dark navy school blazer over a white shirt, sits at a study desk with her chin propped on one hand, eyes cast down at the blank record form in front of her. A worn paperback lies open and face-down beside the form, its spine cracked from a full reading, one corner of the desk holding a cold cup. The desk surface fills the frame from edge to edge, a Korean late-night study room around it, the composition leaving nose room on the right side toward the next beat.
Camera: wide shot holding the whole desk and figure in spatial context, from a high angle looking down on the desk, small and observed, shot on a 35mm lens with natural documentary perspective and minimal distortion
Lighting/mood: warm soft desk-lamp light, quiet wistful tone, the rest of the room falling away into cold blue pre-dawn shadow
Accent: monochrome desaturated base with a single color accent, neon green #0FFD02 on the thin ruled line of the empty form, film-noir low-key lighting, deep shadows
Korean default setting: Korean high school interior, Korean stationery and desk furniture, no foreign signage.
Text handling: the record form shows only empty ruled boxes with no printed words, the open book is face-down so no page text is visible, no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the desk surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
고등학생 야간자율학습 책상
```

### [카드 2]
**텍스트**
```text
그 글은 인물을 역사로 바꿔 읽는다
*나폴레옹은 스탈린, 스노볼은 트로츠키*
묵묵히 일한 복서는 프롤레타리아다
표는 깔끔하다. 소설은 안 그랬다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the pig's raised foreleg and the man-shaped shadow it throws on the boards behind him. A heavy pig stands on a low wooden platform at the center of the barn, foreleg lifted mid-address, chin up, gazing out over the floor toward the right edge, and his cast shadow on the same weathered plank wall inside the barn carries the silhouette of a uniformed man in boots. At the left edge a second, leaner pig is being crowded out of frame by two large dogs, head turned back over his shoulder. Recurring animal subject — an old grey-brown draft horse with a heavy neck, a white blaze down his face and a frayed rope halter, stands motionless in the rear with his head lowered, watching the platform without moving.
Camera: medium shot framing the standing pig from the waist up with the platform, from a low angle looking up for dominance and dramatic presence, shot on a 50mm standard lens with minimal distortion and natural cinematic composition
Lighting/mood: single hard side-light cutting across the subject, deep chiaroscuro shadows, tense atmosphere
Accent: monochrome desaturated base with a single color accent, neon green #0FFD02 caught in the pig's eye highlight, film-noir low-key lighting, deep shadows
Non-Korean context: this is an English farm barn interior of the 1940s, wooden construction, no Korean signifiers.
Text handling: no writing anywhere on the boards in this frame, no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the barn plank wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Animal Farm Napoleon pig
```

### [카드 3]
**텍스트**
```text
"모든 동물들은 평등하다"고 적힌 벽에
그 밤 한 줄이 덧붙었다
*"어떤 동물들은 더욱 평등하다"*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the old horse's bloodshot eye, wide and unfocused in a vacant stare, a single wet white streak mirrored in it. Recurring animal subject — an old grey-brown draft horse with a heavy neck, a white blaze down his face and a frayed rope halter, lifts his head toward the boards, his profile filling the left half of the frame. Behind him the painted lines of the commandments run across the same weathered plank wall inside the barn at a steep oblique angle and slightly out of focus, so the brush strokes read as paint texture rather than as readable words, and the lowest line is still wet and glistening as if added an hour ago. A ladder and an open paint pot stand at the base of the wall, kept low in shadow.
Camera: tight close-up with the face filling the frame for intimate pressure, from a worm's-eye view near the ground looking up along the wall, shot on an 85mm portrait lens with soft background separation
Lighting/mood: a single pool of hard light isolating the wall in surrounding blackness, claustrophobic loneliness, deep navy 7500K pre-dawn cast bleeding in from outside
Accent: monochrome desaturated base with a single color accent, neon green #0FFD02 in the wet glisten of the freshly added bottom line, film-noir low-key lighting, deep shadows
Non-Korean context: this is an English farm barn interior of the 1940s, wooden construction, no Korean signifiers.
Text handling: the painted lines are seen at an extreme oblique angle and defocused so that no letter is legible anywhere, no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the barn plank wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Animal Farm seven commandments barn
```

### [카드 4]
**텍스트**
```text
그 글은 이 장면에서 미헬스를 부른다
*1911년 그가 세운 과두제의 철칙이다*
민주적으로 출발한 조직도 커지면
선출된 자가 선출한 자들을 지배한다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the widening vertical gap between the four figures standing high on the rostrum and the packed rows of upturned heads far below them. A crowded European party congress hall of the 1910s, where hundreds of delegates sit shoulder to shoulder across the hall floor with their faces tilted up toward a raised rostrum, while a handful of leaders stand on it looking down over the room. In the near foreground at the left, a man in a high-collar suit stands apart from the rows with a small notebook open in one hand, watching the rostrum rather than the crowd. The hall floor runs unbroken from the bottom of the frame all the way to the far wall.
Camera: wide shot holding the full figures and the surrounding hall, from a low angle at delegate seat height looking up toward the rostrum, shot on a 24mm wide lens for cinematic spatial context
Lighting/mood: a harsh single overhead light pooling on the rostrum, deep surrounding black over the seated rows, oppressive
Accent: monochrome desaturated base with a single color accent, neon green #0FFD02 in the overhead shaft falling on the rostrum, film-noir low-key lighting, deep shadows
Non-Korean context: this is a European assembly hall of the 1910s, period clothing, no Korean signifiers.
Text handling: no banners, no placards, no lettering on any surface in this frame, no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the hall floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Robert Michels party congress
```

### [카드 5]
**텍스트**
```text
대응표를 옮겨 적으면 세특은 채워진다
그 명제를 자기 학교 학생회에 대보면
그때부터 문장이 불편해진다
*불편해진 쪽이 진짜 읽은 문장이다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: her eyes lifting straight into the camera, steady and unsettled, the pen finally at rest in her hand. Recurring subject — a Korean high school student, a girl in her late teens, shoulder-length black hair tied back, wearing a dark navy school blazer over a white shirt, sits upright at the same study desk and looks directly out of the frame with unwavering eye contact, one hand resting flat on a half-filled notebook page. Morning light has replaced the lamp, which now stands switched off at her elbow. The desk surface runs edge to edge beneath her and the room behind has opened up and softened.
Camera: medium shot framing her from the waist up for face and gesture, front-on with a direct gaze and symmetrical composition, from eye level with a neutral balanced perspective, shot on a 35mm lens with natural documentary perspective
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: monochrome desaturated base with a single color accent, neon green #0FFD02 on one underlined phrase in the notebook, muted daylight contrast
Korean default setting: Korean high school interior, Korean stationery and desk furniture, no foreign signage.
Text handling: the notebook page is seen at a shallow angle so the handwriting reads as texture only with no legible words, no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the desk surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
고등학생 교실 창가 아침
```
