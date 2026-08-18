# 🚗 가장 먼저 지워진 건 자율주행이었다

**[프롬프트 설계]**
- 화풍: B 극화 — 감정 서사가 아니라 '조건과 일정'이 축이라, 저채도·경계 또렷한 사실성 화면이 맞다
- 분위기: 크게 다친 사람이 없다는 안도 뒤에 남는 서늘함. 소란 없이 가라앉은 평일 오후 도심, 사고보다 사고가 멈춰 선 자리가 더 오래 보이는 톤(흐린 낮 확산광 계열의 눌린 정조 + 사람이 비워진 자리를 계승)
- 연출 방향: 독자는 '테슬라 사고'라는 다섯 글자에서 반사적으로 자율주행을 떠올리는데, 첫 보도가 그 가능성부터 지워 버린다 — 그 허탈이 멈춤점(독자훅)이다. 전할 것은 새 위험을 의심하는 사이 오래된 위험을 막을 장치가 아직 오지 않았다는 낙차. 그래서 카메라는 얼굴이 아니라 **멈추지 못한 자리**에 붙는다: 접힌 범퍼가 기둥에 닿은 지점, 밟지 않은 두 페달, 그리고 그 앞 1~1.5m의 빈 틈. 사람 표정을 지우고 손·발·정지 지점만 남겨, 이 사고를 개인 과실 드라마가 아니라 조건의 문제로 보이게 한다
- 독자 동선: **발단** 카드1→**전개** 카드2~3→**피크** 카드4→**해소** 카드5→**시사점** 카드6 · 훅=카드1 끝(단서형 — 사고가 멈춘 장소·시각을 흘리고 다음 장이 피해 규모로 회수)+카드3 끝(미완 예고형 — 경찰 인용이 원인을 열어 둔 채 끊김) · 착지 한 줄 요지 = 그 오래된 위험을 막을 장치의 의무 장착일은 2029년 1월 1일, 새로 만드는 차부터다
- 연속성 앵커: 반복 인물 (없음) / 반복 장소 — `Recurring location — the plaza in front of a large glass-walled office and shopping complex in Yeouido, Seoul, with a freestanding vertical signage pillar near a downhill parking garage exit ramp.`

### [카드 1]
**텍스트**
```text
8월 18일 오후 2시 45분께 여의도,
테슬라 시승차가 주차장을 나오자마자
바로 앞 IFC몰 간판을 들이받았다
*하필 평일 오후의 쇼핑몰 앞이었다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the folded-in front bumper pressed against the base of a tall vertical signage pillar, the exact point where the car stopped. Recurring location — the plaza in front of a large glass-walled office and shopping complex in Yeouido, Seoul, with a freestanding vertical signage pillar near a downhill parking garage exit ramp. A dark sedan sits at an angle with its nose buried into the pillar, all doors closed and nobody inside, while a short tire mark trails back from its rear wheels to the mouth of the underground parking exit ramp behind it. The signage panel is completely blank with no letters on it. At the far right edge a few weekday afternoon pedestrians are only faint distant silhouettes, already walking away.
Camera: wide shot from a high angle, shot on 35mm lens
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the crumpled bumper edge, muted daylight contrast
Korean default setting: Korean urban street conventions, left-hand drive, Korean road markings and curb shapes.
Vector: nose room on the right, the tire mark and the car's angle leading the eye toward the right edge.
Text handling: the signage panel, all shopfronts and every background surface are blank — no letters, no logos, no license plate digits; avoid incidental text through framing and cropping. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the plaza pavement) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
여의도 IFC몰 정문 간판
```

### [카드 2]
**텍스트**
```text
*다행히 다친 건 차 안의 3명뿐이었다*
모두 경상, 두 병원으로 나뉘어 갔다
지나던 사람이 다쳤다는 보도는 없다
소방은 차대차 사고로 접수했다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a bandaged hand resting loosely on the stretcher rail, the fingers relaxed, the injury clearly minor. Recurring location — the plaza in front of a large glass-walled office and shopping complex in Yeouido, Seoul, with a freestanding vertical signage pillar near a downhill parking garage exit ramp. Two paramedics in uniform lift the stretcher toward the open rear doors of an ambulance, one at the head and one at the foot, both looking down at the patient whose face is turned away from the camera. A third responder stands at the right rear corner holding the door open and glancing back toward the crash site.
Camera: medium shot from eye-level, shot on 85mm portrait lens
Lighting/mood: flat sterile clinical fluorescent light spilling from the ambulance interior, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the stretcher rail, muted daylight contrast
Korean default setting: Korean urban street conventions, left-hand drive, Korean ambulance proportions without any markings.
Text handling: the ambulance body, uniforms and all equipment are unmarked and blank — no letters, no logos, no numbers; avoid incidental text through framing and cropping. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the plaza pavement) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
- no blood, no visible wounds, no distressed or agonized expression
```
**검색어**
```text
119 구급차 들것 환자 이송
```

### [카드 3]
**텍스트**
```text
그 사이 경찰이 먼저 지운 건 둘이었다
차는 자율 주행 상태가 아니었고
음주나 약물 정황도 발견되지 않았다
*운전 실수인지는 "조사해봐야 한다"*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a gloved fingertip halted in the air just above the steering column, not yet touching anything. Recurring location — the plaza in front of a large glass-walled office and shopping complex in Yeouido, Seoul, with a freestanding vertical signage pillar near a downhill parking garage exit ramp. A police investigator leans into the open driver's door of the stopped sedan and looks down at the dashboard and the empty driver's seat, while a second officer stands just behind with a notebook, following the same line of sight. The dashboard screen is dark and completely blank, reflecting nothing.
Camera: medium close-up from a high angle looking down into the open driver's door, shot on 70mm short telephoto
Lighting/mood: cold blue dim interior light, heavy and suffocating, faint trembling tension
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) on the investigator's glove cuff, film-noir low-key lighting, deep shadows
Korean default setting: Korean urban street conventions, left-hand drive, Korean sedan interior layout.
Vector: nose room on the right, both officers' gaze carried toward the right edge of the frame.
Text handling: the dashboard display, notebook page, uniforms and badges are blank — no letters, no logos, no numbers; avoid incidental text through framing and cropping. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the driver's seat upholstery and floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
교통사고 현장 경찰 차량 감식
```

### [카드 4]
**텍스트**
```text
*제목 끝에 "자율주행 아냐"가 붙었다*
안 붙이면 그렇게 읽힌다는 뜻이었다
의심이 걷히면 남는 건 오래된 사고다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the two pedals hanging side by side in the dark footwell, one broad and one narrow, both untouched. Seen from the floor looking up, the brake and the accelerator fill the center of the frame with the seat edge above them and the mat below. At the very top edge, only the lower half of a driver's leg and shoe is visible, hovering in the air between the two pedals without resting on either. Nothing else occupies the frame — no dashboard, no window, no second figure.
Camera: tight close-up from a ground-level worm's-eye angle, shot on 24mm wide lens
Lighting/mood: single hard side-light cutting across the subject, deep chiaroscuro shadows, tense atmosphere
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) tracing the rim of the accelerator pedal at its strongest intensity in the whole sequence, film-noir low-key lighting, deep shadows
Korean default setting: Korean sedan footwell layout, left-hand drive pedal arrangement.
Text handling: the pedals, mat and every surface are unmarked and blank — no letters, no logos, no numbers; avoid incidental text through framing and cropping. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the car floor mat) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
자동차 운전석 가속 브레이크 페달
```

### [카드 5]
**텍스트**
```text
사람이 페달을 밟았고 멈추지 못했다
그걸 차가 대신 막는 장치가 있다
멈춰 선 차의 앞뒤 1~1.5m 범위에서
*장애물을 감지하면 출력을 눌러 버린다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the narrow band of empty air between the car's front bumper and the concrete pillar standing just ahead of it. Recurring location — the plaza in front of a large glass-walled office and shopping complex in Yeouido, Seoul, with a freestanding vertical signage pillar near a downhill parking garage exit ramp. A stopped sedan rests at the top of the exit ramp with its bumper squared toward the pillar, and a thin luminous arc is drawn across the pavement inside that gap, curving from one corner of the bumper to the other as if the car were measuring the distance itself. Through the open side window a driver's hands rest on the steering wheel, visible only from the wrists down.
Camera: medium close-up from a high angle, shot on 50mm standard lens
Lighting/mood: flat cold even surveillance light, no shadow no warmth, detached and watchful
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) forming the luminous arc on the pavement, muted daylight contrast
Korean default setting: Korean urban street conventions, left-hand drive, Korean parking ramp markings.
Text handling: the pillar, ramp surface and car body are blank — no letters, no logos, no license plate digits, no measurement labels; the arc is a pure shape of light, not a diagram with numbers. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the ramp pavement) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
- no technical diagram, no measurement arrows, no dimension lines, no HUD graphics
```
**검색어**
```text
페달 오조작 방지장치 주차장 출구
```

### [카드 6]
**텍스트**
```text
지워진 게 자율주행이라면, 남는 건
자동차만큼 오래된 위험이다
그걸 막는 장치의 의무 장착일은
*2029년 1월 1일, 새로 만드는 차부터다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a long line of cars halted at a signal, every one of them the same dull grey except a single vehicle whose outline still glows. Rows of ordinary sedans and vans stand bumper to bumper across a wide city avenue in the blue hour just after sunset, all facing the camera head on, their drivers reduced to dim silhouettes behind windshields. The avenue recedes toward high-rise towers until the cars shrink into small dots, and nothing in the line moves.
Camera: extreme long shot from eye-level, front-on, shot on 200mm telephoto lens
Lighting/mood: cold blue evening tone, lone streetlight reflection on the damp asphalt, desolate stillness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) picking out the rim light of exactly one car in the line, film-noir low-key lighting, deep shadows
Korean default setting: Korean urban street conventions, left-hand drive, Korean lane markings and traffic signal shapes.
Text handling: all signage, storefronts and license plates are blank — no letters, no logos, no numbers; avoid incidental text through framing and cropping. no garbled or fake script, no meaningless letters, no random characters, no dense text.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the road asphalt) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
서울 도심 대로 차량 정체 저녁
```
