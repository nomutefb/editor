# 새벽 한강 다리 — 우산 쓴 기자의 15초 뉴스 오프닝

## ⚙️ UI 설정
의도: 새벽 한강 다리 + 우산 쓴 기자 + 카메라를 향한 접근 → 해석: 실사 시네마틱 · 차가운 여명 톤의 진중한 뉴스 오프닝 · 15초 3샷(설정→접근→도착) · 모델: Kling 3.0 Omni
모드: Omni — @참조 1장으로 기자 정체성을 고정하고, 걷기 동작이 샷을 넘어 흐르는 멀티샷이라 Omni가 정도
해상도: 검증 720p → 확정 1080p — @참조 사용 생성은 4K와 배타 보고라 4K는 최종 업스케일 후보로만
생성 시간: 15초 — 샷 5s+5s+5s(합 = 생성 시간)
비율: 16:9 — 방송 오프닝 관례(쇼츠용이면 9:16으로 변경)
수량: 1 — 검증 단계는 1개씩 돌려 변수 확인이 경제적
네이티브 오디오: On — 빗소리 앰비언스·보도풍 음악을 프롬프트로 생성(오디오 서술 포함이라 Off 절약 대상 아님)
멀티샷 방식: 스마트 멀티샷(단일 프롬프트 + 인라인 Shot 라벨 = C방식) — 걸어오는 동작의 연속성이 본질이라 커스텀 박스보다 컷 재량형이 자연스러움
네거티브 필드: 전용 입력칸이 보이면 아래 🚫 블록을 거기 붙여넣기 — 미노출이면 본문 Avoid로 충분

## 🎬 시나리오
새벽 한강 다리 위, 우산을 쓴 기자가 카메라 앞까지 걸어와 렌즈를 정면으로 응시하며 뉴스의 문을 연다.
샷1: 차가운 청색 여명의 텅 빈 다리 — 저 끝에서 우산을 쓴 작은 실루엣이 걸어오기 시작한다(설정).
샷2: 카메라가 기자 앞에서 같은 속도로 물러나며 동행 — 또렷한 걸음, 우산에서 떨어지는 빗방울, 코트 자락의 미세한 흔들림(접근).
샷3: 기자가 카메라 앞에 멈춰 서서 우산을 살짝 젖혀 얼굴을 드러내고, 말을 걸기 직전의 호흡으로 렌즈를 응시 — 음악이 툭 멎으며 오프닝이 완성된다(도착).
오디오는 가랑비 앰비언스 위에 보도풍 현악 펄스를 낮게 깔았다가 마지막 순간 급정지로 끊는다.

### 🔗 첨부 순서
@ 순서: ①[기자 — 인물(전신·정체성 고정)]

### 샷1 · 15s · 새벽 다리 접근 시퀀스(단일 프롬프트 — 인라인 샷 라벨 3개 포함, 통째로 붙여넣기)
```text
실외 · 새벽의 한강 다리 · 비 내리는 여명. 같은 장소·같은 인물을 유지하고, 카메라는 인물의 걸음과 시선을 따라 자연스럽게 컷한다.

Shot 1 (5s) — [설정 샷, 눈높이 고정 프레임]: 차가운 청색 여명에 잠긴 한강 다리. 젖은 아스팔트에 가로등 불빛이 길게 반사되고 가랑비가 가늘게 흩날린다. 다리 저 끝에서 @ 의 기자(베이지 트렌치코트, 투명 우산을 쓴 30대 여성)가 작은 실루엣으로 카메라를 향해 걸어오기 시작한다.

Shot 2 (5s) — [미디엄샷, 후퇴 트래킹]: 카메라가 걸어오는 @ 의 기자 앞에서 같은 속도로 부드럽게 물러난다. 기자는 뒤꿈치부터 닿는 걸음으로 무게를 옮기며 전진하고, 한 손은 우산 손잡이를 단단히 쥐고 있다. 우산 가장자리에서 빗방울이 똑똑 떨어지고, 트렌치코트 자락이 걸음마다 미세하게 흔들린다.

Shot 3 (5s) — [미디엄 클로즈업, 느린 푸시인]: @ 의 기자가 카메라 바로 앞에 멈춰 선다. 얼굴을 드러내려고 우산을 살짝 뒤로 젖히고, 시청자에게 말을 걸기 직전처럼 숨을 한 번 고른 뒤 턱을 가볍게 들어 렌즈를 정면으로 응시한다. 카메라는 5초에 걸쳐 아주 천천히 얼굴로 다가간다.

오디오: 우산 위로 톡톡 떨어지는 가랑비와 먼 도시의 낮은 웅웅거림. 그 아래로 긴박한 현악 펄스의 보도풍 음악이 낮게 깔리며 점점 조여들고, 기자가 멈춰 서는 순간 음악이 툭 멎고 빗소리만 남는다.

cold blue pre-dawn tone, lone streetlight reflection on wet ground, photorealistic, cinematic lighting, natural skin texture, film grain, sharp detail, subtle rim light. Same exact reporter across all shots, same trench coat, same umbrella.

Avoid: identity drift, warped face, character drift between shots, deformed hands, extra fingers, smiling, umbrella shape change, lighting inconsistency.
```

### 🚫 네거티브
```text
identity drift, warped face, character drift between shots, deformed hands, extra fingers, smiling, umbrella shape change, lighting inconsistency
```

## 🖼 레퍼런스
```text
Full-body photorealistic reference of a Korean female news reporter in her mid-30s, calm composed expression, straight dark shoulder-length hair slightly damp, wearing a beige trench coat over a charcoal suit, holding an opened clear transparent umbrella over her shoulder, standing in a neutral pose facing camera, face fully visible and sharp, cold blue pre-dawn tones, soft overcast light, wet asphalt with subtle streetlight reflection, night bridge background softly blurred, natural skin texture, sharp facial detail, no text, no watermark
```

## 📌 안내
사용 모듈: S01+S06+S07+H01+M09+M04+LGT02+WX-01+AU-19+AU-12+NEG00+NEG13
이 영상은 AI 생성물 표기 의무 대상 — 게시 전 후반 편집에서 "AI 생성" 오버레이를 상시 고정할 것(생성 프롬프트에는 넣지 않음).
보도풍 음악은 관용구 수준의 긴박 펄스만 — 실제 방송사 시그널 멜로디를 흉내 내면 안 됨.
🖼 이미지를 생성한 뒤 Kling에 첨부하고, 프롬프트의 각 @ 에 커서를 대어 그 이미지를 선택하면 칩으로 치환됨(첨부 1장 = 🔗 범례의 ①).
추정 비율: 16:9 — 바꾸려면 입력에 "9:16 세로로"
추정 인물: 30대 한국 여성 기자 — 바꾸려면 입력에 "남성 기자로"
추정 오디오: 음악 무드(대사 없음) — 바꾸려면 입력에 `[대사: "..."]`
추정 날씨: 가랑비 — 폭우는 물 물리가 AI 취약 축이라 기본값에서 제외, 바꾸려면 입력에 "폭우로"
