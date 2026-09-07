# 노뮤트 에디터

뉴스 수집·요약, 카드 이미지와 영상 제작을 한 화면에서 관리하는 개인 편집 도구.
운영 화면은 https://edit.nomute.kr 이고, 이 저장소의 `main`을 Cloudflare Pages가 빌드한다.

## 작업 시작

Node 24, Python 3.11 이상, Git, Bash 4 이상을 사용한다. 화면 검사는 Chromium이 필요하다.
검사 의존성은 `python3 -m pip install PyYAML Pillow`로 설치한다.

```sh
git config core.hooksPath .githooks
node build-viewer.mjs
python3 -m http.server 8080 --directory viewer
```

로컬 정적 서버는 화면 확인용이다. 실제 제작·설정 저장은 운영 환경의 Pages Functions와 R2 연결이 필요하다.
제작 도구별 추가 설치는 해당 `apps` 폴더의 안내와 설치 스크립트를 따른다.

## 어디를 수정하나

| 영역 | 작성 위치 | 역할 |
|---|---|---|
| 메인 화면 | `viewer-src/manifest.json`에 나열된 조각 | 기능별 작성 원본 |
| 스튜디오 화면·공용 부품 | `viewer/` | 이미지·영상 편집 및 공용 상태 관리 |
| 요청 처리 | `functions/` | 설정, 진행 상태, 제작 접수 |
| 제작 실행 | `.github/workflows/`, `.github/scripts/`, `apps/` | 자동 작업과 결과 저장 |
| 뉴스 수집 | `scraper/` | 수집·선정·관측 |
| 검사·빌드 | `shared/`, `tests/` | 기존 규칙과 실제 실패 상황 검증 |
| 문체와 편집 품질 | `apps/news/`, `prompts/`, `PROJECT_MEMORY.md` | 뉴스 제작 지침 |

`viewer/index.html`은 생성물이다. 원본을 수정한 뒤 `python3 shared/build_shell.py`를 실행한다.
배포 때는 원본 조각이 기존 단일 HTML로 합쳐지므로 캐시된 화면과 스크립트의 버전이 갈라지지 않는다.
기존 생성 도구가 HTML을 직접 바꿨으면 `python3 shared/import_shell.py`로 조각에 반영하고 차이를 확인한다.

## 검증

```sh
python3 shared/check_refs.py
node --test tests/*.test.mjs
python3 tests/test_git_land.py
node build-viewer.mjs
bash shared/smoke_all.sh
```

Chromium 자동 탐색이 안 되면 `CHROMIUM_PATH`를 지정한다.
화면 전후 비교는 `node shared/preview_shot.js base`와 `diff`를 사용한다.
변경한 코드의 검사와 화면 검사 통과 후 PR로 반영하고, 운영 화면이 해당 버전으로 갱신됐는지 확인한다.

## 저장과 복구

- 설정은 요청 당시의 목록을 기준으로 항목별 병합한다. 충돌한 변경은 기기에 보관하고 설정 메뉴에서 내려받을 수 있다.
- 연결 실패로 저장하지 못한 설정은 기기에 남고, 재접속·화면 복귀 시 재시도한다.
- 자동 결과 저장 실패는 실패로 종료한다. 결과 스냅샷은 작업 첨부물로 3일 보관한다.
- 로컬 실행 실패 스냅샷은 `.git/editor-recovery`에 남는다. `files/`의 원본과 삭제 목록을 확인하고 최신 브랜치에 필요한 변경만 적용한다.

## 가벼운 보관 정책

과거 버전 사본, 작업 보고서, 일회성 산출물, 루트 백업 압축파일을 새 커밋에 누적하지 않는다.
관측 시계열과 참조 메타는 기본 14일만 보관한다. 현재 후보에 필요한 메타는 유지한다.
제작에 쓰는 견본·브랜드·폰트·입력 원본과 진행 중 작업은 역사 로그와 구분해서 유지한다.
삭제된 과거 파일은 Git 이력에 남아 있으며 이 작업은 원격 Git 이력을 다시 쓰지 않는다.

개발 공통 규칙은 `AGENTS.md`, 현재 운영 규칙은 `CLAUDE.md`, 검사 색인은 `docs/current-contracts.md`에서 확인한다.
