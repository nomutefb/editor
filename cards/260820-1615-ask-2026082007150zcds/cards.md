# 청와대는 안 뚫렸다는데, 인증기관에서 명함정보가 나왔다

**[프롬프트 설계]**
- 화풍: B 극화 — 국가 배후 해킹과 위탁 고리의 책임을 따지는 구조 비판이라, 사실성과 무게를 함께 지는 극화가 맞다.
- 분위기: 늦은 밤 전산실의 차갑고 균질한 기계광. 아무것도 부서지지 않았는데 명단만 소리 없이 빠져나간 뒤의 허탈. 해명은 있으나 안심은 없는 정조(thumb_dispatch의 화면 언더글로·허탈 응시를 조명 톤과 정조로만 계승).
- 연출 방향: 뉴스를 안 보는 독자도 "내 서버는 멀쩡한데 내 명함은 남의 서버에서 털렸다"는 모순 하나로 멈춘다 — 그러니 매 카드에서 *지켜진 것*(굳게 닫힌 서버랙, 단호한 해명대)과 *새어 나간 것*(바닥에 흩어진 명함 한 장)을 같은 프레임에 두고, 그 사이에서 아무것도 할 수 없는 사람의 눈과 손을 강조점으로 잡는다. 명함 한 장이 덱 전체를 관통하는 반복 오브젝트이고, 명도는 起 균질 형광 → 承 하강 → 轉 단일 광웅덩이 최암 → 結 확산광 릴리즈로 누적시킨다.
- 독자 동선: 제시 카드1 → **발단** 카드2 → **전개** 카드2~3 → **피크** 카드4 → **해소** 카드5 → **시사점** 카드6 · 훅=카드1 끝(예고형: 모순만 던지고 이유는 유보 → 카드2 첫 줄이 즉시 회수)+카드3 끝(단서형: '인증 업무를 맡은 회사' — 어디인지 유보 → 카드4 첫 줄이 회수) · 착지 = 표적이 된 곳들의 공통점은 유명세가 아니라 남의 명단을 대신 들고 있었다는 것이고, 내 이름이 어느 서버에 적히는지는 내가 고른 적이 없다.
- 연속성 앵커: Recurring subject — a Korean man in his 40s with short neatly parted hair and rimless glasses, wearing a charcoal suit with the tie slightly loosened and an ID lanyard around his neck / Recurring location — a dim late-night server room with tall equipment racks and overhead cable trays

### [카드 1]
**텍스트**
```text
청와대 서버는 뚫리지 않았다
8월 20일 경찰이 확인한 사실이다
그런데 해커가 빼간 자료에서
*청와대 관계자들의 신상이 나왔다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: his eyes fixed on the business cards scattered across the floor at his feet, jaw set hard. Recurring subject — a Korean man in his 40s with short neatly parted hair and rimless glasses, wearing a charcoal suit with the tie slightly loosened and an ID lanyard around his neck. He stands in a late-night server room with one hand still resting on the locked cabinet door of an intact equipment rack towering beside him, the other hand hanging open and empty. Dozens of cards lie face-down and edge-on across the raised floor panels, the trail of them leading toward the right edge of the frame, with nose room on the right and his body turned that way. Cable trays run overhead the full depth of the room.
Camera: wide shot from eye-level, shot on 35mm lens
Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the rack status LEDs only), muted daylight contrast
Korean setting by default: Korean man, Korean office interior conventions.
Text handling: no readable text anywhere; every business card is turned face-down or seen edge-on, and all rack labels are cropped out of frame.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the raised server-room floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
전산실 서버랙 명함
```

### [카드 2]
**텍스트**
```text
*뚫린 곳은 민간 인증기관 서버였다*
경찰이 그 자료를 분석해 보니
이름과 소속, 직함과 연락처가 나왔다
명함에 적히는 정보로 추정된다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the investigator's unblinking eyes and the hard flat line of her mouth, lit from below by the monitor. A single Korean police cyber investigator sits at a desk in a dark analysis room, seen from just behind her shoulder, leaning in toward a large monitor filled with an out-of-focus grid of rows and columns. Her right hand rests flat on a printed sheet beside the keyboard, the printed side angled away from view. Behind her the room falls into blackness broken only by two dormant monitors against the back wall.
Camera: over-the-shoulder shot from a slightly canted Dutch angle, shot on 70mm short telephoto lens
Lighting/mood: cold blue screen under-glow lighting the face from below in a dark room, restless paranoid unease
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on one highlighted row of the on-screen grid), film-noir low-key lighting, deep shadows
Korean setting by default: Korean woman, Korean office interior conventions.
Text handling: the on-screen grid is blurred into abstract rows and blocks with no legible characters; the printed sheet is tilted away so nothing on it can be read.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the dark back wall of the analysis room) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area against this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
경찰 사이버수사 분석실
```

### [카드 3]
**텍스트**
```text
청와대 관계자는 선을 그었다
"해킹은 사실이 아니다"
경찰도 같은 확인을 내놨다
*뚫린 건 인증 업무를 맡은 회사였다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the spokesman's flat controlled face and the horizontal cut of his hand slicing the air at chest height. A Korean government spokesman in his 50s in a dark navy suit stands at a plain podium in a briefing room, facing a taped photo line of tripod cameras and a cluster of microphones, his gaze level and unwavering toward the right edge of the frame with nose room on that side. Behind him a plain backdrop panel carries only an abstract emblem with no lettering. A single thin data cable runs across the floor from behind the podium and disappears past the edge of the frame.
Camera: medium shot from a low angle, shot on 50mm standard lens
Lighting/mood: flat cold even surveillance light, no shadow no warmth, detached and watchful
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the single recording light of the nearest camera), muted daylight contrast
Korean setting by default: Korean man, Korean press briefing conventions, no institutional logo of any kind.
Text handling: the backdrop bears an abstract emblem only, with no words, no name plates and no lettering anywhere in the room.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the plain briefing-room backdrop wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area against this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
청와대 브리핑룸 포토라인
```

### [카드 4]
**텍스트**
```text
경찰은 그 회사 이름을 밝히지 않았다
유출 시점도 규모도 공개되지 않았다
*내 명함이 거기 있었는지, 나는 모른다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a vacant thousand-yard stare, his unfocused eyes looking past everything, with one green pinpoint of light caught in the lens of his glasses. Recurring subject — a Korean man in his 40s with short neatly parted hair and rimless glasses, wearing a charcoal suit with the tie slightly loosened and an ID lanyard around his neck. His face fills the upper half of the frame, held inside a single narrow pool of hard light while the room behind him drops into complete blackness. One hand rises just into the bottom edge of that light, pinching a single business card turned edge-on so nothing printed shows.
Camera: tight close-up from eye-level, shot on 85mm portrait lens
Lighting/mood: single pool of hard light isolating the figure in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 as the one pinpoint reflection in his lenses), film-noir low-key lighting, deep shadows
Korean setting by default: Korean man, Korean office interior conventions.
Text handling: the business card is held edge-on with no printed side visible, and nothing else in the frame carries lettering.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the unbroken black interior wall behind him) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area against this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
야간 사무실 명함 남성
```

### [카드 5]
**텍스트**
```text
*경찰이 쫓는 건 이 사건만이 아니다*
언론사 서버 관리업체와 제약회사,
병원도 국가 배후 조직에 뚫렸다
2025년엔 정부 인증서가 표적이었다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the tired set of the lead investigator's shoulders as she leans both palms on the table edge, her eyes moving slowly across the layout below her. Four Korean police investigators stand around a long situation-room table before dawn, all looking down at a spread of documents and a hand-drawn diagram in which simple building pictograms — a broadcast tower, a hospital cross, a factory chimney — are linked by pinned string. Cold pre-dawn light enters through a window at the far end of the room and falls across the table.
Camera: wide shot from a high overhead bird's-eye angle, shot on 24mm wide lens
Lighting/mood: cold blue pre-dawn tone, desolate stillness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the pinned string linking the pictograms), muted daylight contrast
Korean setting by default: Korean investigators, Korean office interior conventions, no institutional logo of any kind.
Text handling: every document is angled away or cropped at the frame edge, and the diagram carries only pictograms and connecting lines with no words or letters at all.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the long situation-room table top) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
경찰 수사 상황실 상황판
```

### [카드 6]
**텍스트**
```text
표적의 공통점은 유명세가 아니었다
남의 명단을 대신 들고 있어서였다
내 이름이 어느 서버에 적혀 있는지
*나는 한 번도 고른 적이 없다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: his steady gaze looking straight out of the frame at the viewer, tired but level, no longer searching for anything. Recurring subject — a Korean man in his 40s with short neatly parted hair and rimless glasses, wearing a charcoal suit with the tie slightly loosened and an ID lanyard around his neck. He stands facing the camera in the aisle between two long rows of server racks that recede behind him into soft focus, holding a single business card between two fingers at chest height, turned edge-on so nothing printed is visible. His other hand hangs open at his side.
Camera: medium shot from eye-level, front-on and centered, shot on 85mm portrait lens
Lighting/mood: overcast diffused daylight from a high window, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the rows of rack status LEDs receding behind him), muted daylight contrast
Korean setting by default: Korean man, Korean office interior conventions.
Text handling: the business card is held edge-on with no printed side visible, and every rack label is out of focus with no legible characters.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the server aisle floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
데이터센터 서버랙 통로
```
