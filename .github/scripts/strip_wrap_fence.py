#!/usr/bin/env python3
# 산출 랩퍼 코드펜스 벗기기 — 모델이 카드 전체를 ```markdown 펜스로 감싸고 그 뒤에 자기 보고문을 덧붙인 회차를
#   정규화한다(stdin → stdout · 랩퍼가 없으면 바이트 완전 무변경).
#
# 왜(260817 실사고 · 운영자 「뉴스 2번 요약이 깨진다」):
#   요약 모달 본문에 frontmatter 원문(`---` · event_key · alt_urls …)이 코드블록으로 그대로 노출됐다.
#   진범 = 모델이 산출을 이렇게 냈다 —
#       ---                      ← 여분 구분선
#       ```markdown              ← "이게 파일 내용" 랩퍼
#       ---                      ← 진짜 frontmatter 시작
#       event_key: …
#       ---
#       # 본문 …
#       ```                      ← 랩퍼 닫힘
#       ---
#       **완료 여부** — …        ← 모델 자기 보고문
#   analyze.sh 493행 `sed -n '/^---/,$p'` 는 첫 `---` 부터 취하므로 여분 구분선부터 통째로 살아남고,
#   498행 awk 는 여는 `---` 뒤의 중복 `---`·빈 줄만 걷어내지 도구 펜스는 모른다 → 펜스가 그대로 남아
#   진짜 frontmatter 가 본문 안쪽으로 밀린다 → 닫는 `---` 보증 awk 가 펜스 앞에 `---` 를 박아
#   **도장 필드 4개짜리 가짜 frontmatter + 코드블록에 든 진짜 frontmatter** 라는 이중 구조가 굳는다.
#   실측 피해 = 260817-1047(운영자 신고 건) · 260812-1906(같은 형태로 5일 전에도 났다 = 신규 회귀가 아니라
#   모델 변덕이 올 때마다 재현되던 간헐 사고이고, 그걸 흡수하는 층이 파이프에 없었다).
#
# 술어(둘 다 성립할 때만 손댄다 = 정상 산출 무접촉):
#   ⓐ 여는 `---` 다음의 「아직 실질 필드가 안 나온 구간」에 코드펜스 줄이 있다 = 랩퍼 여는 펜스
#      → 그 줄 제거(중복 `---`·빈 줄은 종전대로 analyze/ask 의 awk 가 걷는다).
#   ⓑ ⓐ 가 성립한 회차에 한해 **마지막 펜스 줄부터 끝까지** 버린다 = 랩퍼 닫힘 + 그 뒤 모델 보고문.
#      ⚠ 랩퍼를 못 찾으면 꼬리 절단도 안 한다 — 본문이 정당한 ```text 초안 블록으로 끝나는 정상 카드에서
#         마지막 펜스를 지우면 초안이 통째로 깨진다(그래서 ⓐ 가 ⓑ 의 선행 조건이다).
#      ⚠ 본문 초안 블록(```text)은 랩퍼 안에 중첩돼 있어 마크다운 규격상 이미 깨진 구조라 균형 계산이
#         성립하지 않는다 → 「마지막 펜스」가 랩퍼 닫힘이라는 실측 기반 술어를 쓴다.
import re
import sys

_FENCE = re.compile(r"^[ \t]*(```|~~~)")


def strip_wrap(txt):
    lines = (txt or "").split("\n")
    if not lines or not lines[0].strip() == "---":
        return txt, ""
    open_i = -1
    for i in range(1, len(lines)):
        s = lines[i].strip()
        if s == "---" or s == "":          # 중복 구분선·빈 줄 = 아직 실질 필드 전
            continue
        if _FENCE.match(lines[i]):
            open_i = i
        break                               # 첫 실질 줄에서 판정 종료(본문 펜스 무접촉)
    if open_i < 0:
        return txt, ""
    close_i = -1
    for i in range(len(lines) - 1, open_i, -1):
        if _FENCE.match(lines[i]):
            close_i = i
            break
    if close_i < 0:
        return txt, ""
    kept = lines[open_i + 1:close_i]
    while kept and kept[-1].strip() == "":
        kept.pop()
    out = "\n".join(lines[:open_i] + kept)
    return (out + "\n" if txt.endswith("\n") else out), "랩퍼 펜스 제거 — 꼬리 %d줄 절단" % (len(lines) - close_i)


def main():
    raw = sys.stdin.read()
    out, note = strip_wrap(raw)
    print(out, end="")
    if note:
        sys.stderr.write(note + "\n")


if __name__ == "__main__":
    main()
