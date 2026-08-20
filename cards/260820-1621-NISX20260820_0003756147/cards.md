# 청와대 서버는 멀쩡한데, 청와대 인사 정보가 샜다

**[프롬프트 설계]**
- 화풍: B 극화 — 인증·위탁 사슬이라는 구조를 고발하는 사건이라 무게가 필요하고, 한국 웹툰의 굵은 선과 스크린톤이 기관·서버라는 딱딱한 소재를 친숙하게 잡아준다
- 분위기: 소리 없이 지나간 침해. 기관의 조명은 끝까지 무정하고 사람 쪽만 점점 어두워지는, 그 낙차의 정조
- 연출 방향: 뉴스를 안 보는 독자도 '내 이름과 번호가 내가 고른 적 없는 회사에서 새어 나갔고 확인할 방법이 없다'는 감각으로 멈춰 서게 한다(독자훅=무력감). 전할 관점은 본체가 아니라 본체를 아는 곳이 뚫린다는 구조, 그리고 범위 공개가 늦어질수록 유리해지는 쪽이 누구냐는 것. 그래서 카메라는 거대한 시스템(랙·단상·로비)과 손바닥만 한 사물(명함 한 장·화면 위 한 줄·꺼진 폰)을 번갈아 잡되, 강조점은 늘 후자에 둔다 — 사건의 무게가 큰 쪽이 아니라 작은 쪽에 실려 있기 때문이다. thumb_dispatch에서 무정한 기관 형광의 색온도와 '감시당하는 줄 모르는 거리감'만 이어받아 전 카드의 색·정조로 깐다
- 독자 동선: **발단** 카드1→**전개** 카드2~3→**피크** 카드4→**해소** 카드5~6→**시사점** 카드7 · 훅=카드1 끝(단서형: 명단의 주인을 유보)+카드3 끝(예고형: 왜 안심이 아닌지)+카드5 끝(예고형: 알려진 범위의 끝) · 질문형 0회 · 착지=배후 규명과 범위 공개는 속도가 다르고, 늦어질수록 시간을 버는 쪽은 그 명단을 이미 쥔 쪽이다
- 연속성 앵커: Recurring subject — a Korean man in his 40s with short side-parted hair and rimless glasses, wearing a pale blue dress shirt with the collar unbuttoned and a loosened dark tie. / Recurring place — a late-night Korean open-plan office floor with rows of empty desks and half-drawn blinds.

### [카드 1]
**텍스트**
```text
민간 인증기관 서버가 해커에게 뚫렸다
경찰이 8월 20일 빠져나간 자료를 열자
이름과 휴대전화 번호가 적혀 있었다
*그 명단은 국내 주요 인물의 것이었다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the investigator's narrowed eyes catching the blinking indicator lights above him. A lone Korean forensic investigator in a plain zip-up jacket and thin gloves stands small at the bottom of the frame, tilting his head up along a towering row of server cabinets that fills the wall in front of him. His right hand rests on one cabinet door hanging half open at his shoulder while rows of port lights blink down the dark aisle above, and his gaze runs up and toward the right edge of the frame. The place is a windowless Korean data center aisle, anonymous and unbranded, with nose room on the right.
Camera: wide shot with full body and spatial context, from a low angle looking up for dominance and dramatic presence, shot on a 14mm ultra-wide lens with vast environment and dramatic depth
Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the server indicator lights), muted daylight contrast
Korean default: Korean people and a Korean data center interior, no institutional logos or emblems, plain unbranded work clothing.
Text handling: no readable labels on the cabinets; any markings are cropped out of frame or thrown far out of focus.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the row of server cabinets forming one unbroken metal wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
데이터센터 서버랙 점검
```

### [카드 2]
**텍스트**
```text
적힌 건 명함에 들어가는 수준이었다
이름과 휴대전화 번호, 주소였다
누구나 건네고 받는 종이 한 장이다
*그 명함 가운데 청와대 인사가 있었다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: his fingertips stopping on one card in the middle of the spread. Recurring subject — a Korean man in his 40s with short side-parted hair and rimless glasses, wearing a pale blue dress shirt with the collar unbuttoned and a loosened dark tie. He sits at his desk and looks straight down at dozens of business cards fanned across the desktop, lifting one card a few millimetres between two fingers while his eyes stay locked on it. Recurring place — a late-night Korean open-plan office floor with rows of empty desks and half-drawn blinds, the monitor beside him the only thing still switched on, its glow washing up under his face.
Camera: medium shot with waist-up framing and hands clearly visible, from a high angle looking down across the desk, shot on a 50mm standard lens with minimal distortion and natural cinematic composition
Lighting/mood: cold blue screen under-glow lighting the face from below in a dark room, restless paranoid unease
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the single lifted card's edge), film-noir low-key lighting, deep shadows
Korean default: Korean people and a Korean office interior, no institutional logos or emblems, unbranded plain stationery.
Text handling: the cards are blank or shown at an angle so no lettering is legible; the lifted card is cropped by his fingers.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the desk top) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
명함첩 명함 정리
```

### [카드 3]
**텍스트**
```text
경찰이 먼저 내놓은 말은 선긋기였다
청와대 서버는 뚫린 적이 없다는 것이다
그 업체도 대통령실과 무관하다고 했다
*둘 다 사실이지만 안심할 말은 아니다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the flat, unmoving mouth of the official at the podium as he speaks. A Korean police official in a plain dark suit stands behind a bare podium at the top of the frame, one palm laid flat on the lectern in a cutting-off gesture, his chin level and his gaze aimed past the reporters toward the right edge. Below him the backs and shoulders of several seated reporters fill the foreground, small and dark, a cluster of microphones angled up at him. The place is a Korean briefing room with a plain fabric backdrop wall rising behind the podium, nose room on the right.
Camera: group shot with multiple subjects in clear arrangement and hierarchy, from a low angle looking up at the podium, shot on a 35mm lens with natural documentary perspective and minimal distortion
Lighting/mood: harsh single overhead light pooling on the lectern, deep surrounding black, oppressive interrogation
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on a single recording light in the microphone cluster), film-noir low-key lighting, deep shadows
Korean default: Korean people and a Korean government briefing room, no institutional logos or emblems, no agency crest on the backdrop, unbranded microphones.
Text handling: the backdrop is a plain unprinted fabric; any lettering is cropped out of frame by the podium edge.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the plain backdrop wall behind the podium) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
경찰청 국가수사본부 브리핑
```

### [카드 4]
**텍스트**
```text
인증기관은 신원을 확인해 주는 자리다
뚫린 곳은 본체가 아니라
*본체를 아는 곳이었다*
명단 한 장이 표적을 고르는 지도가 된다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a pair of eyes mirrored on the glass, unfocused in a vacant thousand-yard stare. Recurring subject — a Korean man in his 40s with short side-parted hair and rimless glasses, wearing a pale blue dress shirt with the collar unbuttoned and a loosened dark tie, present only as a faint reflection floating across the screen. The whole frame is filled by the surface of one monitor screen showing stacked rows of blurred, unreadable entries, with a single row held under a sharp highlight bar and a cursor stopped hard at its left edge. Nothing else exists in the frame but that screen surface and the reflection lying over it.
Camera: extreme close-up on a single detail filling the frame, from eye level with a neutral perspective, shot on a 100mm macro lens with fine detail, precise texture and shallow depth of field
Lighting/mood: single pool of hard light isolating the subject in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the highlight bar and the cursor), film-noir low-key lighting, deep shadows
Korean default: a Korean office monitor, no institutional logos or emblems, no brand marks on the bezel.
Text handling: every row of entries is rendered as soft illegible blur with no formed letters; only the highlight bar and cursor are sharp.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the monitor screen glass) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
개인정보 명단 모니터 화면
```

### [카드 5]
**텍스트**
```text
털린 곳은 이 회사 하나가 아니었다
언론사 서버 관리업체와 제약사, 병원이
국가 배후 조직에 뚫려 수사 중이다
*그런데 정작 알려진 건 여기까지다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the lone night-shift worker's slack shoulders as she keeps her eyes on a screen she is not really reading. A single Korean woman in her 30s in plain scrubs sits alone behind a curved reception counter in the middle of a deserted hospital lobby, her face lit from the front by a monitor, her body turned slightly toward the right edge of the frame. Far behind her at the end of the corridor a metal server cabinet stands with its door swung open, cables spilling from it onto the polished floor. The place is a Korean hospital lobby after midnight, empty chairs in even rows, nose room on the right.
Camera: wide shot showing the full environment and spatial context, from a high angle looking down on the lobby, shot on a 24mm wide lens with cinematic depth
Lighting/mood: eerie sickly-green light, unsettling toxic cast, creeping dread
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the open server cabinet's status lights), film-noir low-key lighting, deep shadows
Korean default: Korean people and a Korean hospital interior, no institutional logos or emblems, unbranded plain scrubs and unmarked signage.
Text handling: all wayfinding signs are shown edge-on or blurred so no lettering is legible.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the polished hospital lobby floor) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
병원 야간 접수데스크
```

### [카드 6]
**텍스트**
```text
부산경찰청이 규모와 경로를 쫓고 있다
어느 기관인지, 몇 명인지, 언제인지
아직 아무것도 나오지 않았다
*명단에 오른 사람도 알 길이 없다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: his thumb hovering just above the phone screen without pressing anything. Recurring subject — a Korean man in his 40s with short side-parted hair and rimless glasses, wearing a pale blue dress shirt with the collar unbuttoned and a loosened dark tie. He sits alone holding the phone low in both hands, eyes cast down at it, shoulders pulled inward and jaw set. Recurring place — a late-night Korean open-plan office floor with rows of empty desks and half-drawn blinds, and on the wall behind him a muted display shows an indistinct press briefing reduced to a blurred standing figure.
Camera: close-up with the face centered on the eyes and expression, from eye level with a neutral realistic perspective, shot on an 85mm portrait lens with soft background separation
Lighting/mood: cold blue dim interior light, heavy and suffocating, faint trembling tension
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on a lone notification dot on the phone), film-noir low-key lighting, deep shadows
Korean default: Korean people and a Korean office interior, no institutional logos or emblems, unbranded devices.
Text handling: the phone screen and the wall display are shown at a steep angle and heavily blurred so nothing is legible.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the office wall behind him) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
야근 사무실 스마트폰
```

### [카드 7]
**텍스트**
```text
배후를 밝히는 데는 오래 걸린다
누가 명단에 올랐는지 알리는 건 다르다
알려 주는 일이 늦어질수록
*시간을 버는 쪽은 명단을 쥔 쪽이다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: his steady, exhausted eyes looking straight into the lens without blinking. Recurring subject — a Korean man in his 40s with short side-parted hair and rimless glasses, wearing a pale blue dress shirt with the collar unbuttoned and a loosened dark tie. He stands centered and square to the camera, the dark phone hanging loose in one hand at his side, the other hand open and empty, chin level. Recurring place — a late-night Korean open-plan office floor with rows of empty desks and half-drawn blinds, now rimmed with cold pre-dawn light coming through the slats behind him, one server tower still awake in the far corner.
Camera: full shot head-to-toe with a clear silhouette, front-on with a direct gaze and symmetrical composition at eye level, shot on a 40mm lens with a neutral human-vision perspective
Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground outside, desolate stillness
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 on the distant server tower's single lit indicator), film-noir low-key lighting, deep shadows
Korean default: Korean people and a Korean office interior, no institutional logos or emblems, unbranded devices and furniture.
Text handling: no signage or screens face the camera; every surface with markings is turned away or lost in shadow.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the blinded window-wall of the office behind him) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
새벽 오피스 블라인드 창
```
