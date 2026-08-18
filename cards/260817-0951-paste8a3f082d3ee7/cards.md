# 대피하라는 문자는 두 시간 전에 갔다

**[프롬프트 설계]**
- 화풍: A 수채화 — 사망자가 나온 재난이라 극화의 고발 톤으로 참사를 키우지 않고, 번짐과 파스텔로 새벽의 한기와 절제된 슬픔만 남긴다.
- 분위기: 서늘한 무력감. 비명이 아니라 정적 — 알림은 울렸는데 아무 일도 일어나지 않은 두 시간의 공기.
- 연출 방향: 독자를 멈추게 하는 건 "비탈 아래 1층에 사는 나", "새벽에 재난문자 진동을 느끼고 그냥 다시 누워본 나"다. 그래서 카메라는 무너진 현장보다 **문자를 받은 사람의 자리**에 오래 머문다 — 어둠 속에서 얼굴을 아래에서 비추는 폰 화면 빛, 문턱을 넘지 못한 발, 문틀을 쥔 손끝. 시사점(경보는 시 전체로 내려오고 무너지는 건 비탈 하나다)은 두 개의 표면을 맞세워 전한다: 빛나는 작은 화면과 흙에 잠긴 창. 피해자·유가족·단지 실명은 화면에 두지 않고, 붕괴의 순간이 아니라 그 직전과 직후만 그린다. thumb_dispatch의 차가운 새벽 색조와 부재의 정조를 전 카드의 색 키노트로 이어받되, 앵글은 카드마다 흩는다.
- 독자 동선: **발단** 카드1→**전개** 카드2~3→**피크** 카드4→**해소** 카드5→**시사점** 카드6 · 훅=카드1 끝(예고형 — 시각을 박고 "문자가 갔다"로 끊어 다음 장이 그 문자를 연다)+카드3 끝(단서형 — 나갈 길이 막혔다는 사실만 남기고 절단)+카드5 끝(단서형 — 대피 숫자가 전부 사고 뒤였다는 시차) · 착지 한 줄 요지 = 문자는 도착했고 1층은 묻혔다.
- 연속성 앵커: Recurring subject — a Korean man in his 30s with short black hair, wearing a loose gray T-shirt and dark cotton pajama pants (카드2·3·6에 동일 문자열 복사) / 반복 장소 = a ground-floor unit of a low-rise Korean apartment block at the foot of a wooded slope.

### [카드 1]
**텍스트**
```text
거제에 15일부터 782.5mm가 쏟아졌다.
그중 400mm가 16일 밤에 몰렸다.
한 시간에만 124.5mm가 내렸다.
*8월 17일 새벽 2시 10분, 문자가 갔다.*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: one small human silhouette standing motionless behind the only lit low window, shoulders squared, watching the rain. A steep dark wooded slope towers directly behind a low residential building, and dense diagonal rain sheets across the whole frame. Runoff pours down the slope and pools on the asphalt below, catching a single streetlight. Every other window is dark and no one is outside. The lit window sits just above the center of the frame with the slope massed above it, and the runoff makes a leading line toward the right edge.
Camera: wide shot from a low angle looking up the slope, shot on 20mm wide lens
Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground, desolate stillness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by the wet streetlight reflection on the asphalt, film-noir low-key lighting, deep shadows
Korean setting by default: Korean low-rise apartment block proportions, Korean street lamp and road markings, Korean guardrail forms.
Text handling: keep every surface free of writing; no signage, no building numbers, no plates rendered anywhere.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the black rain-filled night sky) extending edge to edge from top to bottom of the frame behind everything else. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 폭우 산비탈 주택
```

### [카드 2]
**텍스트**
```text
거제시가 전 시민에게 보낸 문자였다.
산사태 경보도 같은 시각 전역에 걸렸다.
산사태보다 두 시간 남짓 빨랐다.
*경보가 늦어서 생긴 일이 아니었다.*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: his half-awake eyes lit from below by the phone glow, pupils tightening as they read. Recurring subject - a Korean man in his 30s with short black hair, wearing a loose gray T-shirt and dark cotton pajama pants - has pushed himself halfway upright on the edge of a low bed and holds the phone in both hands near his chest. The screen is angled away from the camera so nothing on it is legible, only its cold light spilling across his face and forearms. Behind him one flat bedroom wall and a closed window streaked with rain.
Camera: medium shot from eye level, three-quarter angle, shot on 50mm standard lens
Lighting/mood: cold blue screen under-glow lighting the face from below in a dark room, restless paranoid unease
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by the rim of light along his jaw and hands, film-noir low-key lighting, deep shadows
Korean setting by default: Korean apartment bedroom proportions, floor-level bedding and a low wooden frame.
Text handling: the phone screen faces away and stays unreadable; no writing on the wall, no labels, no numbers rendered anywhere.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the dark bedroom wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
재난문자 휴대폰 화면
```

### [카드 3]
**텍스트**
```text
대피하라고는 했다. "안전한 지역으로."
*어디가 안전한지는 적혀 있지 않았다.*
거제는 주요 도로와 터미널이 잠겼고
경남 204곳이 통제돼 버스도 끊겼다.
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: his hand still gripping the edge of the entrance wall beside him, knuckles pale, his bare feet stopped on the last dry patch of concrete. Recurring subject - a Korean man in his 30s with short black hair, wearing a loose gray T-shirt and dark cotton pajama pants - stands with his back to the camera under a bare entrance lamp, facing out toward the right side of the frame with the phone hanging in his other hand. Ahead of him the narrow alley is flooded ankle-deep, rain hammering the black water, and nothing beyond the small pool of lamplight is visible. Nose room on the right, his gaze directed toward the right edge.
Camera: cowboy shot from eye level, back view, shot on 24mm wide lens
Lighting/mood: single pool of hard light isolating the figure in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by the lamp reflection on the flooded surface, film-noir low-key lighting, deep shadows
Korean setting by default: Korean low-rise apartment entrance step, Korean alley curb and drain grate, Korean utility pole silhouette.
Text handling: the phone screen is dark and turned away; no shop signage, no unit numbers, no notices rendered anywhere.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the wet concrete ground running unbroken from the entrance step out into the flooded alley) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 도로 침수
```

### [카드 4]
**텍스트**
```text
그로부터 두 시간 뒤, 새벽 4시 반이었다.
옥포동 뒷산이 104동 1층을 덮쳤다.
*구조된 20대 남성은 병원에서 숨졌다.*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a rescuer's gloved fingers pressed deep into the wet soil, spread wide and searching. Only that hand and forearm enter the frame; the rest of the body stays out of view. The packed mud rises against a half-buried ground-floor window frame with a snapped branch lying across it, and one flashlight beam rakes sideways over the soil surface. No victim is shown, no injury is shown, no blood is shown.
Camera: extreme close-up from a high angle, shot on 100mm macro lens
Lighting/mood: single hard side-light cutting across the subject, deep chiaroscuro shadows, tense atmosphere
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by the reflective strip on the glove cuff, film-noir low-key lighting, deep shadows
Korean setting by default: Korean apartment window frame proportions, Korean rescue glove and sleeve forms.
Text handling: no unit numbers, no equipment lettering, no markings rendered on the glove or the window frame.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the mud-covered ground) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
옥포동 산사태 구조
```

### [카드 5]
**텍스트**
```text
옆집 50대 여성은 왼팔이 부러졌다.
새벽 5시 6분 통영에서도 산사태가 났다.
*통영의 주의보는 두 시간 뒤에 나왔다.*
84가구 115명 대피도 사고 난 뒤였다.
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the wide empty gaps between the scattered sleeping mats, families sitting apart and not speaking. Seen from directly overhead, about twenty evacuated residents of mixed ages are spread across a school gymnasium floor on thin mats and folded blankets. A middle-aged woman with her forearm in a sling sits near the front, an elderly couple sits at the far edge, several people face the wall, and packed bags and shoes are lined beside each mat. The right side of the floor is still empty and waiting.
Camera: wide shot from a bird's-eye view, shot on 35mm classic wide lens
Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by one folded emergency blanket among the mats, muted daylight contrast
Korean setting by default: Korean school gymnasium floor lines and wall padding, Korean relief mat and blanket forms.
Text handling: no floor markings that read as words, no banners, no notices, no numbers rendered anywhere.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the gymnasium floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
이재민 임시대피소 체육관
```

### [카드 6]
**텍스트**
```text
경보는 시 전체로 내려오지만
무너지는 건 비탈 하나다.
전 시민이 같은 문장을 받은 그 새벽,
*문자는 도착했고 1층은 묻혔다.*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: his eyes through the window glass, looking straight out and slightly down, the phone lowered and forgotten in his hand. Recurring subject - a Korean man in his 30s with short black hair, wearing a loose gray T-shirt and dark cotton pajama pants - stands just inside a ground-floor window seen from outside, one palm flat against the glass. A dried band of mud marks the wall below the sill and the wet wooded slope rises out of focus above the roofline. The rain has stopped. The window opening extends past the left and top edges of the composition so no complete rectangle is enclosed.
Camera: medium shot from eye level, front-on, shot on 85mm portrait lens
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02) carried only by a thin morning glint along the wet sill, muted daylight contrast
Korean setting by default: Korean low-rise apartment wall texture and window proportions, Korean sill and drain forms.
Text handling: no unit numbers, no building plates, no notices, no writing rendered on the wall or the glass.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the apartment building exterior wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
거제 옥포동 저층 아파트
```
