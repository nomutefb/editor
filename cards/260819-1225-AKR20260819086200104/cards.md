# 집이 남아 있어도 돌아가지 못한다

**[프롬프트 설계]**
- 화풍: A 한국웹툰 수채화 — 규탄할 가해자가 있는 사건이 아니라 대피와 기다림의 시간이 축이라, 부드러운 번짐이 인물을 지키면서 정서를 옮긴다
- 분위기: 새벽의 푸른 정적에서 시작해 낮의 무력한 확산광을 지나 한밤의 고립으로 떨어졌다가 이튿날 아침빛으로 풀리는 흐름. thumb_dispatch의 차가운 여명 톤(LGT02)과 '부재'의 정조(SG-09)를 조명·거리감으로만 이어받는다
- 연출 방향: 독자가 멈추는 지점은 사망자 숫자가 아니라 *멀쩡히 서 있는 집과 그 앞 천막 사이의 거리*다. 그래서 카메라는 무너진 것이 아니라 **닫힌 문·비어 있는 마당·흔들리는 물컵**을 본다. #재난참사 안전 시각화에 따라 시신·부상·식별 가능한 얼굴은 전 카드에서 배제하고, 사람은 뒷모습·옆모습·손끝으로만 등장시켜 감정을 자세와 거리로 옮긴다. 악센트는 구호 방수천의 파란색 한 점으로 전 카드를 묶는다
- 독자 동선: **발단** 카드1→**전개** 카드2~4→**피크** 카드5→**해소** 카드6→**시사점** 카드7 · 훅=카드1 끝(단서형 — 17만 명이 숨진 나라라는 배경이 이번 규모를 묻게 만든다, 카드2가 즉시 숫자로 회수)+카드3 끝(단서형 — 맞지 않는 숫자, 카드4가 즉시 회수) · 착지 = 사망자는 1992년보다 훨씬 적지만 4만 명에게 지진은 아직 끝나지 않았다
- 연속성 앵커: `Recurring subject — an Indonesian woman in her 40s, hair tied back in a low bun, wearing a faded floral batik blouse and a long dark skirt, always seen from behind or in profile with her face never clearly visible.` (카드2·4·5·7에 동일 문자열 삽입) / 반복 장소 = `the open dirt clearing of a Flores village lined with blue tarpaulin shelters`

### [카드 1]
**텍스트**
```text
인도네시아 플로레스섬, 인구 200만 명
15일 새벽 규모 7.7 지진이 났다
2004년 아체 앞바다 9.1 지진 때
*쓰나미로 17만 명이 숨진 나라다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a single hairline crack threading across the empty dirt lane, the only thing in the village that has moved. Seen from directly overhead before sunrise, rows of low tin-roofed houses stand with every shutter closed and no one outside. A plastic chair lies tipped over in one yard, and the thin fissure runs between two houses and continues toward the right edge of the frame. Not one window is lit.
Camera: establishing shot from a bird's-eye view directly overhead, shot on a 14mm ultra-wide lens
Lighting/mood: cold blue pre-dawn tone, lone streetlight reflection on wet ground, desolate stillness
Accent: monochrome desaturated base with a single color accent, the cold cobalt blue of the pre-dawn sky held as one soft note within the pastel wash, film-noir low-key lighting, deep shadows
Setting note: an Indonesian island village in East Nusa Tenggara, local architecture and vegetation.
Safety: no injuries, no bodies, no blood, no wounds; no identifiable faces.
Text handling: avoid incidental lettering entirely; resolve any signage as shape and shadow only.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the village ground seen from directly above) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Flores village aerial
```

### [카드 2]
**텍스트**
```text
17일 집계는 이재민 1만2천800명
*이틀 만에 그 숫자가 4만 명이 됐다*
사망자는 68명에서 70명이 됐고
부상자는 213명에서 1천100명이다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: a hand stopped above an open paper ledger, the pen tip resting on a line that keeps getting longer. Recurring subject - an Indonesian woman in her 40s, hair tied back in a low bun, wearing a faded floral batik blouse and a long dark skirt, always seen from behind or in profile with her face never clearly visible; she stands at the head of the queue holding a folded blanket and waits. Behind her a short line of villagers, all seen from behind, extends out of the frame. A folding table sits under the eave of a blue tarpaulin shelter, and a relief worker leans over the ledger.
Camera: medium shot from eye level, shot on a 50mm standard lens, minimal distortion, natural cinematic composition
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single color accent, the blue of the relief tarpaulin held as one soft note within the pastel wash, muted daylight contrast
Setting note: an Indonesian island village in East Nusa Tenggara, local clothing and vegetation.
Safety: no injuries, no bodies, no blood, no wounds; every figure anonymous, faces never clearly visible.
Text handling: the ledger page reads as blank paper with pen strokes only; no legible writing anywhere.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the blue tarpaulin wall of the shelter behind the table) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Indonesia earthquake evacuee registration
```

### [카드 3]
**텍스트**
```text
피해를 본 집은 1만2천 채다
집 밖에 나온 사람은 4만 명이다
한 집에 여러 명이 산다 쳐도
*그래도 숫자가 맞지 않는다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the gap itself, a row of houses standing with their doors shut and a crowded field of tarpaulin shelters pitched in front of them. Looking down a sloping village, the roofs are intact and every window is dark while dozens of small tents crowd the open ground below them. A few small distant figures sit on mats between the tents, and none of them are anywhere near the houses. Laundry hangs unmoved on a line strung between two shelter poles, and the cluster of tents drifts toward the right edge with open nose room on the right.
Camera: wide shot from a high angle looking down the slope, shot on a 24mm wide lens, cinematic wide shot with spatial context
Lighting/mood: faded warm light, soft golden haze, gently nostalgic and wistful
Accent: monochrome desaturated base with a single color accent, the blue of the relief tarpaulins held as one soft note within the pastel wash, muted daylight contrast
Setting note: an Indonesian island village in East Nusa Tenggara, local architecture and vegetation.
Safety: no injuries, no bodies, no blood, no wounds; distant figures anonymous, faces never visible.
Text handling: no signage, no lettering on any surface; shapes and shadow only.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the sloping bare ground of the village) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Flores earthquake damaged houses
```

### [카드 4]
**텍스트**
```text
재난관리청이 그 숫자를 설명했다
집이 부서진 사람만 센 게 아니었다
*심리적 충격에 못 돌아간 주민이 있고*
그들까지 합쳐 4만 명이라고 했다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: her fingers resting flat on a blanket she has not unfolded, the small lantern beside her the only warm thing inside the tent. Recurring subject - an Indonesian woman in her 40s, hair tied back in a low bun, wearing a faded floral batik blouse and a long dark skirt, always seen from behind or in profile with her face never clearly visible; she sits upright on a woven mat facing the tent opening. Two other adults lie asleep further back under a shared blanket, kept low and soft so she stays the focus. Through the opening, the dark shape of an undamaged house stands across the clearing.
Camera: medium close-up from behind at eye level, shot on an 85mm portrait lens, soft background separation
Lighting/mood: warm soft desk-lamp light, quiet wistful tone
Accent: monochrome desaturated base with a single color accent, the blue of the tarpaulin wall held as one soft note within the pastel wash, film-noir low-key lighting, deep shadows
Setting note: an Indonesian island village in East Nusa Tenggara, local clothing and household objects.
Safety: no injuries, no bodies, no blood, no wounds; every figure anonymous, faces never clearly visible.
Text handling: no lettering on the tent, the blanket or any object in the frame.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the blue tarpaulin inner wall of the shelter) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Indonesia earthquake tent interior
```

### [카드 5]
**텍스트**
```text
*첫 강진 뒤 여진이 2천100차례 왔다*
그중 70번은 몸으로 느껴졌다
나흘째 그 섬은 계속 흔들리고 있다
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the water in a plastic cup breaking into fine concentric rings, and a knuckle whitening on the mat beside it. Recurring subject - an Indonesian woman in her 40s, hair tied back in a low bun, wearing a faded floral batik blouse and a long dark skirt, always seen from behind or in profile with her face never clearly visible; only her hand enters the frame, pressed flat against the woven mat. The cup, a folded pair of sandals and the weave of the mat fill the rest of the frame at close range. Everything beyond that small circle of light is swallowed by darkness.
Camera: extreme close-up from ground level, shot on a 100mm macro lens, fine detail and shallow depth of field
Lighting/mood: single pool of hard light isolating the subject in surrounding blackness, claustrophobic loneliness
Accent: monochrome desaturated base with a single color accent, the blue of the tarpaulin edge held as one soft note within the pastel wash, film-noir low-key lighting, deep shadows
Setting note: an Indonesian island village in East Nusa Tenggara, local household objects.
Safety: no injuries, no bodies, no blood, no wounds; the figure is anonymous, no face in the frame.
Text handling: no lettering on the cup or any object; plain unmarked surfaces only.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the woven floor mat inside the shelter) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Indonesia aftershock evacuation tent
```

### [카드 6]
**텍스트**
```text
재난관리청이 100t을 보냈고
국가경찰청도 250t을 보탰다
그 350t이 7개 지역으로 갔지만
*구호단체는 식량과 물이 급하다고 한다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: two men's shoulders straining under a sack while the stack behind them already stands taller than they are. Four workers in plain shirts unload rice sacks and water jerricans from a flatbed truck onto pallets covered with blue sheeting, all seen from behind or in profile. Beyond the clearing a narrow unpaved road climbs into the hills and disappears over a ridge. At the far edge of the clearing a woman waits with two empty containers, standing well away from the stack.
Camera: wide shot from eye level, shot on a 35mm lens, natural documentary perspective with balanced subject and background
Lighting/mood: harsh overexposed midday sunlight, hard shadows, oppressive heat
Accent: monochrome desaturated base with a single color accent, the blue of the relief sheeting held as one soft note within the pastel wash, muted daylight contrast
Setting note: an Indonesian island village in East Nusa Tenggara, local clothing and vegetation.
Safety: no injuries, no bodies, no blood, no wounds; every figure anonymous, faces never clearly visible.
Text handling: sacks, crates and the truck carry no printing; plain unmarked surfaces only, no logos.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the bare dirt clearing) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
BNPB Flores aid distribution
```

### [카드 7]
**텍스트**
```text
1992년 이 섬에선 2천500명이 숨졌다
이번엔 단층이 섬 아래서 어긋나
쓰나미가 작았고 사망자는 70명이다
*4만 명에게 지진은 아직 끝나지 않았다*
```
**이미지 프롬프트**
```text
korean manhwa style watercolor illustration, soft watercolor wash with visible brush texture, warm pastel palette (peach, cream, dusty blue), hand-drawn line work with loose ink contours, emotive character expressions, warm ambient lighting
Scene: Emotional focal point: the distance between her and her own front door, measured by the empty yard lying between them. Recurring subject - an Indonesian woman in her 40s, hair tied back in a low bun, wearing a faded floral batik blouse and a long dark skirt, always seen from behind or in profile with her face never clearly visible; here she sits at the mouth of her tent facing the camera with her head lowered so the face stays in shadow. Behind her, across the yard, stands her house with unbroken walls, a shut door and dark windows. A rolled sleeping mat and a kettle rest on the ground beside her.
Camera: medium shot from a front-on angle at eye level, symmetrical composition, shot on a 40mm lens with neutral natural perspective
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: monochrome desaturated base with a single color accent, the blue of the tarpaulin behind her held as one soft note within the pastel wash, muted daylight contrast
Setting note: an Indonesian island village in East Nusa Tenggara, local architecture and clothing.
Safety: no injuries, no bodies, no blood, no wounds; the figure is anonymous, face never clearly visible.
Text handling: no lettering on the house, the tent or any object in the frame.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the dirt yard of the clearing) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE - strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Manggarai earthquake displaced tents
```
