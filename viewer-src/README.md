# 화면 작성 원본

`manifest.json` 순서대로 `.part`를 이어 붙여 `viewer/index.html`을 만든다.
원본 조각은 같은 스크립트 전역 범위와 실행 순서를 공유한다. 독립 모듈처럼 실행하지 않는다.

- 변경할 기능 이름이 있는 조각을 수정한다.
- `python3 shared/build_shell.py`로 화면을 만든다.
- `python3 shared/check_refs.py`로 원본과 생성물의 일치 및 기존 동작 계약을 검사한다.
- 최종 배포는 HTML과 스크립트가 함께 캐시되도록 기존 인라인 형태를 유지한다.
- 기존 도구가 생성 화면을 수정했다면 `python3 shared/import_shell.py`로 원본에 반영한 뒤 차이를 검토한다.
