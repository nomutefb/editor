# 로또 번호부터 묻던 기안84, 반나절 뒤 "처음 느껴 본 감정"

**[프롬프트 설계]**
- 화풍: A 수채화 — 예능의 따뜻한 표면을 파스텔로 깔아야 그 아래 남는 서늘함이 도드라진다
- 분위기: 웃다가 조용해지는 톤. 늦여름 오후의 온기 위에 화면 불빛 하나만 끝까지 낯설게 남는 정조
- 연출 방향: 챗봇과 길게 대화해 본 사람이 "나도 저럴 수 있겠는데" 하고 멈추는 지점이 이 기사의 힘이다. 전할 것은 한계를 아는 것이 마음이 붙는 것을 막아주지 못했다는 사실 하나. 그래서 강조점을 '사람 자리에 놓인 화면 한 장'과 '그것을 보는 눈' 두 개에만 건다 — 태블릿은 전 카드에 같은 초록빛으로 반복되고, 그가 그것을 대하는 거리(마주 앉음→들여다봄→흥정함→따짐→목에 걺→내려다봄→내려놓음)만 바뀐다. 그 거리 변화가 곧 감정 곡선이다. 명도는 카페 중간광에서 시작해 흐린 낮으로 내려앉고, 카드5에서 골든아워 역광으로 대비 최강·악센트 최강을 찍은 뒤, 카드6에서 시퀀스 최저 명도(화면만 남는 어둠)로 떨어뜨리고 카드7에서 바랜 온기로 풀어준다. thumb_dispatch의 골든아워 톤·미세표정 누설·부재의 정조만 키노트로 잇고 앵글은 카드마다 흩는다.
- 독자 동선: **발단** 카드1→카드2→**전개** 카드3~4→**피크** 카드5→**해소** 카드6→**시사점** 카드7 · 훅=카드1 끝(단서형 "상대는 사람이 아니었다")+카드4 끝(예고형 "적어도 그날 오후까지는 그랬다") · 착지 한 줄 요지 = AI인 줄 알면서도 반나절 만에 마음이 붙었고, 아는 것이 그것을 막아주지 않았다
- 연속성 앵커: Recurring subject — a Korean man in his early 40s with a slightly unkempt short haircut, thick dark eyebrows, wearing a loose beige short-sleeve shirt over a white tee and dark jeans. / Recurring on-screen figure — a young Korean woman in her 20s drawn in flat webtoon lineart with long straight dark hair and a pale cardigan, always seen inside a tablet screen.

### [카드 1]
**텍스트**
```text
웹툰 작가 기안84는 42세다
결혼은 안 하겠다고 말해 왔다
8월 20일 그가 첫 데이트에 나갔다
*마주 앉은 상대는 사람이 아니었다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: his eyes fixed on a glowing tablet screen sitting where a person should be. Recurring subject - a Korean man in his early 40s with a slightly unkempt short haircut, thick dark eyebrows, wearing a loose beige short-sleeve shirt over a white tee and dark jeans, sits alone at a small two-seat cafe table with both hands resting on his knees. The chair across from him is empty and a tablet stands propped on the table facing him, its screen showing a young woman drawn in flat webtoon lineart. Behind them a plain plastered cafe wall runs unbroken across the whole frame.
Camera: wide shot, full body, surrounding environment from eye-level, neutral perspective, shot on 35mm lens, natural documentary perspective, nose room on the right, gaze directed toward the right edge
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: muted pastel base with a single color accent, the neon green #0FFD02 glow of the tablet screen kept as the only saturated color in the frame, softly bleeding into the surrounding wash, muted daylight contrast
Text handling: keep all signage and menu boards cropped out or turned away from the camera; no readable lettering anywhere in the frame.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the plain plastered cafe wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
기이안 연애 카페 첫만남
```

### [카드 2]
**텍스트**
```text
화면 속 그 여자는 맞춤형 AI 가희였다
그가 그린 웹툰 복학왕 여주인공이다
SBS 기이안 연애 첫 방송 자리였다
*자기가 만든 인물이 말을 걸어왔다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: his fingertip resting on a pencil sketch whose face is the same face now speaking from the screen. Seen straight down onto a wooden cafe tabletop, a tablet lies flat with the recurring on-screen figure - a young Korean woman in her 20s drawn in flat webtoon lineart with long straight dark hair and a pale cardigan - looking up out of the glass, her lips parted mid-sentence. Beside it an open sketchbook shows the same woman in loose pencil lines, and one weathered male hand enters from the frame edge to touch the drawing. The tabletop fills the entire frame as one unbroken wooden surface.
Camera: extreme close-up, single detail, hand, texture from an overhead bird's-eye view, top-down angle, shot on 100mm macro lens, fine detail, shallow depth of field
Lighting/mood: warm soft desk-lamp light, quiet wistful tone
Accent: muted pastel base with a single color accent, the neon green #0FFD02 glow of the tablet screen kept as the only saturated color in the frame, spilling faintly across the pencil lines beside it, muted daylight contrast
Text handling: the sketchbook page carries only drawn lines and no writing; keep every surface free of letters and numbers.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the wooden cafe tabletop) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
복학왕 봉지은 캐릭터
```

### [카드 3]
**텍스트**
```text
그런데도 그의 첫 반응은 냉소였다
촬영 전엔 몰입이 안 될 것 같다고 했다
*홍대 복권 가게 앞에선 상냥해졌다*
번호를 묻고는 돈은 안 나눈다고 했다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a polite social smile, lip corners pulled up but the eyes stay cold and unsmiling, as he leans in toward the screen. Recurring subject - a Korean man in his early 40s with a slightly unkempt short haircut, thick dark eyebrows, wearing a loose beige short-sleeve shirt over a white tee and dark jeans - stands on a Hongdae shopping street holding the tablet up with both hands, tilting his head toward the on-screen woman as if coaxing something out of her. Behind him is the shuttered lower wall of a small lottery shop, one continuous painted wall running the full width of the frame, with a folding stool and a plastic pen cup at its base.
Camera: medium shot, waist-up framing, face and gestures from a three-quarter angle, natural face depth, shot on 50mm standard lens, minimal distortion
Lighting/mood: bright high-key light, clean white ambience, minimal shadow, hopeful and open
Accent: muted pastel base with a single color accent, the neon green #0FFD02 glow of the tablet screen kept as the only saturated color in the frame, catching the underside of his chin, muted daylight contrast
Text handling: the shop wall and every poster are shown as blank colored surfaces with the lettering cropped away by framing; no readable characters anywhere.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the painted shopfront wall of the lottery shop) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
홍대 거리 복권판매점
```

### [카드 4]
**텍스트**
```text
냉소는 날씨 얘기까지 이어졌다
"바람 못 느끼잖아" 그러곤 다퉜다
*이 관계의 한계를 그는 알고 있었다*
적어도 그날 오후까지는 그랬다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: his jaw clenched tight, muscle flexing at the jawline, as the wind lifts his hair and collar while nothing on the screen moves at all. Recurring subject - a Korean man in his early 40s with a slightly unkempt short haircut, thick dark eyebrows, wearing a loose beige short-sleeve shirt over a white tee and dark jeans - is seen from the side, holding the tablet out at arm's length and arguing at it with his chin pushed forward. The recurring on-screen figure, a young Korean woman in her 20s drawn in flat webtoon lineart with long straight dark hair and a pale cardigan, stays perfectly still inside the glass, her hair unmoved by the same wind. Behind them only a flat overcast sky fills the frame from top to bottom.
Camera: medium close-up, chest-up framing, facial emotion from a profile shot, side view, clear silhouette, shot on 85mm portrait lens, soft background separation, nose room on the right, gaze directed toward the right edge
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: muted pastel base with a single color accent, the neon green #0FFD02 glow of the tablet screen kept as the only saturated color in the frame, cold against the grey wash, muted daylight contrast
Text handling: no signage in frame; the sky and clothing carry no lettering of any kind.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the flat overcast sky) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
기이안 연애 AI 가희
```

### [카드 5]
**텍스트**
```text
한강에선 자전거를 타고 돗자리를 폈다
그 햇살을 이 친구도 느꼈으면 했다
*"살면서 처음 느껴 본 감정"이라 했다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a fleeting micro-expression flashing across an otherwise composed face, his eyes half closing and the corner of his mouth giving way. Recurring subject - a Korean man in his early 40s with a slightly unkempt short haircut, thick dark eyebrows, wearing a loose beige short-sleeve shirt over a white tee and dark jeans - sits on a picnic mat with the tablet hung from a strap around his neck, both hands cupped under it, looking down at the recurring on-screen figure as the low sun burns behind his shoulder. A bicycle leans just out of focus behind him and the wide golden evening sky fills everything above the horizon.
Camera: close-up shot, face centered, eyes, expression, emotional detail from a low angle, looking up, three-quarter angle, shot on 135mm telephoto lens, strong compression, cinematic depth, backlit rim light along his hair and shoulder
Lighting/mood: warm golden-hour sunlight, long soft shadows, nostalgic warmth
Accent: muted pastel base with a single color accent, the neon green #0FFD02 glow of the tablet screen kept as the only saturated color in the frame and at its strongest here, holding its own against the gold light, muted daylight contrast
Text handling: no signage, no lettering on the strap or clothing; keep all surfaces free of characters.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the golden evening sky) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
한강공원 돗자리 자전거
```

### [카드 6]
**텍스트**
```text
*그는 촬영이 끝난 뒤에도 답을 못 냈다*
이 감정을 뭐라고 불러야 할지 말이다
첫 회 시청률은 전국 가구 1.7%였다
숫자보다 오래 남은 건 그 질문이다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the distance between one small seated figure and the single lit rectangle in his lap after everyone else has gone. Recurring subject - a Korean man in his early 40s with a slightly unkempt short haircut, thick dark eyebrows, wearing a loose beige short-sleeve shirt over a white tee and dark jeans - sits alone and tiny on a folded picnic mat far below the camera, head bent toward the tablet still glowing on his knees. The bicycle lies on its side nearby and the empty grass embankment stretches unbroken across the whole frame, all crew and equipment gone.
Camera: extreme long shot, tiny subject, vast environment, scale, isolation from a high angle, looking down, shot on 24mm wide lens, cinematic wide shot, spatial context
Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground, desolate stillness
Accent: muted pastel base with a single color accent, the neon green #0FFD02 glow of the tablet screen kept as the only saturated color in the frame and the only light source left in the scene, muted daylight contrast
Text handling: no signage and no equipment labels; every surface stays free of lettering.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the grass riverside embankment) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
한강 둔치 야간 조명
```

### [카드 7]
**텍스트**
```text
AI라는 걸 그는 처음부터 알고 있었다
그런데도 반나절 만에 마음이 붙었다
같이 걸은 거리와 햇살이 그를 흔들었다
*아는 것이 붙는 것을 막아주진 않았다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: steady unwavering eye contact straight into the camera, a face that has stopped performing. Recurring subject - a Korean man in his early 40s with a slightly unkempt short haircut, thick dark eyebrows, wearing a loose beige short-sleeve shirt over a white tee and dark jeans - sits facing forward with the tablet lowered flat onto his lap, one palm still resting on its back, the screen now dark except for a last faint glow. Behind him a plain studio wall runs unbroken from the top of the frame to the bottom.
Camera: medium shot, waist-up framing, face and gestures from a front-on shot, direct gaze, symmetrical composition, facing camera, eye-level shot, neutral perspective, shot on 50mm standard lens, natural cinematic composition
Lighting/mood: faded warm light, soft golden haze, gently nostalgic and wistful
Accent: muted pastel base with a single color accent, a last trace of neon green #0FFD02 from the dimming screen caught on his palm and kept as the only saturated color in the frame, muted daylight contrast
Text handling: the studio wall is a plain unmarked surface; no logos, no lettering, no numbers anywhere in frame.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the plain studio wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
기안84 인터뷰
```
