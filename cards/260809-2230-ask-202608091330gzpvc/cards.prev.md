# 용아맥이 아니어도 되는 이유

**[프롬프트 설계]**
- 화풍: A수채화 — 극장 좌석의 들뜬 체감과 끝나고 터진 박수라는 정서가 중심인 문화·체험 기사라 따뜻한 파스텔 톤이 맞다
- 분위기: 표를 못 잡은 조바심에서 시작해 어두운 상영관의 몰입, 젖은 손으로 친 박수까지 — 부러움이 안도로 풀리는 온도
- 연출 방향: 이 기사에서 독자가 멈추는 자리는 '10만원'이라는 숫자와 '나는 못 보는 건가'라는 내려앉음이다. 그래서 카드 전체가 스크린 자체를 크게 그리지 않는다 — 매진된 좌석표, 손에 쥔 휴대폰 화면, 물방울 맺힌 팔걸이, 어둠 속 박수 치는 손처럼 관객 쪽 신체와 사물에 강조점을 둔다. 스크린 반사광이 유일한 광원이 되어 얼굴을 아래에서 비추는 극장 특유의 빛을 카드마다 이어받고, 악센트는 상영관 좌석 안내등의 네온그린으로 잡아 '어느 좌석이냐'는 이 기사의 질문을 색으로 반복한다
- 독자 동선: **발단** 카드1(용아맥 매진·암표) → **전개** 카드2~3(놀란이 172분 전편을 IMAX 70mm로 찍었다·IMAX 매출 22%) → **피크** 카드4(그런데 외신이 다른 좌석을 가리켰다·멀미로 나간 기자) → **해소** 카드5(물세례 맞은 4DX 좌석에서 박수가 터졌다) → **시사점** 카드6 · 훅=카드1 끝(질문형 1회 "그럼 못 보는 건가") + 카드3 끝(단서형 "그런데 평단은 다른 좌석을 말했다") · 착지 한 줄 요지 = 극장이 스트리밍에 안 내준 것은 해상도가 아니라 같이 흔들린 세 시간이었다
- 연속성 앵커: Recurring subject — a Korean woman in her 30s with shoulder-length dark hair tied back loosely, wearing a beige knit cardigan over a white tee / 반복 장소 — a dark Korean multiplex auditorium, rows of wide reclining seats, screen glow as the only light source

### [카드 1]
**텍스트**
```text
600석이 3주치 먼저 팔렸다
중고거래 앱에 뜬 그 좌석은
*장당 10만원대였다*
그럼 나는 못 보는 건가
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: her thumb frozen mid-scroll above the phone, lips slightly parted. Recurring subject — a Korean woman in her 30s with shoulder-length dark hair tied back loosely, wearing a beige knit cardigan over a white tee, sits alone on a bench outside a cinema entrance holding a phone in both hands. She looks down at the phone screen where a seat map glows almost entirely filled, her gaze pulled toward the lower right of the screen. Behind her a tall glass wall of the multiplex lobby reflects a queue of blurred moviegoers.
Camera: MS from Eye-level, three-quarter angle, shot on 50mm standard lens
Lighting/mood: cold blue screen under-glow lighting the face from below, overcast diffused daylight through the lobby glass, restless unease
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the seat-map dots on the phone screen), muted daylight contrast
Render no readable text anywhere; the seat map reads as abstract dots and blocks only. Keep her hands and the phone in the upper-center area of the frame.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the cinema lobby floor and glass wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
CGV 용산 아이맥스 예매 좌석배치도
```

### [카드 2]
**텍스트**
```text
표가 몰린 이유는 분명했다
놀란이 러닝타임 172분을
*전부 IMAX 70mm로 찍었다*
2008년 27분에서 18년 만이다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: two gloved hands cradling a heavy film magazine as if it were fragile. A film technician in a gray work coat stands at a projection-room table, both hands lifting a wide reel of large-format film, eyes fixed down on the loop of film between his fingers. A tall metal projector bulks in the background, its small port window throwing a hard beam past his shoulder. Coils of film rest on the table beside him.
Camera: MCU from High angle, shot on 100mm macro lens
Lighting/mood: warm soft desk-lamp light on the film, deep shadow behind the projector, quiet reverence
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on a small indicator lamp on the projector body), film-noir low-key lighting, deep shadows
No labels, no printed markings, no numbers on the film canisters or projector; render surfaces bare. Keep hands and film in the upper-center area.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the projection-room table top) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
IMAX 70mm 필름 영사기 릴
```

### [카드 3]
**텍스트**
```text
감독은 관객이 갑판에 함께
서 있게 하려 했다고 말했다
개봉 2주차까지 IMAX 상영만으로
*전체 매출의 22%가 나왔다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the narrow gap between a lone standing viewer and the enormous screen wall in front of him. A man stands at the foot of a vast cinema screen inside a dark auditorium, tilting his head far back, both arms hanging loose at his sides, looking straight up at the towering bright surface. Rows of empty wide reclining seats sweep away behind him toward the back wall.
Camera: EWS from Worm's-eye view, shot on 16mm wide lens
Lighting/mood: divine volumetric shafts of projector haze descending over the seats, deep surrounding blackness, awed hush
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the aisle step lights running down the seat rows), film-noir low-key lighting, deep shadows
The screen surface is pure abstract light and haze, no image and no text on it. Keep the standing figure and the screen edge in the upper-center area.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the sloped auditorium floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
아이맥스 상영관 스크린 좌석 내부
```

### [카드 4]
**텍스트**
```text
그런데 외신 평단은
다른 좌석을 가리켰다
IMAX보다 4DX가 낫다고 썼다
*한 기자는 멀미로 나갔다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: one hand pressed flat against his own mouth, the other gripping the seat back for balance. A man in his 40s in a rumpled dark shirt rises from a tilted motion seat mid-row, turning his shoulders toward the aisle on the right, eyes squeezed shut and brow drawn tight. His seat is still canted back at an angle behind him, and two seated silhouettes on either side stay fixed forward without turning.
Camera: MS from Dutch angle, over-the-shoulder framing, shot on 35mm lens
Lighting/mood: flickering cold screen glow raking across the row from the front, deep unlit rows behind, queasy instability
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the floor-level aisle guide strip), film-noir low-key lighting, deep shadows
Nose room on the right, his body vector directed toward the right edge of the frame. Keep his face and hands in the upper-center area.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the auditorium seat row and aisle floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
4DX 모션 시트 상영관
```

### [카드 5]
**텍스트**
```text
4DX판은 연출팀이 15일간
본편을 열 번 가까이 돌려봤다
바다와 젖은 흙, 타는 고무 향에
렌즈에 물 튀는 순간마다 분사다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: fine water droplets caught in the air just above her wet eyelashes, the instant before they land. Recurring subject — a Korean woman in her 30s with shoulder-length dark hair tied back loosely, wearing a beige knit cardigan over a white tee, sits pressed back into a tilted motion seat in a dark Korean multiplex auditorium, both hands clamped on the wet armrest, chin lifted toward the screen off-frame above. A folded blanket has slid to her lap and a capped drink leans in the cup holder beside her hand.
Camera: CU from Eye-level, profile angle, shot on 85mm portrait lens
Lighting/mood: single hard side-light of screen reflection cutting across her wet face, deep chiaroscuro shadows, breathless tension
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the tiny water-off button glowing on the armrest), film-noir low-key lighting, deep shadows
No text on the armrest button or the drink cup; render both bare. Keep her eyes, the droplets and her gripping hands in the upper-center area.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the motion seat back and armrest) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
4DX 물 분사 관객 담요
```

### [카드 6]
**텍스트**
```text
용산에서 4DX표를 잡은 관객은
젖은 손으로 박수를 쳤다
세계 최대 스크린이 아니어도
*끝나고 객석에서 박수가 터졌다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: dozens of wet hands lifted and clapping in the dark, water still beading on wrists. Recurring subject — a Korean woman in her 30s with shoulder-length dark hair tied back loosely, wearing a beige knit cardigan over a white tee, stands among the rows clapping with her damp hands raised, looking straight ahead at the camera with a spent, glowing smile. Around and behind her a full house of moviegoers rise from tilted seats clapping in the same direction, the blanket forgotten across her seat.
Camera: WS from Eye-level, front-on shot, shot on 35mm lens
Lighting/mood: warm candle-soft house lights coming up over the rows, faint screen afterglow, released tenderness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the exit guide lamps along the wall), muted daylight contrast
No signage text, no letters on the exit lamps or walls; render them as plain glowing shapes. Keep the clapping hands and faces in the upper-center area.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the auditorium seating tier floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
극장 객석 관객 박수 어둠
```

### [카드 7]
**텍스트**
```text
극장이 스트리밍에 안 내준 건
해상도가 아니었던 셈이다
같은 세 시간을 옆자리와 함께
*흔들리고 젖은 시간이 남았다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: two neighboring seat cushions still dark with water, dented in the shape of the people who just left. An empty row of tilted motion seats holds a forgotten folded blanket draped over one armrest and a capped paper cup left in the holder, with faint wet footprints leading away toward the aisle. No people remain in the frame; the house lights are up on the abandoned row.
Camera: MS from Bird's-eye view, shot on 40mm lens
Lighting/mood: warm faded house light with a soft golden haze over the damp fabric, gently wistful afterglow
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the row-number lamp at the end of the armrest), muted daylight contrast
No numbers, no letters, no printed brand marks on the cup, blanket or seats; the row lamp is a bare glowing dot. Keep the two wet cushions and the blanket in the upper-center area.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the seat row upholstery and floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
빈 상영관 좌석 담요 컵홀더
```
