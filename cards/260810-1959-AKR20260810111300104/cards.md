# 14살이 쏜 지 사흘, 이번엔 전직 의원이 청사에서 쐈다

**[프롬프트 설계]**
- 화풍: B 극화 — 총기 참사 두 건과 규제의 구멍을 다루는 고발·구조 비판 축이라 한국 웹툰 극화의 굵은 잉크선·명암 대비가 사건 무게를 견딘다
- 분위기: 대낮의 환한 빛 아래 굳어버린 정적 — 밝은데 안전하지 않다는 감각, 비명 대신 멈춘 표정으로 무게를 내는 절제된 긴장
- 연출 방향: 뉴스를 안 보는 독자도 "저기 지금 어떤 상태냐"를 0.5초에 알아채게, 사건의 강조점을 **총이 아니라 사람의 눈과 손**에 건다(총구·유혈은 화면 밖으로 밀고, 열린 차문·저지선·바닥에 뜬 서류·서명하는 손 같은 남은 자국으로 사건을 복원). 학교 난사 카드는 어른과 빈 운동장만으로 그려 아이들을 화면에 세우지 않는다. 시사점 관점은 "손을 뻗은 자리에 총이 있었다"이므로 덱 전체가 **손과 그 손이 닿는 거리**를 반복 모티프로 공유한다. thumb_dispatch에서 한낮 직사광의 압박감과 '결정적 순간 직전의 동결'만 키노트로 상속
- 독자 동선: 제시 카드1 → **발단** 카드2 → **전개** 카드3 → **피크** 카드4 → **해소** 카드5 → **시사점** 카드6~7 · 훅=카드1 끝(예고형: "사흘 전에도 총성이 울렸다")+카드3 끝(예고형: "그 말이 나온 지 사흘째 아침") · 착지 한 줄 요지 = 규제는 앞으로 쥘 손을 말하는데 이 사흘의 총은 이미 손에 있었다 · 명도 아크 = 起 한낮 직사광 → 承 흐린 확산광·형광 → **轉 카드4 최저 명도·최고 대비(하드 측광)** → 카드5 저조도 유지 → 結 카드7 아침 여운광 릴리즈 · 줄 수 = 轉 카드4만 3줄, 나머지 4줄
- 연속성 앵커: `Recurring subject A — a Thai man in his 60s, stocky, short graying hair, wearing a loose pale short-sleeved shirt and dark trousers`(카드4·5) / `Recurring subject B — a Thai man in his 50s, broad-shouldered, neatly combed black hair, wearing a light beige short-sleeved official shirt`(카드4) / `Recurring place — a low cream-colored Thai provincial government building with a tiled portico and a wide open-air parking forecourt`(카드1·7)

### [카드 1]
**텍스트**
```text
8월 10일 오전 태국 논타부리 청사였다
차에 오르던 남자가 네 발을 맞았다
*쏜 사람은 법을 만들던 자리에 있었다*
사흘 전에도 이 주에서 총성이 울렸다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the stalled, unblinking eyes of a woman clerk who has pressed one hand flat over her own mouth. Recurring place — a low cream-colored Thai provincial government building with a tiled portico and a wide open-air parking forecourt. She and one colleague stand just outside a stretched police tape line, bodies turned toward a dark sedan stopped mid-turn with its driver door hanging open, while four uniformed officers walk the tape around it. Every eyeline in the frame bends across the forecourt to that one open car door, and the composition leaves nose room on the right with her gaze drifting toward the right edge.
Camera: wide shot from a slightly elevated high angle, shot on 24mm wide lens
Lighting/mood: harsh overexposed midday sunlight, hard shadows, oppressive heat
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Keep all lettering out of the frame: no building signage, no banner wording, no plate characters. The taped line and the open door carry the meaning instead of any written word.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the sunlit asphalt forecourt) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Nonthaburi provincial hall shooting police
```

### [카드 2]
**텍스트**
```text
사흘 전 7일에도 같은 주의 학교였다
열네 살이 조부모를 쏘고 학교로 갔다
그날 여덟 명이 숨지고 열넷이 다쳤다
*대부분 열두 살에서 열네 살이었다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a teacher's reddened, unfocused eyes fixed on the empty schoolyard beyond the gate. Three adults stand outside a taped line with heads lowered, one teacher and two parents, while two uniformed officers hold the open gate behind them and a single unclaimed school backpack lies where it fell on the pavement. No children appear anywhere in the frame; the bare yard behind the fence and that one backpack stand in for them.
Camera: medium shot from eye level, shot on 35mm lens
Lighting/mood: overcast diffused daylight, flat soft shadows, muted somber mood
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Keep all lettering out of the frame: no school name board, no banner wording, no writing on the backpack. The empty yard carries the meaning instead of any written word.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the paved street in front of the school gate) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Nonthaburi school shooting Thailand
```

### [카드 3]
**텍스트**
```text
총리는 곧바로 총기 규제를 예고했다
공공장소에서 총기 소지를 단속하고
*공무원 빼고 일반인은 제한하기로 했다*
그 말이 나온 지 사흘째 아침이었다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the pressure in a thumb pinning the corner of a single sheet down onto the lectern. A man in a dark suit stands behind a plain lectern crowded with microphones, chin lifted, eyes aimed just above the lenses massed in front of him, one hand flat on the paper. A dense row of tripod cameras and raised recorders crowds the lower edge of the frame, and a blank fabric backdrop fills the wall behind him. The composition leaves nose room on the right, his gaze angled toward the right edge.
Camera: medium close-up from a low angle, shot on 50mm standard lens
Lighting/mood: flat sterile clinical fluorescent light, cold even greenish-white, emotionless institutional
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Keep all lettering out of the frame: the backdrop is blank fabric, the lectern bears no emblem, the sheet under his thumb shows only faint unreadable ruling. No institutional logo anywhere.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the plain fabric backdrop wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Anutin Charnvirakul press conference gun control
```

### [카드 4]
**텍스트**
```text
전직 의원이 의장에게 다가섰다
*급소를 포함해 네 발이었다*
의장은 병원으로 옮겨졌지만 숨졌다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the half-step of retreat in an older official's widening eyes, and the shadow of a raised arm climbing the wall beside him. Recurring subject A — a Thai man in his 60s, stocky, short graying hair, wearing a loose pale short-sleeved shirt and dark trousers — stands with his back to the camera in the near foreground, one shoulder filling the left edge of the frame. Recurring subject B — a Thai man in his 50s, broad-shouldered, neatly combed black hair, wearing a light beige short-sleeved official shirt — faces him one pace away in a corridor, a folder slipping from his hand with two loose sheets already suspended in the air. No weapon is visible anywhere in the frame; only the cast shadow on the corridor wall and the closing distance between the two men.
Camera: tight close-up over the shoulder at eye level with a Dutch tilt, shot on 85mm portrait lens
Lighting/mood: single hard side-light cutting across the subject, deep chiaroscuro shadows, tense atmosphere
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 or the story's symbolic color), film-noir low-key lighting, deep shadows
Keep all lettering out of the frame: the falling sheets are blank, the corridor bears no door plate and no notice board. No blood, no wound, no impact shown.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the corridor wall) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Nonthaburi PAO president shooting
```

### [카드 5]
**텍스트**
```text
함께 있던 운전기사도 총에 맞았다
용의자는 곧 경찰에 붙잡혔다
*1천100만 밧을 안 갚아 쐈다고 했다*
경찰은 그 주장을 확인하지 않았다
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: the flat, unmoved set of a mouth above two hands folded together on a bare table. Recurring subject A — a Thai man in his 60s, stocky, short graying hair, wearing a loose pale short-sleeved shirt and dark trousers — sits alone at the table with his hands clasped, eyes cast down and away from the two plainclothes investigators whose shoulders and forearms frame the top edge of the frame. A small voice recorder rests on the table between them, angled toward him, the one object the whole scene is arranged around.
Camera: medium shot from a high angle, shot on 50mm standard lens
Lighting/mood: cold blue dim interior light, heavy and suffocating, faint trembling tension
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02 or the story's symbolic color), film-noir low-key lighting, deep shadows
Keep all lettering out of the frame: no case file wording, no wall notice, no badge inscription. The recorder and the folded hands carry the meaning instead of any written word.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the bare tabletop) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
former Thai MP arrested Nonthaburi
```

### [카드 6]
**텍스트**
```text
태국에 풀린 민간 총기는 1천30만정
100명당 15정, 동남아에서 가장 많다
스무 살이면 정신 검진 없이 허가된다
*열네 살은 SNS로 총 쓰는 법을 배웠다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a young man's fingertips resting flat on the form he has just signed, still not lifting. Seen from directly above a shop counter, his two hands hold a pen over a printed sheet while a shopkeeper's hand slides a receipt pad toward him from the far side; beneath the glass counter top the outlines of merchandise stay soft and out of focus. Two more customers wait behind him, only their shoes and long shadows entering the lower edge of the frame.
Camera: close-up from a bird's-eye overhead angle, shot on 100mm macro lens
Lighting/mood: flat cold even surveillance light, no shadow no warmth, detached and watchful
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Keep all lettering out of the frame: the signed sheet shows only faint unreadable ruling and a signature stroke, the receipt pad is blank, no price tag wording, no shop name.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the glass counter top) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Thailand gun shop licence counter
```

### [카드 7]
**텍스트**
```text
열네 살의 손과 전직 의원의 손이었다
닮은 데 없는 둘을 이은 건 총이었다
총리의 규제는 앞으로 쥘 손을 말한다
*이 사흘의 총은 이미 손에 있었다*
```
**이미지 프롬프트**
```text
korean manhwa style serious drama illustration, sharp black ink outlines with varying line weight, precise anatomical rendering, screentone shading, cel-shaded color with defined edges, high contrast chiaroscuro, muted desaturated palette with selective color accents, heavy atmosphere
Scene: Emotional focal point: a tired, level gaze aimed straight into the camera, holding it without blinking. A middle-aged Thai commuter stands centered in the frame facing forward, both hands open and empty at his sides, while behind him the morning traffic of a Nonthaburi street blurs into soft shapes of motorbikes, a food cart and walking figures. Recurring place — a low cream-colored Thai provincial government building with a tiled portico and a wide open-air parking forecourt — sits far back on the horizon behind his shoulder. Nothing is held in his hands and nothing is visible in anyone else's.
Camera: front-on medium shot from a slightly low angle, shot on 35mm lens
Lighting/mood: warm soft morning light, gentle and quiet, faint melancholy
Accent: monochrome desaturated base with a single color accent (neon green #0FFD02), muted daylight contrast
Keep all lettering out of the frame: no street signage, no shop board, no vehicle plate characters. The empty hands and the level stare carry the meaning instead of any written word.
Aspect ratio: 4:5 vertical portrait, full bleed single image filling the entire frame edge to edge with no inner border, no outer frame, no rectangular outline, no white margin around the image.
MANDATORY: This is ONE single seamless illustration on ONE continuous surface. The entire canvas shows ONE continuous scene without any horizontal division, without any line cutting the image, without any frame inside the frame. The whole image is one unified visual flowing edge to edge.
Composition: ONE continuous surface (the open morning sky) extending edge to edge from top to bottom of the frame. The main subject is anchored in the upper-center area on this same surface. No other surface, no transition between two distinct surfaces anywhere in the frame.
NEGATIVE — strictly avoid:
- no comic panel layout, no split panel, no panel division, no horizontal divider line cutting the image, no upper and lower separate scenes, no two stacked frames, no boxed sections, no inset, no second view of the same subject, no duplicate elements
- no letterbox, no black bands at top or bottom, no padding, no empty black areas, no UI overlay, no caption space rendered as a solid color block
- no border, no frame, no panel border, no inner outline, no outer rectangular outline, no white margin around the image, no thick black outline framing the scene, no comic page border, no painted picture frame, no canvas border, no matted edge
- no main subject in the lower portion, no key figure in the bottom area, no face placed in the bottom of the frame, no central focal point in the bottom third
- no long sentences rendered, no paragraphs of text, no full newspaper headlines, no document body text, no long signage text, no English text, no garbled letters, no fake script, no dense text covering the image; minimal Korean text only if essential (a few characters max)
```
**검색어**
```text
Nonthaburi street morning Thailand
```
