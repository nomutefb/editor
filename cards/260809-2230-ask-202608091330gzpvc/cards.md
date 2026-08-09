# 용아맥 10만원 암표 앞에서, 외신은 다른 좌석을 가리켰다

**[프롬프트 설계]**
- 화풍: A 한국 웹툰 수채화 — 범죄·권력이 아니라 '극장에 앉은 사람의 마음'이 사건이라, 파스텔 번짐이 관객 표정을 가장 부드럽게 받는다
- 분위기: 들뜬 기대가 매진 화면 앞에서 한 번 꺾였다가, 젖은 객석의 박수로 되살아나는 온도 곡선. 차가운 화면빛 → 따뜻한 객석빛으로 넘어간다
- 연출 방향: 독자훅 = '나는 그 좌석을 못 잡았다'는 조바심(표 못 구한 관객이 멈추는 자리). 전하려는 것 = 이 영화의 최고 순간이 화면 크기에만 있지 않았다는 것. 그래서 강조점은 스크린이 아니라 **좌석과 사람의 얼굴**에 쏠린다 — 매진된 좌석 배치도를 올려다보는 눈, 물방울 맺힌 팔걸이를 쥔 손, 상영이 끝나고 젖은 채 마주친 웃음. 상영관 자체는 늘 뒤에 두고, 앞에는 그 좌석에 앉은 사람을 둔다. thumb_dispatch의 차가운 화면 언더글로(LGT11)를 피크 카드 조명 톤으로 계승하고, 거리감은 뒤로 갈수록 좁혔다가 마지막에 다시 벌린다
- 독자 동선: **발단** 카드1→**전개** 카드2→**피크** 카드3→**해소** 카드4~5→**시사점** 카드6 · 훅=카드1 끝(예고형 "이유가 있었다"→카드2 즉시 회수)+카드2 끝(단서형 수치 22%→카드3 회수) · 착지 한 줄 요지 = 3주 매진 앞에서 남은 건 화질이 아니었다(감독이 판 화면 ↔ 관객이 산 함께 흔들린 시간의 양가 병치)
- 연속성 앵커: Recurring subject — a Korean woman in her 30s with shoulder-length hair tied back, wearing a light beige cardigan over a white tee (카드 1·3·5·6 등장) / 반복 장소 = a large multiplex auditorium with tiered seating

### [카드 1]
**텍스트**
```text
8월 5일 놀란의 오디세이가 열렸다
개봉일 예매만 56만7000명이었다
열기는 600석 용산 아이맥스로 몰렸다
*그 상영관이어야 하는 이유가 있었다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: her lifted chin and the bright widening of her eyes as she looks up at the seating board. Recurring subject — a Korean woman in her 30s with shoulder-length hair tied back, wearing a light beige cardigan over a white tee — stands in a crowded cinema lobby, holding her phone up in both hands, her gaze angled up and toward the right edge of the frame. Behind and beside her, about a dozen moviegoers queue in the same direction on one continuous polished lobby floor. The overhead board shows only an abstract grid of seat pictograms, no letters at all. Nose room on the right, gaze directed toward the right edge.
Camera: wide establishing shot from eye-level, shot on 35mm lens
Lighting/mood: bright high-key light, clean white ambience, minimal shadow, hopeful and open
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast, the accent kept as one soft point inside the pastel palette
Text handling: avoid all incidental lettering by framing and pictograms only; the seat board is a grid of small squares, signage is cropped out of frame.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the polished lobby floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, no brand logos, no company marks; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
CGV 용산아이파크몰 아이맥스 로비
```

### [카드 2]
**텍스트**
```text
*놀란은 172분 전부를 필름에 담았다*
아이맥스 70mm 카메라로만 찍었다
다크 나이트 27분에서 18년 만이다
2주 만에 전체 매출의 22%가 나왔다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the director's narrowed eyes locked on the far horizon while his palm steadies the camera body. A generic middle-aged film director in a windbreaker crouches beside an enormous boxy film camera mounted low on a ship's deck, four crew members bracing the rig and the cables around him. All of them face the open sea at the right edge of the frame, spray coming over the gunwale onto the boards. The huge camera is the one object every hand in the scene is touching. Nose room on the right, gaze directed toward the right edge.
Camera: medium shot from a low angle, shot on 50mm lens
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast, the accent kept as one soft point inside the pastel palette
Text handling: the camera body and equipment cases carry no markings; any label surface is turned away from the lens.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the ship's wet wooden deck) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, no brand logos, no equipment badges; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
아이맥스 70mm 필름 카메라 촬영
```

### [카드 3]
**텍스트**
```text
표는 3주치가 이미 다 팔렸다
장당 10만원, 북미에선 1000달러다
*못 구한 사람은 그대로 밀려났다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: her eyes glistening with welling tears, not yet falling, and the slow drop of her mouth corners. Recurring subject — a Korean woman in her 30s with shoulder-length hair tied back, wearing a light beige cardigan over a white tee — stands alone in a dim corridor, holding her phone close to her chest with both thumbs stilled, looking straight down into the screen. The phone is the only light source and the only object she touches, its glow washing up her jaw. The screen shows nothing but a dense grid of small filled squares, no letters. Her shoulders pull inward, making her smaller.
Camera: tight close-up from eye-level, shot on 85mm portrait lens
Lighting/mood: cold blue screen under-glow lighting the face from below in a dark room, restless paranoid unease
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows, the accent kept as one soft point inside the pastel palette
Text handling: the phone screen is rendered as filled square pictograms only, tilted away from the lens so no writing is legible.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the dark auditorium corridor wall behind her) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, no app interface labels; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
영화 예매 매진 좌석표
```

### [카드 4]
**텍스트**
```text
*그런데 외신은 다른 좌석을 가리켰다*
미국 슬레이트는 4DX가 낫다고 썼다
설계팀은 본편을 열 번 돌려봤다
향은 바다와 젖은 흙, 타는 고무다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the knot between his brows and the way his fingers grip the armrest as he studies the screen. A Korean man in his 30s in a black staff jacket sits alone in the middle of an otherwise empty motion-seat auditorium, an open blank notebook on his knee, looking forward and slightly up. Two rows ahead of him a Western woman journalist sits sideways with a small notepad, also facing the screen, kept lower and softer so the staff member stays the focus. The empty tilting seats spread away from them in even rows, nozzles glinting on the seatbacks.
Camera: wide shot from a high angle, shot on 24mm lens
Lighting/mood: single pool of hard light isolating the figure in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows, the accent kept as one soft point inside the pastel palette
Text handling: the notebook and notepad pages are blank and angled away; seat numbers and wall signage are cropped out of frame.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the sloped rows of theater seats) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, no seat number decals, no brand logos; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
CGV 4DX 상영관 좌석
```

### [카드 5]
**텍스트**
```text
물은 후룸라이드급으로 쏟아진다
담요를 챙기라는 안내가 붙었다
멀미로 도중에 나간 기자도 있었다
*그런데 불이 켜지자 박수가 터졌다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: her wet eyelashes and the surprised laugh breaking across her soaked face as she claps. Recurring subject — a Korean woman in her 30s with shoulder-length hair tied back, wearing a light beige cardigan over a white tee, now drenched — sits in a front row clapping hard, a folded blanket slipping off her lap. Ten or so soaked moviegoers around her clap in the same direction, water droplets still hanging in the air above them. Far behind, one person walks up the aisle toward the exit with a hand over the mouth, small and low-contrast.
Camera: group shot from a low angle, shot on 40mm lens
Lighting/mood: soft wraparound key light bouncing off the screen, gentle falloff, tender warm intimacy
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows, the accent kept as one soft point inside the pastel palette
Text handling: no signage, no seat markings; every printed surface is cropped or turned away.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the tiered rows of theater seating) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, no brand logos; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
4DX 물 분사 관객
```

### [카드 6]
**텍스트**
```text
같은 영화가 두 좌석에서 갈렸다
한쪽은 감독이 설계한 화면을 팔았고
다른 쪽은 함께 흔들린 시간을 팔았다
*매진 앞에서 남은 건 화질이 아니었다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: her fingertips still worrying the damp cuff of her cardigan, her eyes calm and turned straight toward the viewer. Recurring subject — a Korean woman in her 30s with shoulder-length hair tied back, wearing a light beige cardigan over a white tee, hair still damp — stands alone in the center aisle of an emptied auditorium, facing the camera in a centered static composition, not yet leaving. On both sides the rows of seats hold wet cushions and two abandoned blankets, house lights just raised. The damp blanket nearest her is the single object tying her to the seat she sat in.
Camera: wide shot from eye-level, shot on 50mm lens
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast, the accent kept as one soft point inside the pastel palette
Text handling: exit markers and seat numbers are cropped out of frame; no printed surface faces the lens.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the theater floor and its rows of seats) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, no exit signs, no brand logos; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
상영 종료 극장 빈 객석
```
