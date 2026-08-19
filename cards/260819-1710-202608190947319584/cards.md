# 그늘의 3분의 2는 우연이었다

**[프롬프트 설계]**
- 화풍: B 극화 — 감정 사건이 아니라 도시 구조 고발이라, 하드라인·고대비가 빛과 그림자의 경계선 자체를 증거처럼 세운다
- 분위기: 한낮 땡볕의 무정함과, 그것을 처음 다 재본 자료의 냉정함이 겹친 톤. 사람은 적고 바닥과 그림자가 말한다
- 연출 방향: 독자훅은 "지하철역에서 집까지 걷던 그 5분에 그늘이 있고 없고가 그동안 운이었다"는 서늘함이다. 그래서 매 카드가 잡는 강조점은 사람의 표정이 아니라 **바닥에 그어진 그림자의 경계선** — 그 선이 어디서 끊기는지, 누가 그었는지, 왜 동네마다 다른지를 순서대로 보여 준다. thumb_dispatch에서 이어받는 것은 사람 없는 정물의 거리감과 무채색 무게(SG-09·LGT08 정조)이며, 여기에 한낮 직사광의 하드라이트를 얹어 '뜨거운데 아무도 책임지지 않는 표면'을 만든다. 악센트 #0FFD02는 매 카드에서 **그늘 쪽에만** 걸어, 초록이 닿은 자리와 닿지 않은 자리를 독자가 눈으로 세게 한다
- 독자 동선: **발단** 카드1 → **전개** 카드2~3 → **피크** 카드4 → **해소** 카드5 → **시사점** 카드6~7 · 훅=카드1 끝(질문형 1회: "그늘은 대체 누가 만들어 온 걸까")+카드2 끝(단서형: 15.2%포인트라는 수치를 던지고 카드3이 즉시 회수) · 착지 한 줄 요지 = 그늘이 도시 구조 문제라는 건 시가 인정했고, 남은 건 그 구조를 바꾸는 값이며 그게 정해져야 이름이 권리가 된다
- 연속성 앵커: 반복 인물 (없음) / 반복 장소 — `Recurring location — a wide Seoul downtown sidewalk of gray paving blocks between high-rise facades and a row of thin young street trees.`

### [카드 1]
**텍스트**
```text
한여름 서울 보도는 하루 4시간 21분
그늘 한 점 없는 땡볕에 놓인다
온열질환자 셋 중 하나가 길에서 나왔다
*그늘은 대체 누가 만들어 온 걸까*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the back of a lone walker's neck and the forearm raised to shield the eyes, both scorched by light coming straight down. Recurring location — a wide Seoul downtown sidewalk of gray paving blocks between high-rise facades and a row of thin young street trees. One office worker walks away from the viewer along the bleached pavement toward the right edge of the frame, head lowered, a jacket folded over one arm, gaze fixed on the far crossing ahead. A single thin young street tree stands beside the path and its shadow is so small it barely covers its own base. The pavement runs unbroken to the far end of the block with no shade falling anywhere on it, nose room on the right.
Camera: wide shot from eye-level, shot on 24mm wide lens
Lighting/mood: harsh overexposed midday sunlight, hard shadows, oppressive heat
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 confined to the one small patch of tree shadow on the pavement), muted daylight contrast
Korean urban context by default: Korean pedestrian signals, Korean lane markings, Korean signage shapes with no readable letters.
Text handling: avoid incidental writing entirely; signage and storefronts are resolved as blank shapes or cropped out of frame.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the sidewalk pavement) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
서울 폭염 보도 아스팔트
```

### [카드 2]
**텍스트**
```text
서울시가 보도 4031㎞를 다 쟀다
평균 그늘 비율은 44.4%였다
건물이 만든 몫이 29.2%포인트
*가로수 몫은 15.2%포인트뿐이었다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the hard straight edge where a tower's shadow ends and bare sidewalk begins. A Seoul downtown block viewed straight down from far above: long rectangular shadow blocks thrown by high-rise slabs cover most of the sidewalk strips, while the thin scattered canopies of the street trees cover only a narrow remainder along the curb. No people are legible at this height. The pavement, the shadow blocks and the tree canopies read as one continuous ground plane, and the uncovered pavement runs through the block as one bright unbroken band.
Camera: extreme long shot from a bird's-eye view, shot on 35mm lens
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 confined to the narrow tree-canopy shade along the curb), muted daylight contrast
Korean urban context by default: Korean block layout, Korean crosswalk stripes, rooftop shapes with no readable letters.
Text handling: rooftop and street signage resolved as blank geometric shapes only.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the city ground plane seen from above) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
서울 도심 항공사진 건물 그림자
```

### [카드 3]
**텍스트**
```text
*그늘을 만들려고 세운 건물은 없다*
건물 높이와 배치, 물러선 거리가
그 그늘을 우연히 정했을 뿐이다
그늘은 원래 도시 구조의 문제였다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a knife-straight shadow line falling across the paving stones, drawn by nothing but the height of the tower above it. Recurring location — a wide Seoul downtown sidewalk of gray paving blocks between high-rise facades and a row of thin young street trees. Seen from below, a sheer office tower rises out of the frame and its setback edge throws the shade line diagonally across the walkway. One pedestrian stands right at that line with half the body in shade and half in glare, looking up at the building edge. The tower, the sidewalk and the shadow all sit on the same continuous plane of stone.
Camera: medium shot from a low angle, shot on 20mm wide lens
Lighting/mood: single hard side-light cutting across the subject, deep chiaroscuro shadows, tense atmosphere
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 confined to the shaded half of the paving stones), film-noir low-key lighting, deep shadows
Korean urban context by default: Korean office tower proportions, Korean sidewalk tiling, no readable letters anywhere.
Text handling: building signage cropped out of frame or resolved as blank panels.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the paving stones of the sidewalk) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
서울 고층빌딩 보도 그림자 경계
```

### [카드 4]
**텍스트**
```text
모자란 몫은 자치구 그늘막이 메웠다
송파구 400개, 종로구 79개로 5배 차다
*그늘은 더위가 아니라 구 살림이 정했다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: an elderly woman's eyes squeezed nearly shut under the flat of her own hand, sweat tracking along the temple. She waits at a Korean crosswalk with no shade structure over it, standing alone at the curb, her gaze aimed across the road toward the far corner. Just behind her heel, four bare bolt stubs are set into the pavement where a folding shade canopy was never installed. The crosswalk asphalt runs unbroken behind her, glaring and empty.
Camera: tight close-up from eye-level, shot on 85mm portrait lens
Lighting/mood: harsh overexposed midday sunlight, hard shadows, oppressive heat
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 confined to the tiny shadow cast by her raised hand), muted daylight contrast
Korean urban context by default: Korean pedestrian signal pole, Korean crosswalk stripes, Korean street furniture with no readable letters.
Text handling: no signage in frame; all incidental writing avoided by framing.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the crosswalk asphalt) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
횡단보도 그늘막 파라솔 신호대기
```

### [카드 5]
**텍스트**
```text
*그래서 서울시가 소관을 옮긴다*
8월 19일 내놓은 '그늘보행권'은
지구단위계획과 정비사업에 기준을 건다
그늘이 구 살림 아닌 계획의 몫이 된다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a planner's fingertip pressing down on a drafting table as the other hand draws one continuous shade band along a street on the plan. Seen straight down onto the table, a large city block drawing fills the surface, and the new hatched band runs unbroken along the sidewalk line from one edge of the sheet to the other. A scale ruler and a folded planning sheet lie beside it. The whole frame is that one table surface; the drawing, the hands and the tools all rest on it.
Camera: medium shot from a bird's-eye view, shot on 35mm lens
Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 confined to the newly drawn shade band on the plan), film-noir low-key lighting, deep shadows
Korean urban context by default: Korean planning drawing conventions, Korean office desk objects, no readable letters.
Text handling: the plan is rendered as line work, hatching and blank callout boxes only, with all labels left unwritten.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the drafting table top) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
지구단위계획 도면 도시계획
```

### [카드 6]
**텍스트**
```text
사업비가 정해진 건 시범 10곳까지다
2028년 이후 약 350개 가로는
"사업주체와 협의"로 남았고
*민간엔 용적률 인센티브를 검토한다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the empty stretch of table between two pulled-out chairs, where nothing has been put down yet. A long meeting table stands in a dim room after everyone has gone, two chairs angled out on opposite sides facing each other across the gap. A single rolled plan lies closed near one edge and one cup sits cold beside it. Nobody is in the room and the table runs from the near edge of the frame to the far wall as one unbroken surface.
Camera: wide shot from a high angle, shot on 35mm lens
Lighting/mood: cold blue dim interior light, heavy and suffocating, faint trembling tension
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 confined to the thin edge of the rolled plan), film-noir low-key lighting, deep shadows
Korean urban context by default: Korean municipal meeting room furniture and proportions, no readable letters.
Text handling: the rolled plan stays closed and every document surface is kept blank or turned away from view.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the meeting table top) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
서울시청 회의실 협의 테이블
```

### [카드 7]
**텍스트**
```text
그늘이 도시 구조의 문제라는 건
이제 서울시도 인정했다
남은 건 그 구조를 바꾸는 값이다
*그게 정해져야 이름이 권리가 된다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the thin shadow of a newly planted street tree, still too small to cover the width of the walkway beneath it. Recurring location — a wide Seoul downtown sidewalk of gray paving blocks between high-rise facades and a row of thin young street trees. The sidewalk runs straight away from the viewer down the center of the frame, symmetrical and still, with the young trees spaced evenly along it and their small shadows falling short of the far curb. No one is walking on it. The pavement holds the whole frame as one unbroken plane from the near edge to the vanishing point.
Camera: extreme long shot from eye-level, front-on shot with symmetrical composition, shot on 35mm lens
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 confined to the young leaves and the small shadows they cast), muted daylight contrast
Korean urban context by default: Korean sidewalk tiling, Korean tree guards and curb forms, no readable letters.
Text handling: all storefront and street signage kept out of frame or resolved as blank shapes.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the wide empty pavement) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
서울 보도 어린 가로수 식재
```
