# 응모는 공짜, 읽는 건 사람

**[프롬프트 설계]**
- 화풍: B 극화 — 감정 사건이 아니라 제도·비용 구조가 축이라, 잉크 선과 명암만으로 무게를 실어야 한다
- 분위기: 아무도 화내지 않는데 문이 닫히는 서늘함. 무심한 확산광 아래 종이만 쌓이고, 그 앞에 선 사람은 계속 작아진다
- 연출 방향: 독자는 '혼자 쓴 원고를 어딘가에 보내 본 사람'이고, 멈추는 자리는 반칙한 사람이 하나도 없는데 상이 흔들린다는 대목이다. 그래서 카메라는 응모자도 AI도 겨누지 않고, **쌓인 종이의 단면 → 그것을 손으로 넘기는 사람 → 요강에 이미 인쇄돼 있던 한 줄** 순서로 과녁을 옮긴다. 악센트 네온그린은 원고 묶음을 묶은 끈 하나에만 걸어 덱 전체를 관통시키고, 마지막 카드에서는 그 끈만 빈 의자에 남긴다. 규탄이 아니라 '비용을 아무도 안 정했다'는 설계 실패가 보이게, 화면에서 사람을 지우지 말고 계속 읽게 둔다
- 독자 동선: **발단** 카드1→**전개** 카드2~3→**피크** 카드4→**해소** 카드5~6→**시사점** 카드7 · 훅=카드1 끝(예고형 "편집부가 센 건 편수만이 아니었다")+카드3 끝(예고형 "그런데 규정을 어긴 사람은 없었다") · 착지 한 줄 요지 = 문을 여는 값이 커졌는데 누가 낼지 아무도 안 정했고, 좁힌 문은 몇 년 뒤 안 나온 책으로 돌아온다
- 연속성 앵커: Recurring subject - a Japanese editor, a man in his 50s with close-cropped graying hair and thin wire-rimmed glasses, wearing a plain dark navy cardigan over a white shirt. / Recurring location - the same cramped Japanese publishing house editorial room with gray metal shelves.

### [카드 1]
**텍스트**
```text
일본 SF 신인상 공모가 마감됐다
3월 말까지 원고 1,012편이 왔다
지난해 484편에서 두 배 넘게 뛰었다
*편집부가 센 건 편수만이 아니었다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the lone editor's shoulders, kept small under the stacks standing in front of him. Recurring subject - a Japanese editor, a man in his 50s with close-cropped graying hair and thin wire-rimmed glasses, wearing a plain dark navy cardigan over a white shirt. He stands at the near end of one long editorial table with his arms at his sides, looking down at rows of tied paper manuscript bundles that cover the table and run past the top of the frame; he has not picked one up yet. The nearest bundle catches the daylight so the cut edges of the paper read clearly, while the rows behind recede into flat gray and lead the eye toward the right edge, with nose room kept on the right. Recurring location - the same cramped Japanese publishing house editorial room with gray metal shelves.
Camera: wide shot, full body with surrounding environment and spatial context, from a high angle looking down so the subject reads small and observed, shot on a 24mm wide lens with cinematic wide framing and subtle depth
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the cords binding the manuscript bundles), muted daylight contrast
Text handling: no readable writing anywhere; pages are seen edge-on or from too far to resolve type, and any printed line reads as indistinct texture only. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the long editorial table) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Hayakawa Shobo editorial office manuscripts
```

### [카드 2]
**텍스트**
```text
하야카와쇼보 편집부의 추정은 이렇다
열 편 중 두세 편이 생성형 AI다
*가려낸 단서는 글이 아니라 서식이었다*
단락 사이 공백이 중간부터 사라진다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the editor's narrowed eyes tracking one line down a single loose page. Recurring subject - a Japanese editor, a man in his 50s with close-cropped graying hair and thin wire-rimmed glasses, wearing a plain dark navy cardigan over a white shirt. He holds one sheet up close with both hands and reads it, his eyes moving across the paper, his mouth pressed flat. A stack of unread bundles sits at his elbow at the edge of the frame, and his desk lamp is switched off. Recurring location - the same cramped Japanese publishing house editorial room with gray metal shelves.
Camera: medium close-up, chest-up framing carrying facial emotion with slight body context, from eye level with a neutral and balanced perspective, shot on an 85mm portrait lens with soft background separation
Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on a small tab clipped to the page he holds), muted daylight contrast
Text handling: the page he holds is angled away and cropped by his hands, so its printed lines read as indistinct rows of texture, never as characters. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the flat office wall behind him) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Japanese book editor reading manuscript slush pile
```

### [카드 3]
**텍스트**
```text
늘어난 건 SF만이 아니었다
다카라지마샤 미스터리 대상이 그렇다
461편에서 731편으로 60% 뛰었다
*그런데 규정을 어긴 사람은 없었다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the distance between two crouching staff and the sheer length of the blocks laid out around them. Seen from directly overhead, hundreds of tied paper manuscript bundles are laid out in separate rectangular blocks of different heights across one continuous floor. Two small staff figures crouch between the blocks, one setting another bundle down at the end of a row and the other counting with a hand extended over the paper. The blocks run off toward the right edge of the frame with the open floor kept on the right. Recurring location - the same cramped Japanese publishing house editorial room with gray metal shelves.
Camera: extreme long shot with tiny subjects in a vast environment conveying scale and isolation, from an overhead bird's-eye top-down angle reading the layout as geometry, shot on a 14mm ultra-wide lens with dramatic depth
Lighting/mood: flat cold even surveillance light, no shadow no warmth, detached and watchful
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the cords of one bundle among the hundreds), muted daylight contrast
Text handling: seen from this height no page resolves into type; the paper reads only as stacked edges and flat tone. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the editorial room floor) extending edge to edge from top to bottom of the frame. The main subjects are anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Kono Mystery ga Sugoi Taisho Takarajimasha
```

### [카드 4]
**텍스트**
```text
요강에는 이미 적혀 있었다
*"생성AI 등의 이용도 가능하다"*
응모료 0원에 상금은 100만 엔이다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: one raked line on the page with a fingertip stopped just beneath it, not moving. A single sheet of contest application guidelines lies flat on a dark desk, tilted so a hard side light rakes across the paper fibers and lifts every crease. A bare fingertip rests directly under one line of print, halted mid-read, the nail pressed slightly pale. The printed rows are cropped by the frame edge and resolve only as indistinct bands of type, and nothing else in the room is lit.
Camera: extreme close-up on a single detail with visible paper texture, from a high angle looking straight down at the page, shot on a 100mm macro lens with fine detail and shallow depth of field
Lighting/mood: single hard side-light cutting across the subject, deep chiaroscuro shadows, tense atmosphere
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 as a thin marker rule drawn in the margin beside that one line), film-noir low-key lighting, deep shadows
Text handling: the type is deliberately unreadable - cropped at the frame edge, raked at a grazing angle, and rendered as indistinct printed bands rather than characters. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the paper page) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Hayakawa SF Contest submission guidelines
```

### [카드 5]
**텍스트**
```text
*반칙한 사람이 없는데 상이 흔들린다*
무너진 건 오래된 균형이었다
원고 한 편에 몇 달이 들던 시절이라
출판사가 사람을 붙여 전부 읽어 왔다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the editor's set jaw as he turns another page without looking up. Recurring subject - a Japanese editor, a man in his 50s with close-cropped graying hair and thin wire-rimmed glasses, wearing a plain dark navy cardigan over a white shirt. He sits mid-table with two other staff further along the same long reading table, all three bent over open manuscripts and turning pages by hand, coats still on their shoulders. The unread bundles beside them have not gone down, and no one is speaking. Recurring location - the same cramped Japanese publishing house editorial room with gray metal shelves.
Camera: medium shot, waist-up framing showing faces and hand gestures, from eye level with a neutral realistic perspective, shot on a 35mm lens with natural documentary perspective and minimal distortion
Lighting/mood: cold blue dim interior light, heavy and suffocating, faint trembling tension
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the cords of the unread stack beside them), film-noir low-key lighting, deep shadows
Text handling: the open manuscripts face the readers and away from camera, so their pages read as blank tone and shadow only. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the plain back wall of the editorial room) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Japanese literary prize manuscript screening editors
```

### [카드 6]
**텍스트**
```text
쓰는 값이 0이 되자 읽는 값만 남았다
*1차부터 최종심까지 전부 사람 손이다*
심사비는 연간 수백만 엔씩 불어난다
닛케이는 신인상이 줄어들 거라고 봤다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the readers made tiny at the foot of stacks that rise past the top of the frame. Seen from near floor level looking up, columns of tied paper manuscript bundles tower like a wall and vanish beyond the upper edge. Recurring subject - a Japanese editor, a man in his 50s with close-cropped graying hair and thin wire-rimmed glasses, wearing a plain dark navy cardigan over a white shirt. He sits low on a stool at the base of that wall with two other readers, all of them holding pages open on their knees, and one higher chair set behind them stands empty. Recurring location - the same cramped Japanese publishing house editorial room with gray metal shelves.
Camera: wide shot, full body with surrounding environment and spatial context, from a low ground-level angle looking up that exaggerates the scale above the figures, shot on a 20mm wide lens with documentary realism
Lighting/mood: single pool of hard light isolating the figure in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the cords running up the towering bundles), film-noir low-key lighting, deep shadows
Text handling: every page is seen edge-on or in shadow, so nothing resolves into type. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the towering wall of stacked paper bundles) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Japanese literary award final judging panel
```

### [카드 7]
**텍스트**
```text
신인상은 다음 세대를 찾는 문이다
그 문을 여는 값이 갑자기 커졌는데
누가 낼지는 아무도 정하지 않았다
*문을 좁히면 몇 년 뒤 책이 줄어든다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the pulled-out chair standing empty where the stacks used to be. A wide, centered, static view of the editorial room after hours, framed straight on with nothing off to either side. One chair is drawn back from a bare table whose surface holds nothing at all, and behind it a door stands half closed with a narrow band of light falling across the floor toward the viewer. A single cut cord is left lying on the seat of the chair. No people are in the room. Recurring location - the same cramped Japanese publishing house editorial room with gray metal shelves.
Camera: extreme long shot, tiny subject in a vast environment conveying scale and isolation, from eye level, front-on with a symmetrical centered composition, shot on a 35mm lens with natural documentary perspective and minimal distortion
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the one cut cord left on the empty chair), muted daylight contrast
Text handling: the room holds no signage, no nameplate and no paper; every surface is bare. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the plain far wall of the empty editorial room) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Japanese publishing house empty office chair
```
