# 🤖 중국 AI에 올린 청두 CCTV 영상, 실제로 읽은 건 미국 클로드였다

**[프롬프트 설계]**
- 화풍: B 한국웹툰 극화 — 감시·국가 연계 데이터·기업 간 무단 복제라는 구조 고발 결이라 수채화의 온기가 맞지 않고, 잉크 선과 스크린톤이 관제실·서버홀·키보드의 차가운 질감을 견딘다
- 분위기: 화면 불빛만 남은 방의 정적 — 누가 시켜서가 아니라 스스로 넣은 자료가 어디로 갔는지 모르는 서늘함. 폭로의 흥분이 아니라 '나도 저랬을 수 있다'는 체감
- 연출 방향: 서사 = **역추적**. 카드1은 '들어와 있으면 안 되는 자료가 클로드 서버에 있다'는 의문으로 열고(질문형 훅 1회), 카드2가 경로를 되짚어 문샷의 몰래 호출을 찾고, 카드3이 이유(증류)와 규모, 카드4가 중국만이 아닌 러시아까지, 카드5가 반박과 침묵, 카드6이 '제 나라 AI가 스파이가 된 셈'으로 닫는다. 그래서 얼굴 대신 등·손·화면 테두리·케이블 같은 '자료가 지나간 경로'를 그리고, 네온그린 1색은 매 카드에서 그 경로가 열린 지점(확대된 화면·슬롯의 LED·케이블·커서·발신 램프)에만 앉힌다. 마지막은 태평양으로 들어가는 해저케이블 정면. thumb_dispatch의 스크린 언더글로 톤과 감시당함 정조를 전 카드 키노트로 잇되 앵글은 카드마다 분산
- 독자 동선: **단일 관점 = 중국 AI가 제 나라 사용자를 속였고, 그 길로 자국 자료가 미국 서버로 갔다(역추적으로 드러남)** · **발단** 카드1(들어온 자료·의문)→**전개** 카드2(되짚은 경로 = 문샷)~3(이유 = 증류·규모)→**피크** 카드4(러시아 국방 DB까지)→**해소** 카드5(반박·침묵·미 정보기관 지목)→**시사점** 카드6 · 훅=카드1 끝(질문형 — 어떻게 들어온 걸까)+카드3 끝(예고형 — 중국 것만이 아니었다) · 착지 = 제 나라 AI가 스파이가 된 셈이고 가장 중요한 자료가 태평양을 건넜다
- 연속성 앵커: (없음) / 반복 장소 (없음)

### [카드 1]
**텍스트**
```text
클로드 서버에 중국 내부 자료가 들어왔다
청두 CCTV 영상, 국유기업 소스코드까지
중국이 밖으로 내보낼 리 없는 것들이었다
*이 자료는 어떻게 들어온 걸까*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the stiff back of an engineer's neck as he leans toward a wall of monitors, his hand frozen on the mouse. One young engineer in a plain grey hoodie sits alone at a long desk in a dim server operations room, seen from behind, facing a grid of dozens of screens; most show blank grey log panes, but one enlarged feed on the far right shows a rainy Chinese city street with a tall CCTV pole and no people. His gaze runs to that enlarged feed at the right edge of the frame, with nose room on the right and gaze directed toward the right edge. Only that feed carries a thin neon green frame; everything else is grey.
Camera: wide shot, full body, surrounding environment, spatial context, from eye-level with neutral realistic perspective, back shot rear view, shot on 24mm wide lens with cinematic wide shot and spatial context
Lighting/mood: flat cold even surveillance light, no shadow no warmth, detached and watchful
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Text handling: the feeds show only streets and buildings, no timestamps, no camera labels, no on-screen characters; the desk carries no papers or signage.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the operations-room floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Anthropic threat report Chengdu CCTV Kimi
```

### [카드 2]
**텍스트**
```text
앤트로픽이 경로를 되짚자 답이 나왔다
키미를 만든 문샷이 키미 사용자 몰래
요청을 클로드로 보내고 있었다
*키미에 넣은 자료가 그대로 미국으로 갔다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: two hands feeding a thick stack of printed chat transcripts into a narrow slot in a black server cabinet, the operators' faces left in darkness with only the paper lit. Two operators in dark hoodies sit at a long console in a dark operations room, one holding the stack and the other steadying it as it slides into the slot, both gazes fixed down on the slot. The sheets are blurred and blank, and the slot glows with a single neon green status light that spills over their knuckles. Behind them a wall of rack monitors sits dim and out of focus.
Camera: medium shot, waist-up framing, face and gestures, from a high angle looking down with the subjects small and observed, three-quarter angle with natural face depth, shot on 50mm standard lens with minimal distortion and natural cinematic composition
Lighting/mood: cold blue screen under-glow lighting the face from below in a dark room, restless paranoid unease
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows
Text handling: the printed sheets carry no legible characters, only soft blurred grey lines; the cabinet has no logo, no labels, no lettering.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the long console desk) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Moonshot Kimi Claude rerouting Anthropic
```

### [카드 3]
**텍스트**
```text
이유는 하나, 남의 AI 답을 긁어다
제 AI를 가르치는 '증류' 때문이었다
*중국 연구소 7곳이 2억 건을 가져갔다*
그런데 새어 나간 건 중국 것만이 아니었다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the upturned face of a lone technician, eyebrows raised and eyes wide, as the back panel he has just pried off a towering sleek consumer AI terminal swings open above him. One Chinese technician in a grey work jacket crouches at the base of a tall matte-black consumer AI kiosk in an empty showroom, one hand still on the loosened panel, his gaze climbing toward the upper right edge of the frame with nose room on the right. Behind the opened panel a thick bundle of cables runs up and out of the top of the frame into darkness, and a single neon green light pulses along that bundle like a vein; the kiosk's smooth front face stays blank and dark.
Camera: wide shot, full body, surrounding environment, spatial context, from a ground-level worm's-eye view near the floor with exaggerated scale, shot on 14mm ultra-wide lens with vast environment, dramatic depth and strong spatial presence
Lighting/mood: single hard side-light cutting across the subject, deep chiaroscuro shadows, tense atmosphere
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows
Text handling: the kiosk carries no logo, no brand name, no screen text; the front panel is a blank dark surface; cables carry no printed markings.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the showroom floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Moonshot Kimi DeepSeek app Claude Anthropic
```

### [카드 4]
**텍스트**
```text
*러시아 국방부 연계 DB의 접속 자격증명이*
딥시크를 거쳐 미국 서버로 건너갔다
공안 사건관리 시스템 작업도 흘러갔다
입력한 사람들은 그 사실을 몰랐다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a single fingertip pressing the enter key, the nail bed blanched white with pressure. One hand of an unseen IT operator rests on a dark keyboard on an office desk, seen from directly above and cropped tight, with a lanyard access card lying face-down beside the keyboard and the lower edge of a monitor glowing faintly at the top of the frame. The gaze of the scene is the hand itself; no face is visible. A thin neon green cursor glow catches the edge of the pressed key, and everything beyond the pool of light falls into black.
Camera: extreme close-up, single detail, hand, texture, from a high angle looking straight down, shot on 100mm macro lens with fine detail, shallow depth of field and precise texture
Lighting/mood: single pool of hard light isolating the figure in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows
Text handling: keycaps are out of focus with no legible characters, the access card shows only its blank back, the monitor edge shows no readable content.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the office desk top) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
DeepSeek Anthropic distillation credentials leak
```

### [카드 5]
**텍스트**
```text
중국 정부는 미국이 이를 정치화한다며
근거 없는 주장이라고 반박했다
정작 문샷과 딥시크는 답이 없었고
*미 정보기관 3곳은 이미 이들을 지목했다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the tightly controlled face of a spokesperson in profile, jaw set and lips pressed, fighting back a visible emotion. One Chinese man in his 50s in a dark suit stands at a plain briefing-room podium, one palm flat on the lectern, looking straight ahead toward the left side of the frame at an unseen press corps. In the foreground at the frame's edge, out of focus, a few microphone heads on a stand point up at him. A small neon green on-air lamp on the podium's edge is the only colour in the room; the backdrop is a bare grey wall.
Camera: medium shot, waist-up framing, face and gestures, from eye-level with neutral perspective and balanced emotion, profile shot side view with clear silhouette, shot on 70mm short telephoto with gentle background compression and subject isolation
Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Text handling: the backdrop carries no emblem, no flag, no lettering; the podium front is plain; microphones carry no station logos.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the bare grey briefing-room wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
China Ministry of Commerce spokesperson distillation briefing
```

### [카드 6]
**텍스트**
```text
중국 연구소가 미국 AI를 몰래 쓰는 사이
자국의 국방과 치안이 미국으로 간 셈이다
제 나라 AI가 스파이가 된 셈이고
*가장 중요한 자료가 태평양을 건넜다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a single armoured fibre-optic cable emerging from wet sand and running straight away from the viewer into the dark surf, tiny against the whole Pacific. An empty cable-landing beach at pre-dawn, seen head-on and dead centre, with no people anywhere; a small concrete landing hut stands at the left with one neon green indicator lamp glowing on its wall. The cable is the only line in the frame and it leads the eye from the bottom centre straight out to the flat black horizon.
Camera: extreme long shot, tiny subject, vast environment, scale, isolation, from a front-on eye-level angle with symmetrical composition facing camera, shot on 24mm wide lens with cinematic wide shot and spatial context
Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground, desolate stillness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), film-noir low-key lighting, deep shadows
Text handling: the hut carries no signage, no warning plate, no lettering; the cable has no printed markings.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the wet sand running into the surf) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Pacific submarine cable landing station beach
```
