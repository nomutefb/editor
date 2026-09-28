# 유튜브 숏폼(ys) — 유튜브 링크 → 인사이트 보고서 · 인포그래픽 · 9:16 숏폼

운영자 260928: NotebookLM 보고서 수준의 요약을 **유튜브 전사만으로** 만들고, 그 요약을 원천 삼아 숏폼 영상까지 한 번에 뽑는다. 뉴스 요약·자료화(nb)·큐영상(vd)과 **독립 레인**이다(서로의 산출·설정을 읽거나 바꾸지 않는다).

## 흐름과 파일
| 단계 | 파일 | 비고 |
|---|---|---|
| 화면 | `viewer/ys.html` (영상 스튜디오 「유튜브」 탭) | Tasks 카드 = `/ys_out/<id>/progress.json` 5초 폴링 |
| 발사 | `functions/api/ys.js` | 유튜브 영상 주소·옵션 화이트리스트(voice·stt·img·len·font·ratio) · 장면 화면 img = codex(GPT 이미지 · 기본)·motion(모션 그래픽)·depth(GPT 입체)·grok(그록 영상) |
| 실시간 서빙 | `functions/ys_out/[[path]].js` | R2 우선(`_r2live.js`) — progress·result·맥 표시등 |
| 워크플로 | `.github/workflows/ys-make.yml` | 자막(yt-dlp) → 받아쓰기(Scribe·Whisper, 선택) → claude 1콜 → 음성 → 그림(선택) → 렌더 → R2 |
| 진행 기록 | `.github/scripts/ys_progress.py` | 8단계 가중 진행률(방식에 없는 단계 = 건너뜀) · 단계별 예산 |
| 대본·보고서 | `prompts/ys-make.md` · `.github/scripts/ys_make.sh` · `ys_plan.py` | 문체 = `shared/ko_tone_rules.md` **KO-TONE:YS** 구간만(im-not-ai v2.8) |
| 음성 | `.github/scripts/ys_tts.py` | edge(무료) · ElevenLabs(`ELEVENLABS_API_KEY` · 목소리 = 레포 변수 `YS_EL_VOICE`, 없으면 계정 목소리 자동) |
| 장면 그림 | `.github/scripts/ys_images.py` ↔ `scripts/mac/nomute_ys_driver.sh` | 맥 Codex(ChatGPT 구독) · R2 `queue/ysimg/` · 영상 비율 그대로(9:16 = 세로 2:3 · 16:9 = 가로 3:2) · 맥 꺼짐 = 모션 그래픽 |
| 모션 그래픽 | `.github/scripts/ys_mg.py` · `apps/ys/mg_icons.json`(Lucide · ISC) | 도식 8틀(비교·흐름·숫자·막대·목록·순환·아이콘·인용) · CSS 애니메이션 → 프레임 구동 캡처(등장 2.4초 + 3초 반복) |
| GPT 입체 | `.github/scripts/ys_depth.py` | 깊이 추정(Depth Anything V2 Small ONNX) + 시차 워핑 = 2.5D |
| 그록 영상 | `.github/scripts/ys_grok.py` ↔ `shared/grok_api.py` | 장면 1개 = 클립 1개 · 첫 프레임 = 맥 GPT 그림 · 3발 동시 · 콘티 레인과 같은 열쇠 줄(nm-grok-key) · 9:16 전면 |
| 맥 표시등 | `scripts/mac/nomute_ys_heartbeat.sh` | R2 `ys_out/_mac/heartbeat.json` 분당 갱신 |
| 렌더 | `.github/scripts/ys_render.py` | 장면 = 전부 화면 전체 + 문장 자막만(화면 문구 없음) — 그록 영상 / GPT 그림(정지·입체) / 모션 그래픽 · ffmpeg · 폰트 3종(pretendard·gothic·barun) |
| 설정 안내 | `viewer/ys-mac-guide.html` | 맥 Codex 설치·로그인·시험 |

## 레포 변수(선택)
`YS_EL_VOICE`(ElevenLabs 목소리 id) · `YS_IMG_WAIT`(그림 대기 초 · 기본 900) · `YS_MAX_SEC`(영상 길이 상한 · 기본 14400) · `YS_STT_MAX_SEC`(받아쓰기 상한 · 기본 3600)

## 검사
`python3 -m unittest tests.test_ys_pipeline` · `node --test tests/ys-api.test.mjs`
