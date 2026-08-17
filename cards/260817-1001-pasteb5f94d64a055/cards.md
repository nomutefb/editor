# 도크는 잠겼고, 그는 집에서 숨졌다

**[프롬프트 설계]**
- 화풍: A 한국웹툰 수채화 — 사람이 숨진 재난이라 극화의 날선 선으로 참사를 키우지 않고, 젖은 공기와 남은 자리를 물감 번짐으로 담는다
- 분위기: 비에 절어 소리가 죽은 새벽 한색 정조. 급박한 재난 화면이 아니라, 이미 지나간 자리의 무거운 정적(thumb_dispatch의 차가운 새벽광·부재 정조를 조명 톤과 거리감으로 계승)
- 연출 방향: 뉴스 안 보는 독자가 멈추는 자리는 "회사는 오늘 나오지 말라고 정해주는데, 집은 아무도 정해주지 않는다"는 서늘함이다. 그래서 화면은 사람의 얼굴이 아니라 **경계 두 개**를 잡는다 — 물에 잠긴 도크(회사 안쪽)와 흙이 닿은 1층 창(집). 같은 비를 맞은 두 표면을 덱 전체가 번갈아 보여주다가 마지막에 한 화면에 같이 세운다. 피해는 흔적과 구조 인력으로만 그리고, 피해자·아파트 이름·기업 로고는 화면에 두지 않는다
- 독자 동선: **발단** 카드1→**전개** 카드2~3→**피크** 카드4→**해소** 카드5~6→**시사점** 카드7 · 훅=카드1 끝(예고형: 그 밤이 새벽 4시 반으로 넘어감)+카드3 끝(단서형: 특근 취소) · 착지 한 줄 요지 = 하루를 멈추라고 정해준 곳이 공장에는 있었고 그의 집에는 없었다
- 연속성 앵커: 인물 (없음) — 피해자 비식별과 부재 연출을 위해 반복 인물을 두지 않는다 / 장소 A(카드 2·4·7): `Recurring location - a plain pale-concrete low-rise apartment block standing directly beneath a steep wooded slope in a rainy Korean coastal shipbuilding town.` / 장소 B(카드 3·7): `Recurring background - distant shipyard gantry cranes standing in the rain.`

### [카드 1]
**텍스트**
```text
*거제에 사흘 동안 805.6㎜가 내렸다*
그중 400㎜ 넘게 마지막 밤에 몰렸다
흙은 이틀 내내 물을 먹고 있었다
그 밤이 새벽 4시 반으로 넘어갔다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the saturated hillside soil, dark and swollen after three days of rain, thin threads of muddy runoff slipping down its face. Recurring location - a plain pale-concrete low-rise apartment block standing directly beneath a steep wooded slope in a rainy Korean coastal shipbuilding town. Rain falls in unbroken vertical strokes across the whole frame and the streets below the block have begun to hold standing water. No people are outside, and a single green protective tarp pinned over one bare patch of the slope is the only saturated color in the frame. The composition leads the eye toward the right edge.
Camera: establishing wide shot from a high angle looking down, shot on 24mm wide lens
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood, heavy rain haze
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by the protective tarp on the slope, muted daylight contrast
Korean setting by default: Korean coastal city architecture, Korean low-rise apartment forms, Korean road markings and signage shapes with no readable letters.
Text handling: avoid incidental writing - no shop signs, no banners, no building nameplates, no logos, keep every surface free of lettering.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the rain-soaked hillside terrain) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 집중호우 도심
```

### [카드 2]
**텍스트**
```text
8월 17일 새벽, 거제 옥포동에서
비탈이 무너져 아파트 1층을 덮쳤다
*그 집에서 구조된 20대 남성이 숨졌고*
50대 여성 등 2명이 다쳤다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a rescue worker's gloved hands sunk into wet soil at the base of a ground-floor window, working steadily and without pause. Recurring location - a plain pale-concrete low-rise apartment block standing directly beneath a steep wooded slope in a rainy Korean coastal shipbuilding town. A tongue of collapsed earth and broken branches has poured across the ground floor and buried the lower windows to half their height. Three rescue workers in helmets and rain gear, seen from behind at a respectful distance, dig and pass debris backward, and no injured person is visible anywhere in the frame. Rain is still falling and their headlamps cut small cones through the blue dark.
Camera: wide shot from eye-level, shot on 35mm lens
Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground, desolate stillness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by the reflective strips on the rescue workers gear, film-noir low-key lighting, deep shadows
Korean setting by default: Korean low-rise apartment exterior, Korean fire and rescue uniform silhouettes with no emblems, Korean street forms with no readable letters.
Text handling: avoid incidental writing - no unit numbers, no building nameplates, no vehicle markings, no agency emblems, no logos, keep every surface free of lettering.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the mud-covered ground) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no injured body, no visible victim, no blood, no wounds, no covered body, no stretcher with a person on it
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
옥포동 산사태 아파트
```

### [카드 3]
**텍스트**
```text
숨진 남성의 신원이 경찰에서 확인됐다
*그는 삼성중공업 조선소 근로자였다*
같은 날 그 회사도 비를 맞고 있었다
도크 일부가 잠겼고, 특근은 취소됐다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the flat brown waterline standing where a dry dock floor should be, swallowing the lowest rungs of a work ladder. Recurring background - distant shipyard gantry cranes standing in the rain. Seen from far above, a large rectangular dry dock is flooded into one sheet of still water and rain stipples its whole surface. The yard is completely empty of workers and moving vehicles, with coiled mooring ropes left on the quay, a row of empty bicycle racks and a shuttered gate at the yard entrance. Scaffolding and hull blocks stand motionless around the basin, and the composition leads the eye toward the right edge.
Camera: extreme long shot from a bird's-eye overhead angle, shot on 20mm wide lens
Lighting/mood: flat cold even surveillance light, no shadow no warmth, detached and watchful, rain haze over the basin
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by one coiled mooring rope on the quay, muted low-contrast daylight
Korean setting by default: Korean shipyard layout, Korean industrial structures, no readable letters on any hull, crane or gate.
Text handling: avoid incidental writing - no company names, no hull markings, no safety signage text, no logos, keep every surface free of lettering.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the flooded dock water surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제조선소 도크 침수
```

### [카드 4]
**텍스트**
```text
*회사는 조선소 문을 닫을 수 있었다*
집 뒤 비탈은 닫아줄 수 없었다
그가 잠든 자리가 그 비탈 아래였다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the exact seam where wet soil presses flat against the glass of a ground-floor window, with a pale curtain hanging undisturbed on the inside. Recurring location - a plain pale-concrete low-rise apartment block standing directly beneath a steep wooded slope in a rainy Korean coastal shipbuilding town. The frame is filled by that single window and the earth banked against it, with grit, a snapped twig and one leaf caught in the wet film on the pane. Far above and out of focus, the dark mass of the wooded slope leans over the building. No people are in the frame.
Camera: tight close-up from a ground-level worm's-eye angle, shot on 100mm macro lens
Lighting/mood: cold blue dim light, heavy and suffocating, faint trembling tension, the deepest shadows and highest contrast of the whole sequence
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by a small potted plant just visible behind the glass, film-noir low-key lighting, deep shadows
Korean setting by default: Korean apartment window frame proportions, Korean domestic curtain and sill details, no readable letters anywhere.
Text handling: avoid incidental writing - no unit numbers, no stickers, no notices on the glass, no logos, keep every surface free of lettering.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the mud-smeared exterior wall and window plane) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no person visible inside or outside the window, no silhouette of a sleeping figure, no blood, no injury
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
산사태 토사 창문
```

### [카드 5]
**텍스트**
```text
그렇다고 아무도 몰랐던 건 아니다
경남도는 전날 낮 비상을 2단계로 올렸다
위험한 비탈을 더 살피겠다고 밝혔다
*사고는 그로부터 약 15시간 뒤에 났다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a row of officials leaning the same way toward a wall of weather displays, one hand hovering just above a paper checklist. Seen from directly overhead, eight or nine staff in identical work vests sit at long parallel desks in a windowless operations room. Their heads are all turned toward large screens that show only abstract radar color blobs and contour shapes with no letters or numbers on them. Phones, folded maps and paper cups cover the desks, and the room is orderly with nobody standing up.
Camera: group shot from a bird's-eye overhead angle, shot on 24mm wide lens
Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by the reflective piping on the work vests, muted low-contrast interior light
Korean setting by default: Korean public agency operations room layout, Korean administrative work vest silhouettes with no emblems.
Text handling: avoid incidental writing - no agency names, no screen labels, no document text, no wall signage, no logos, keep every surface free of lettering.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the operations room floor and desk plane) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
경남도 재난안전대책본부 상황실
```

### [카드 6]
**텍스트**
```text
시민에게 간 건 새벽 2시 10분 문자였다
*안전한 지역으로 대피해달라고 했다*
그런데 그날 아침 6시 반 기준으로
거제 도로 26곳은 차가 다닐 수 없었다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a resident halted at the very edge of the water outside an apartment entrance, phone held low in one hand, its glow catching the underside of the face while the eyes stay fixed on the flooded street ahead. One Korean adult in a jacket thrown over sleepwear, generic and mostly backlit, stands a single step above the waterline and does not come down. The street in front has become one unbroken brown sheet of water, with a plastic traffic barrier and a toppled cone leaning in it and a car sitting submerged to its door handles. Rain dimples the whole surface and the far end of the street disappears into blue dark.
Camera: medium shot from eye-level, shot on 35mm lens
Lighting/mood: cold blue screen under-glow lighting the face from below, restless unease, cold pre-dawn light on the water beyond
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by the reflective band on the traffic barrier, film-noir low-key lighting, deep shadows
Korean setting by default: Korean apartment entrance form, Korean street furniture and traffic barrier shapes, Korean road markings with no readable letters.
Text handling: avoid incidental writing - no phone screen text, no shop signs, no barrier lettering, no license plates, no logos, keep every surface free of lettering.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the flooded street water surface) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no readable phone interface, no notification popup rendered, no recognizable real person, no distressed crowd
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 도로 침수
```

### [카드 7]
**텍스트**
```text
경보도 올라가 있었고 문자도 갔다
없었던 건 어디로 가라는 말이었다
그날 하루를 멈추라고 정해준 곳은
*공장에는 있었고, 그의 집에는 없었다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the drying line of mud across the base of the apartment block, sharp as a tide mark, with the first warm light of morning touching only the wall above it. Recurring location - a plain pale-concrete low-rise apartment block standing directly beneath a steep wooded slope in a rainy Korean coastal shipbuilding town. Recurring background - distant shipyard gantry cranes standing in the rain. The rain has thinned to drizzle, the wooded slope behind the block is dark and scarred where the earth gave way, and far beyond the rooftops the gantry cranes stand motionless against a pale sky. The ground is wet and empty, holding shallow reflections, no one is in the frame, and the composition is centered and still.
Camera: wide shot from a slightly high angle, shot on 35mm lens
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy, the sequence releasing after its darkest point
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by the protective tarp still pinned on the scarred slope, muted daylight contrast
Korean setting by default: Korean coastal shipbuilding town skyline, Korean low-rise apartment forms, Korean street shapes with no readable letters.
Text handling: avoid incidental writing - no building nameplates, no crane markings, no company names, no signage, no logos, keep every surface free of lettering.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the rain-soaked ground of the residential block) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image, minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
옥포 조선소 전경
```
