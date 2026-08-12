# 열아홉이 몰던 벤츠, 열아홉이 조수석에 있었다

**[프롬프트 설계]**
- 화풍: A 한국웹툰 수채화 — 처벌이 아니라 남겨진 시간이 주제인 또래 죽음이라, 고발보다 감정이입·여운의 결이 맞다
- 분위기: 술자리가 끝난 자리부터 아침빛이 든 도로까지, 새벽의 차갑고 조용한 정적 — 파스텔 위에 dusty blue 한기가 깔리고 붉은 빛 한 점만 살아 있는 톤(thumb_dispatch LGT02의 pre-dawn 냉기·정조 계승)
- 연출 방향: 뉴스 안 보는 또래가 멈추는 이유는 "친구 차 조수석에 아무렇지 않게 타본" 자기 기억이 겹치기 때문이다 — 그래서 사고 자체보다 **결정이 만들어지는 손끝**(테이블 위 열쇠를 감싸 쥐는 손 → 핸들 → 금 간 유리에 힘이 풀린 손)을 카드마다 이어 잡아, 술자리에서 도로까지의 짧은 거리를 손 하나로 보이게 한다. 붉은 악센트는 열쇠고리 → 계기판 경고등 → 경광등 → 응급실 표시등 → 파편으로 옮겨 다니며 그 동선을 잇는 실이 된다. 시사점(끊을 수 있었던 지점)은 마지막에 인물을 아주 작게 놓아 독자가 그 자리에 자기를 대입하게 한다
- 독자 동선: **발단** 카드1(술자리 파장·시각·장소)→**전개** 카드2(어머니 명의 벤츠·친구 2명·심야 도로)→**피크** 카드3(가로수 정면 충돌·구조 14명·차 안에 갇힘 · 명도 최저·최타이트 ECU·3줄 침묵 비트)→**해소** 카드4(운전석 사망·조수석 경상의 낙차)→**시사점** 카드5 · 훅=카드1 끝(단서형: 차의 주인을 유보)+카드2 끝(예고형: 도로로 나감) 총 2개·질문형 0회·다음 카드 첫 줄이 즉시 회수 · 착지 한 줄 요지=술자리에서 도로까지 끊을 수 있었던 지점이 몇 번이었나
- 연속성 앵커: `Recurring subject: a Korean man of about nineteen, short black hair, a plain dark short-sleeve shirt, slim build.`(카드1·2·3) / `Recurring subject: a Korean woman of about nineteen, shoulder-length dark hair, a light cream blouse.`(카드1·2·4·5) / 반복 장소 = `the same two-lane Korean city road lined with roadside trees.`(카드2·3·5)

### [카드 1]
**텍스트**
```text
8월 5일 새벽 0시 35분, 경북 영천
셋이 마신 술자리가 끝난 참이었다
그중 한 명이 그대로 운전대를 잡았다
*시동을 건 차는 자기 차가 아니었다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: his fingertips closing around a car key left on the cleared table, the grip already decided. Recurring subject: a Korean man of about nineteen, short black hair, a plain dark short-sleeve shirt, slim build. He sits at the table and reaches for the key with his eyes fixed on it. Behind him two friends of the same age stay seated in soft focus, one of them a Korean woman of about nineteen, shoulder-length dark hair, a light cream blouse, both kept lower and softer so his hand remains the focus. Emptied glasses and a wiped-down wooden tabletop fill the rest of the frame, inside a small late-night Korean eatery.
Camera: wide shot with full body and surrounding environment from a high angle looking down at the table, shot on a 35mm lens, natural documentary perspective, minimal distortion
Lighting/mood: warm soft desk-lamp light, quiet wistful tone
Accent: desaturated pastel base with a single color accent of emergency red (the story's symbolic color) on the key fob, low-key ambience, deep shadows
Text handling: avoid all incidental lettering on signage, menus and labels by framing and angle; no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the wooden tabletop) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
음주운전 술자리 자동차 열쇠
```

### [카드 2]
**텍스트**
```text
그 차는 어머니 소유의 벤츠 승용차였다
*운전석에 앉은 A군은 열아홉이었다*
그는 함께 술을 마신 친구 2명을 태웠다
그리고 새벽 도로로 차를 몰고 나갔다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: his eyes fixed straight ahead through the windshield, blinking slowly, the focus not quite landing. Recurring subject: a Korean man of about nineteen, short black hair, a plain dark short-sleeve shirt, slim build. He grips the steering wheel with both hands and looks toward the right edge of the frame. In the passenger seat beside him sits a Korean woman of about nineteen, shoulder-length dark hair, a light cream blouse, turned slightly away and kept softer. Through the windshield lies the same two-lane Korean city road lined with roadside trees, empty at this hour. Korean road conventions: the steering wheel is on the left side of the car. Nose room on the right, gaze directed toward the right edge.
Camera: medium close-up with chest-up framing from eye level in a three-quarter angle, shot on a 50mm standard lens, minimal distortion, natural cinematic composition
Lighting/mood: cold blue dashboard under-glow lighting the face from below in a dark cabin, restless unease
Accent: desaturated pastel base with a single color accent of emergency red (the story's symbolic color) on a single warning light in the instrument cluster, low-key lighting, deep shadows
Text handling: avoid all incidental lettering on dashboard displays, road signs and shopfronts by framing and angle; no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the dark car interior cabin) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
벤츠 운전석 계기판 야간
```

### [카드 3]
**텍스트**
```text
*차는 가로수를 정면으로 들이받았다*
구조장비 4대와 인력 14명이 투입됐다
두 사람은 차 안에 갇혀 있었다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a young hand pressed flat against the inside of a cracked side window, the fingers going slack. Recurring subject: a Korean man of about nineteen, short black hair, a plain dark short-sleeve shirt, slim build. He is barely readable in the dark cabin behind the glass, head lowered, no injury shown. Beyond the glass and far out of focus, a few rescue workers in helmets move toward the door with handheld lights, kept dim and small so the hand stays the focus. The car has stopped nose-first against a roadside tree on the same two-lane Korean city road.
Camera: extreme close-up on the hand and the cracked glass from a Dutch tilted angle with a canted frame, shot on a 100mm macro lens, fine detail, shallow depth of field
Lighting/mood: cold blue dim interior light, heavy and suffocating, faint trembling tension
Accent: desaturated pastel base with a single color accent of emergency red (the story's symbolic color) as a rotating beacon reflection sliding across the glass, film-noir low-key lighting, deep shadows
Text handling: no lettering anywhere in frame; no garbled or fake script, no meaningless letters, no random characters, no dense text. No blood, no wounds, no impact moment.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the cracked car window glass) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
영천 신망정사거리 가로수 충돌
```

### [카드 4]
**텍스트**
```text
A군은 심정지 상태로 이송돼 숨졌다
조수석의 대학생 B양은 경상을 입었다
둘을 가른 건 운전석과 조수석이었다
*죽은 쪽도 산 쪽도 열아홉이었다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: her hands gripping the edge of the blanket around her shoulders, eyes cast down, unable to look at the doors ahead. Recurring subject: a Korean woman of about nineteen, shoulder-length dark hair, a light cream blouse. She stands a few steps back in a hospital corridor with a bandage on one forearm. Ahead of her, medical staff push a fully covered stretcher through swinging doors, their backs completely blocking what lies on it. The corridor stretches away behind them, empty at this hour.
Camera: wide shot with full body and the surrounding corridor from eye level, shot on a 24mm wide lens, cinematic wide shot with spatial context
Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional
Accent: desaturated pastel base with a single color accent of emergency red (the story's symbolic color) on a small indicator lamp above the doors, muted indoor contrast
Text handling: avoid all incidental lettering on hospital signage, door plates and charts by framing and angle; no garbled or fake script, no meaningless letters, no random characters, no dense text. Nothing on the stretcher is visible.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the hospital corridor wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
응급실 복도 이송 구급대원
```

### [카드 5]
**텍스트**
```text
이 사고에는 물어야 할 가해자가 없다
술을 마시고 운전대를 잡은 쪽이 숨졌다
남은 건 조수석에 있던 쪽의 시간이다
*끊을 수 있었던 지점은 몇 번이었나*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the small distance between a lone standing figure and the scarred tree trunk she is facing. Recurring subject: a Korean woman of about nineteen, shoulder-length dark hair, a light cream blouse. She stands alone and still at the center of the frame, arms at her sides, facing the roadside tree whose bark is freshly gouged. Scattered glass fragments trace a short arc across the asphalt between her and the tree. It is the same two-lane Korean city road lined with roadside trees, now emptied and lit by early morning.
Camera: extreme long shot with a tiny subject in a vast environment from a bird's-eye overhead angle, shot on a 14mm ultra-wide lens, vast environment with dramatic depth
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: desaturated pastel base with a single color accent of emergency red (the story's symbolic color) on one broken taillight fragment among the glass, muted daylight contrast
Text handling: avoid all incidental lettering on road markings, signs and shopfronts by framing and angle; no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the asphalt road surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
가로수 충돌 흔적 도로
```
