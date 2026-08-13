# 레모션 시제품 — 뉴스 요약 카드 → 세로 숏폼

뉴스 요약 카드(`queue/*.md`) 1건을 코드로 그려 10초 세로 영상(1080×1920 · 30fps · h264 mp4)으로 뽑는 실증 레인.
편집 프로그램 0 — 글자·배치·움직임 전부 코드가 계산하고 헤드리스 브라우저가 프레임을 찍는다.

## 실행

```bash
npm install                       # 1회(의존성 244MB · 커밋 밖)
npm run prep                      # 최신 카드 자동 선택 → out/props.json + 글꼴 준비
npm run prep -- queue/<카드>.md   # 특정 카드 지정
npm run render                    # → out/card.mp4 (10초)
npm run poster                    # → out/poster.png (중간 프레임 1장)
```

## 계약(이 레포 규칙 상속)

- **색·활자 = 토큰 미러**(`src/tokens.ts`) — 정본 = `viewer/index.html` `:root` 실측 사본. 콘텐츠 산출물 색 미러 축(track `PIN_PALETTE`·thumb `legacy_green` 선례) = UI 재유입 아님 · 값 창작 0.
- **글꼴 = 렌더 시점 복사** — `scripts/card2props.mjs`가 정본(`assets/fonts/pretendard.woff2`)을 `public/`으로 복사. 레포 안 사본 커밋 0 = 드리프트 축 소멸.
- **크로미엄 = 폴백 해석기**(`remotion.config.ts`) — env → 헤드리스 셸 실존 검사 → null(레모션 관리 다운로드). ⚠ 크로미엄 본체(141+)는 구형 헤드리스 제거로 기동 거부(260813 실측) → 헤드리스 셸만 후보.
- **내용 = 카드 원문 그대로** — 제목(본문 머리), 한줄 요약 1문단, 확인된 사실 앞 3줄(각 첫 문장 완결 인용 · ⚠줄 제외 · 꼬리 출처 괄호만 제거). 문장 중간 절단 0.

## 검증(260813 실측)

- 이 환경(node 22 + 플레이라이트 헤드리스 셸)에서 실렌더 성공 — `out/card.mp4` 10.05s · 1080×1920 · 30fps · 2.4MB.
- 재료 = `queue/260813-0828-ask-202608122328yqnbl.md`(개기일식) 자동 추출.

## 라이선스

레모션은 개인·3인 이하 영리 조직 무료(그 이상 = 유료 회사 라이선스). 원문 = https://github.com/remotion-dev/remotion/blob/main/LICENSE.md

## 미배선(별건 · 운영자 용도 확정 대기)

- 러너 워크플로(발사 버튼) · R2 착지 · 결과 레일(`nmRail.add`) · 화면 진입점 = 전부 미배선. 이 디렉터리는 시제품 실증까지다.
