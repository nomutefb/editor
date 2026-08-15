# 폭우 속 컵라면 — 처마 밑 10초 응시

## ⚙️ UI 설정
의도: 폭우에 갇힌 우산 없는 회사원이 편의점 처마 밑에서 컵라면을 들고 카메라를 정면으로 바라보는 10초 클로즈업 → 해석: 실사 시네마틱 · 근접 고정 프레이밍 + 미세 모션 위주의 정적 감정 샷 · 단일 샷 10초 · 모델: Kling 3.0
모드: ① 3.0 스타트-엔드 — 고정 프레이밍에 분위기·미세 모션만 얹는 장면이라 원본 이미지 유지형이 정도(레퍼런스 이미지를 스타트 프레임으로)
해상도: 검증 720p → 확정 1080p — 확정본 업스케일이 필요하면 최종 단계에서 4K
생성 시간: 10초 — 입력 지정값 그대로(단일 샷 = 커스텀 분할 불필요)
비율: 9:16 — 쇼츠 세로 기본(스타트 프레임도 같은 비율로 합성)
수량: 1 — 검증 후 필요 시 증량
네이티브 오디오: On — 빗소리 앰비언트·호흡이 이 샷의 절반(대사 없음이지만 소리가 핵심)
멀티샷 방식: 단일 프롬프트 — 샷 1개라 분할 자체가 없음
네거티브 필드: 노출 시 아래 `### 🚫 네거티브` 블록을 붙여넣기 — 미노출이면 본문 Avoid로 충분

## 🎬 시나리오
퇴근길 폭우에 갇힌 회사원이 컵라면의 온기 하나에 의지한 채, 하소연하듯 카메라를 정면으로 바라본다.
편의점 처마 밑, 밤. 형광등 불빛이 등 뒤에서 새어 나오고 처마 밖은 장대비가 벽처럼 쏟아진다.
젖은 머리칼에서 물이 떨어지는 남자가 두 손으로 컵라면을 감싸 쥐고 있다 — 김이 얼굴 앞으로 피어오른다.
동작은 미세 모션뿐: 호흡, 느린 눈 깜빡임, 김의 흔들림, 배경의 빗줄기. 카메라는 거의 느껴지지 않을 만큼만 천천히 다가간다.
사건 1개("이 비는 언제 그치나"라는 체념의 응시), 반전 없이 감정 하나로 10초를 버티는 샷.

### 샷1 · 10s · 처마 밑 정면 응시 클로즈업
```text
클로즈업. 실외, 밤, 편의점 처마 밑 — 처마 밖은 폭우가 벽처럼 쏟아진다. 우산 없이 비를 맞고 온 30대 회사원 남자, 젖은 네이비 정장에 물기 밴 흰 셔츠, 이마에 붙은 젖은 머리칼 끝에서 물방울이 또박또박 떨어진다. 그는 온기를 지키려고 두 손으로 김이 오르는 컵라면을 가슴 앞에 감싸 쥐고(fingers grip the paper cup edge), 하소연하듯 렌즈를 정면으로 바라본다 — 초점 없는 허탈한 응시가 카메라에 고정된다. 등 뒤 편의점 유리에서 새어 나오는 형광등 평면광이 젖은 어깨 윤곽을 잡고, 배경 빗줄기는 그 빛을 받아 반짝인다. 표정은 미세하게만 움직인다: 느린 눈 깜빡임, 살짝 벌어졌다 다물리는 입, 얕은 한숨에 들썩이는 가슴, 얼굴 앞에서 흔들리는 라면 김, 바람에 떨리는 젖은 옷자락. 카메라는 10초에 걸쳐 거의 느껴지지 않을 만큼 미세하게 얼굴 쪽으로 다가간다(camera pushes in almost imperceptibly over 10 seconds).

오디오: 처마 위를 두드리는 굵은 빗소리와 바닥 웅덩이에 튀는 물소리가 샷 전체에 깔리고, 멀리 젖은 도로를 지나는 차의 물살 소리. 7초쯤 남자의 얕은 한숨 "하아…" 한 번, 배경 음악 없음.

photorealistic, cinematic lighting, natural skin texture, visible pores, film grain, sharp detail, subtle rim light from the store window, dense rain streaks catching the light, breathing, blinking, fabric sway. Same exact person throughout, identity locked, same face, same wet navy suit, same steaming cup ramen, same convenience store background. Stabilized camera, no morphing, no outfit change, no scene change.

Avoid: deformed hands, extra fingers, warped face, morphing, identity drift, plastic skin, waxy skin, watermark.
```

### 🚫 네거티브
```text
deformed hands, extra fingers, warped face, morphing, identity drift, plastic skin, waxy skin, over-smoothed, background warping, watermark, background music
```

## 🖼 레퍼런스
```text
9:16 vertical photorealistic night photograph. A Korean convenience store at night in torrential rain — camera under the awning, close-up framing on a man in his mid-30s, an office worker caught in the downpour without an umbrella. Rain-soaked navy suit, damp white shirt, wet hair strands stuck to his forehead with droplets falling. He cradles a steaming instant cup ramen with both hands at chest level, fingers gripping the paper cup, and looks straight into the camera with a vacant, worn-out stare. Behind him, flat greenish fluorescent light spills from the store's glass front, rim-lighting his wet shoulders; heavy rain streaks fill the background, catching the light, puddle reflections on the pavement below. Cinematic lighting, natural skin texture, film grain, sharp detail. No text, no watermark, no graphic overlay.
```

## 📌 안내
사용 모듈: S08+M50+LIGHT18+WX-02+EM-19+AN-03+AN-10+NEG00
스타트 프레임: 위 레퍼런스 이미지를 나노바나나로 9:16 생성 → Kling 3.0 스타트-엔드 탭의 스타트 프레임으로 첨부(@ 문법 사용 없음)
AI 생성물 표기: 게시 전 AI 생성 오버레이(9:16용 `ai_overlay_916.png`) 후반 합성 필수 — AI기본법 가시적 표시 의무
추정 시간대: 밤 — 바꾸려면 입력에 "해질녘으로"
추정 화풍: 실사 시네마틱 — 바꾸려면 입력에 "극화 웹툰풍으로"
추정 오디오: 대사 없이 빗소리·한숨만 — 대사를 넣으려면 입력에 '[대사: "..."]'
추정 비율: 9:16 세로 — 바꾸려면 입력에 "16:9로"
