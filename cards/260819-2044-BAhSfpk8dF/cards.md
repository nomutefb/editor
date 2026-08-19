# 안 맞으면 규칙을 바꿨다

**[프롬프트 설계]**
- 화풍: B 극화 — 감정 사건이 아니라 정보가 만들어지고 유통되는 구조를 고발하는 기사라, 선이 또렷하고 명암이 깊은 극화가 맞다
- 분위기: 건조하고 서늘함 — 누가 속인 게 아니라 스스로 답을 정해두고 좌표를 찾은 흔적이 물증으로 남아 있는, 감정 없이 무거운 톤
- 연출 방향: 이 사건의 과녁은 사람이 아니라 절차다. 그래서 얼굴 대신 **손과 물증**(고쳐 쓴 종이·지운 자국·판마다 다른 쪽번호·꺼진 화면)에 강조점을 둔다. 독자가 멈추는 자리는 '해독이 맞나 틀리나'가 아니라 *작성자 본인이 남긴 문장*이므로, 카드가 진행될수록 화면은 넓은 밤에서 책상 한 뼘으로 조여들고 마지막에 다시 벌어진다. 실제 책 제목·표지·기관 표식·실존 인물은 전부 뺀다 — 책이 과녁이 아니다. 조명은 다이제스트가 고른 무채색 확산광의 정조를 이어받아 감시광에서 시작해 심문광까지 단계적으로 어두워지고, 마지막 카드에서만 아침빛으로 풀린다. 악센트는 네온그린 #0FFD02 한 색으로 '지금 눈길이 가야 할 한 점'만 찍는다
- 독자 동선: **발단** 카드1→**전개** 카드2~4→**피크** 카드5→**해소** 카드6→**시사점** 카드7 · 훅=카드1 끝(예고형: 불이 날 거라는 말이 돌았다 → 카드2 첫 줄이 즉시 회수)+카드4 끝(단서형: 좋아요 97·리포스트 23) · 착지 한 줄 요지 = 무너뜨릴 문장은 글 안에 다 있었고, 그걸 지나친 것이다
- 연속성 앵커: Recurring subject — a Korean adult in a plain dark long-sleeve top with short black hair, shown only as hands and forearms, the face never entering the frame. / Recurring place — the same cramped night desk with a scratched dark wooden surface.

### [카드 1]
**텍스트**
```text
8월 11일, 한 영상이 퍼졌다
뒤집힌 태극기와 반도체 로고가 있었고
대구 표식과 '8.13'이란 날짜가 있었다
*불이 날 거라는 말이 돌았다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere

Scene: Emotional focal point: the cold unblinking glow of a video still held at arm's length in a dark room. A pair of hands holds up a phone whose screen shows a crude collage — an upside-down flag shape, a landmass washed in red, a small flame mark and a short date stamp — while the person's face stays outside the frame in shadow. Two more dimly lit screens rest further back on the same desk surface, each showing the same collage, so the image reads as one clip multiplying outward. The gaze line and the phone both angle toward the right edge of the frame.

Camera: wide shot, full body, surrounding environment, movement, spatial context from high angle shot, looking down, vulnerable subject, small, observed, shot on 35mm lens, natural documentary perspective, balanced subject and background, minimal distortion, nose room on the right, gaze directed toward the right edge

Lighting/mood: flat cold even surveillance light, no shadow no warmth, detached and watchful

Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the date stamp glowing on the screen), film-noir low-key lighting, deep shadows

Text handling: keep all incidental writing out of the composition — no signage, no captions, no readable interface text; the date stamp is rendered as a short glowing numeric mark only, kept in the upper half of the frame, well clear of the lower portion.

Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.

MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.

Composition: ONE continuous surface (the dark wooden desk) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.

NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
난수방송 영상 캡처
```

### [카드 2]
**텍스트**
```text
13일 새벽 대구 서구에서 불이 났다
온라인은 반도체 공장을 지목했지만
*실제로 탄 건 섬유가공공장이었다*
한 동이 탔지만 인명피해는 없었다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere

Scene: Emotional focal point: the exhausted slackness of a firefighter's gloved hand letting a hose line drop at daybreak. Seen from far above, a single burned-out low factory shed sits collapsed at the center of a wet industrial lot, its roof gone and charred fabric bales spilling out of the opening. Fire trucks and small crew figures are arranged in a loose ring around it, packing up rather than fighting flames, and no casualty is present anywhere in the scene. Rolls of scorched textile, not machinery or clean-room equipment, mark what the building held.

Camera: extreme long shot, tiny subject, vast environment, scale, isolation from overhead shot, bird's-eye view, top-down angle, layout, geometry, shot on 20mm wide lens, subject and environment, documentary realism

Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground, desolate stillness

Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the cordon line ringing the burned shed), film-noir low-key lighting, deep shadows

Text handling: no company signage, no logos, no plate lettering, no unit numbers rendered anywhere; the identity of the building is told by the spilled textile bales alone, kept in the upper and middle bands of the frame.

Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.

MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.

Composition: ONE continuous surface (the wet asphalt factory lot) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.

NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
대구 이현동 섬유공장 화재
```

### [카드 3]
**텍스트**
```text
남은 공통점은 대구와 불, 둘뿐이었다
대구에선 지난해 화재가 1257건 났다
하루 평균 3.4건, 드문 일이 아니다
*도시와 날짜만 찍으면 대체로 맞는다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere

Scene: Emotional focal point: the flat indifference of a duty officer's eyes scanning a wall board packed with identical incident rows. A uniformed dispatch worker stands at eye level in front of a large operations wall, one hand resting on a desk edge, looking sideways at the board rather than at the viewer. The board is filled with hundreds of small repeating tick marks and row bars stacked into dense columns, one mark per call, so the eye reads volume instead of any single event. A single mark near the upper center is brighter than all the others.

Camera: medium shot, waist-up framing, face and gestures, conversational from eye-level shot, neutral perspective, realistic, balanced emotion, shot on 50mm standard lens, minimal distortion, natural cinematic composition

Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood

Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the one brighter tick mark among hundreds), muted daylight contrast

Text handling: the wall board carries only abstract tick marks and bar rows — no numerals, no headers, no station names, no readable labels of any kind; the density itself is the message and it stays in the upper two thirds of the frame.

Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.

MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.

Composition: ONE continuous surface (the operations room wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.

NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
소방 상황실 화재 통계판
```

### [카드 4]
**텍스트**
```text
19일, 한 이용자가 이런 글을 올렸다
숫자 일곱 쌍을 책 한 권에 대입해
*'부산시 대선금'이 나왔다는 것이다*
좋아요 97개, 리포스트 23개가 달렸다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere

Scene: Emotional focal point: an index fingertip pinning one spot on an open page, pressing hard enough to dent the paper. Recurring subject — a Korean adult in a plain dark long-sleeve top with short black hair, shown only as hands and forearms, the face never entering the frame — leans over a thick unmarked book lying open on the desk, the other hand hovering over a phone lit face-up beside it. Seven small handwritten coordinate pairs are lined up on a slip of paper next to the book, and a thin thread runs from that slip toward the pinned spot on the page. The book has no title, no cover art and no printed lettering anywhere; the forearm and the thread both lean toward the right edge of the frame.

Camera: medium close-up, chest-up framing, facial emotion, slight body context from high angle shot, looking down, vulnerable subject, small, observed, shot on 85mm portrait lens, flattering face, soft background separation, elegant focus, nose room on the right

Lighting/mood: cold blue screen under-glow lighting the scene from below in a dark room, restless paranoid unease

Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the single pinned spot under the fingertip), film-noir low-key lighting, deep shadows

Text handling: the book pages, the slip and the phone screen carry no legible writing — the coordinate pairs are drawn as short abstract pen strokes only, and every one of them sits in the upper half of the frame, clear of the lower portion.

Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.

MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.

Composition: ONE continuous surface (the scratched dark wooden desk) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.

NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
양장본 회고록 펼친 지면
```

### [카드 5]
**텍스트**
```text
그런데 작성자가 과정을 다 적어놨다
줄로 세다 안 맞자 글자로 바꿨다
영상은 *"억지로" 끝과 앞을 이어붙였다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere

Scene: Emotional focal point: knuckles gone white around a pen that has already scratched the same line out three times. Recurring subject — a Korean adult in a plain dark long-sleeve top with short black hair, shown only as hands and forearms, the face never entering the frame — is caught in extreme close-up over a single sheet of paper, one hand crossing out a rule written at the top and writing a different one beneath it. Layers of erased and re-written marks pile up on the same spot until the paper has worn thin and torn at the corner. A cut strip of film-like tape lies beside the sheet with its two ends forced together and buckling where they do not match.

Camera: extreme close-up, single detail, eye, lips, hand, texture from Dutch angle, tilted horizon, canted frame, unstable mood, shot on 100mm macro lens, fine detail, shallow depth of field, precise texture

Lighting/mood: harsh single overhead light pooling on the table, deep surrounding black, oppressive interrogation

Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the buckled joint where the two strip ends are forced together), film-noir low-key lighting, deep shadows

Text handling: the crossed-out rule and the rewritten one are drawn as abstract scratched-out pen strokes only — no readable words, no letters, no numerals anywhere — and the entire worn spot stays in the upper-center band of the frame.

Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.

MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.

Composition: ONE continuous surface (the sheet of worn paper) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.

NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
지운 자국 손글씨 메모지
```

### [카드 6]
**텍스트**
```text
*대입한 책은 판마다 쪽수가 다르다*
779쪽, 781쪽, 784쪽으로 갈린다
어느 판을 썼는지는 적혀 있지 않다
아무도 다시 찍어볼 수 없는 좌표다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere

Scene: Emotional focal point: the widening gap between three page edges that should have lined up and do not. Three copies of the same thick unmarked book lie side by side on the desk, each opened to what should be the same place, and the three page blocks are visibly different thicknesses so the opened spreads sit at three different depths. A ruler laid across all three touches only one of them. No hands and no person are present; the desk is the same scratched dark wooden surface as before.

Camera: medium shot, waist-up framing, face and gestures, conversational from overhead shot, bird's-eye view, top-down angle, layout, geometry, shot on 40mm lens, neutral perspective, natural human-vision feel

Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional

Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the one page edge the ruler actually touches), muted daylight contrast

Text handling: none of the three books carries a title, a cover design, a page number or any printed lettering — the mismatch is shown purely by the differing thickness of the page blocks, held in the upper and middle bands of the frame.

Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.

MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.

Composition: ONE continuous surface (the scratched dark wooden desk) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.

NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
도서 판권지 쪽수 표기
```

### [카드 7]
**텍스트**
```text
무너뜨릴 문장은 그 글 안에 다 있었다
규칙을 바꿨다고 작성자가 직접 썼다
리포스트 23개는 그 줄을 지나쳤다
*속은 게 아니라 안 읽은 것이다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere

Scene: Emotional focal point: a thumb already sliding past the one line it needed to stop on. Seen straight on at eye level in morning light, a row of hands from several different people each hold a phone at the same height, every thumb mid-swipe in the same upward direction, none of the faces in frame. On each screen the same block of writing appears as abstract grey strokes, and on every screen one strip near the top glows while the thumbs pass under it. The scene is static and centered, the hands facing the viewer rather than leading off to either side.

Camera: wide shot, full body, surrounding environment, movement, spatial context from eye-level shot, neutral perspective, realistic, balanced emotion, front-on shot, direct gaze, symmetrical composition, facing camera, shot on 35mm lens, natural documentary perspective, balanced subject and background, minimal distortion

Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy

Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the one glowing strip every thumb passes), muted daylight contrast

Text handling: all screen writing is drawn as abstract grey stroke blocks with no letters, no words and no numerals; the single glowing strip is a plain highlighted bar, and every screen sits in the upper two thirds of the frame.

Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.

MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.

Composition: ONE continuous surface (the plain morning-lit wall behind the hands) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.

NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
스레드 앱 리포스트 화면
```
