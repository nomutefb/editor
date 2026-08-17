# 보름을 돌아 다 세었는데, 그게 전체의 30%다

**[프롬프트 설계]**
- 화풍: B 극화 — 인물 대결이 아니라 배분과 산술이 본선이라, 무거운 선과 명암으로 숫자의 무게를 세운다
- 분위기: 개표가 끝났는데도 끝나지 않은 저녁. 환호 대신 정적, 확정 대신 유보. 화면은 밝은데 그 앞이 조용한 긴장
- 연출 방향: 뉴스를 안 보던 독자가 멈추는 지점은 두 개다 — 31만 표가 갈린 거리가 1207표라는 낙차, 그리고 보름을 다 세었는데 그게 셋 중 한 칸이라는 헛헛함. 그래서 두 후보의 얼굴이 아니라 *숫자가 뜬 화면·아직 열리지 않은 함·봉인된 봉투*에 카메라를 건다. 사람은 올려다보는 눈과 멈춘 손끝으로만 등장하고, 주인공은 언제나 '채워진 칸과 비어 있는 칸'. 어느 후보 쪽으로도 기울지 않는 대신 배분 구조 자체가 화면의 주어가 된다
- 독자 동선: **발단** 카드2→**전개** 카드2~3→**피크** 카드4→**해소** 카드5→**시사점** 카드6 · 훅=카드1 끝(단서형 — 1207표라는 수치만 던지고 정체는 카드2 첫 줄이 회수)+카드3 끝(예고형 — 과반이 깨졌다로 끊고 카드4가 '그런데'로 회수) · 착지 한 줄 요지=오늘 세지 않은 표가 내일 처음 열린다(카드1은 제시용 도입, 발단은 카드2)
- 연속성 앵커: (없음 — 반복 주인공 없이 사물·공간이 주체) · 반복 장소: Recurring location — the same large indoor convention hall in Goyang with dark ceiling trusses and one huge results screen on the wall (카드1, 카드2)

### [카드 1]
**텍스트**
```text
8월 16일 저녁, 고양 킨텍스에서
민주당 당대표 순회경선의
마지막 개표 결과가 발표됐다
*31만 표가 갈린 거리는 1207표*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the upturned faces of the front row, eyes fixed on the screen without blinking. Recurring location - the same large indoor convention hall in Goyang with dark ceiling trusses and one huge results screen on the wall. About twenty Korean adults stand with their backs to the viewer, heads tilted up toward the screen mounted high on the hall wall, arms hanging at their sides, nobody moving. The screen displays two long horizontal bars of almost identical length lying side by side above a plain scale, and the bars are the only thing bright in the room.
Camera: wide shot from a low angle, shot on 24mm wide lens
Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by the two bars on the screen, muted daylight contrast
Korean default: Korean adult figures and Korean convention-hall interior conventions, generic faces, no resemblance to any real public figure, no party logo, no emblem, no organization name anywhere.
Text handling: the screen shows plain graphic bars only, with no numbers, no letters and no readable characters anywhere in the frame; keep the screen and the upturned faces in the upper half, well clear of the lower 40 percent of the canvas.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the dark convention hall wall carrying the large results screen) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no meaningless letters, no random characters, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
민주당 전당대회 합동연설회 킨텍스
```

### [카드 2]
**텍스트**
```text
*김민석 46.66%, 정청래 46.28%*
서울 597표, 경기 610표 차였다
8월 1일 충청에서 시작한 순회경선이
서울·경기를 끝으로 문을 닫았다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: one man's eyes flicking back and forth between the two bars, unable to tell which one is longer. Recurring location - the same large indoor convention hall in Goyang with dark ceiling trusses and one huge results screen on the wall. Four Korean party members in their forties and fifties stand waist-up in front of the glowing screen, one of them raising a hand halfway toward the display and stopping in mid-air. The screen wall rises directly behind them and its light washes up over their faces from below.
Camera: medium shot from eye level, shot on 50mm standard lens
Lighting/mood: cold blue screen under-glow lighting the faces from below in a dark room, restless paranoid unease
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the two near-identical bars, film-noir low-key lighting, deep shadows
Korean default: Korean adult figures and Korean convention-hall interior conventions, generic faces, no resemblance to any real public figure, no party logo, no emblem, no organization name anywhere.
Text handling: the screen carries plain graphic bars only, with no numbers, no letters and no readable characters; keep the faces and the raised hand in the upper half, clear of the lower 40 percent of the canvas.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the same glowing results screen wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no meaningless letters, no random characters, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
민주당 당대표 경선 개표 결과 발표
```

### [카드 3]
**텍스트**
```text
8월 15일 호남은 달랐다
김 후보가 57.54%로 크게 앞섰다
*그때 누계 52.21%, 지금은 49.91%*
서울·경기를 지나며 과반이 깨졌다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a hand still pressed flat against the last sheet, fingers not yet lifting away. A Korean staff member in a dark jacket, framed from the chest up, has just fixed a final tally sheet onto a corridor wall where a row of earlier regional sheets already hangs. On the earlier sheets two bars sit far apart; on the newest one they are almost level. He looks sideways at the new sheet instead of at his own hand, and the corridor wall runs unbroken behind him.
Camera: medium close-up from a Dutch tilt angle, shot on 85mm portrait lens
Lighting/mood: cold blue dim interior light, heavy and suffocating, faint trembling tension
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the bars of the newest sheet, film-noir low-key lighting, deep shadows
Korean default: Korean adult figure and Korean office-corridor conventions, generic face, no resemblance to any real public figure, no party logo, no emblem, no organization name anywhere.
Text handling: every sheet is cropped at the frame edge and softly blurred so that only the bar shapes read and no characters are legible; keep the hand and the newest sheet in the upper half, clear of the lower 40 percent of the canvas.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the corridor wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no meaningless letters, no random characters, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
민주당 순회경선 호남 권리당원 투표
```

### [카드 4]
**텍스트**
```text
*그런데 이 보름이 정한 건 30%다*
당대표 선출은 대의원 40%,
권리당원 30%, 여론조사 30%다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a bare hand resting on the rim of the one open box, knuckles tense, going no further. The frame closes tight on a single opened ballot box crammed with folded paper slips, struck by one hard pool of light from directly above. Behind it two more identical boxes sit sealed and unopened, sinking into black. The hand belongs to someone outside the frame who lifts nothing out, and all three boxes rest on one long dark table.
Camera: tight close-up from a high angle, shot on 100mm macro lens
Lighting/mood: single pool of hard light isolating the subject in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) grazing the edge of the open box, film-noir low-key lighting, deep shadows
Korean default: Korean hand and Korean polling-equipment conventions, no party logo, no emblem, no organization name anywhere.
Text handling: the folded slips and the boxes are completely blank with no printed characters visible; keep the open box and the resting hand in the upper-center, clear of the lower 40 percent of the canvas.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the long dark table top) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no meaningless letters, no random characters, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
민주당 권리당원 투표함
```

### [카드 5]
**텍스트**
```text
대의원 40%는 가장 큰 덩어리인데
이 숫자에 한 번도 들어가지 않았다
국민여론조사 30%는 14일에 시작해
*이미 끝났고, 결과만 봉인돼 있다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the taped seal running across the envelope, untouched and perfectly flat. A large sealed document envelope lies alone on a desk in the upper-center of the frame, with an empty chair pushed back beside it. A Korean man in a dark suit stands with his back to the viewer at the lower left edge, only his shoulders and the back of his head entering the frame, looking down at the envelope with both hands hanging empty at his sides. The dim office wall runs unbroken behind the desk.
Camera: medium shot from eye level with the figure seen from behind, shot on 70mm short telephoto
Lighting/mood: single hard side-light cutting across the subject, deep chiaroscuro shadows, tense atmosphere
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the sealing tape, film-noir low-key lighting, deep shadows
Korean default: Korean adult figure and Korean office interior conventions, generic build, no resemblance to any real public figure, no party logo, no emblem, no organization name anywhere.
Text handling: the envelope and every paper in the room are blank with no printed characters visible; keep the sealed envelope and the desk in the upper-center, clear of the lower 40 percent of the canvas.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the dim office wall behind the desk) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no meaningless letters, no random characters, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
민주당 중앙당선거관리위원회 국민여론조사
```

### [카드 6]
**텍스트**
```text
8월 17일 대전에서 결과가 나온다
보름간 센 표는 셋 중 한 칸을 채웠고
나머지 두 칸은 아직 열리지 않았다
*오늘 세지 않은 표가 내일 처음 열린다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the empty podium standing dead center, its microphone still folded down. Seen from directly overhead, a vast convention hall floor holds hundreds of empty chairs in perfect rows around a small central stage placed in the upper-center of the frame. One podium and one covered table sit at the middle of that stage, and a single narrow band of pale light falls across the floor from a door left ajar at the edge. Not one person is present anywhere in the hall.
Camera: extreme long shot from a bird's-eye view, shot on 14mm ultra-wide lens
Lighting/mood: cold blue pre-dawn tone, desolate stillness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the narrow band of light crossing the floor, film-noir low-key lighting, deep shadows
Korean default: Korean convention-center interior conventions, no party logo, no emblem, no organization name, no banner text anywhere.
Text handling: the podium, the covered table and every surface are blank with no printed characters visible; keep the central stage and podium in the upper-center, clear of the lower 40 percent of the canvas.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the convention hall floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no meaningless letters, no random characters, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
대전컨벤션센터 민주당 전국당원대회
```
