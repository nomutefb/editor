#!/usr/bin/env python3
# 원문 제목 복원 도장 — frontmatter title 이 본문 후킹 헤드(# …)로 덮였을 때 수집기 원문 제목으로 되돌린다.
#   CONTRACT: check_orig_title_restore
#
# 왜(260813 실사고):
#   prompts/news-analysis.md 38행 계약 = 「title = 기사 제목 원문 그대로 · 생성 헤드·이모지 넣지 마라
#   (후킹 헤드는 본문 `# {제목}` 몫)」. 260811 밤부터 이 계약이 산출에서 깨졌다 — 실측 260811~13 카드 11건이
#   전부 `title == 본문 # 헤드`(추상 후킹문)였고, 같은 기사의 수집기 메타에는 원문 제목이 정상으로 들어 있었다
#   (예: 「정부, 폭염에 수산물 최대 50% 할인·재난지원금 332억원 투입」 → 산출 title 「바다는 식힐 수 없어서,
#   죽기 전에 팔라고 한다」). 즉 원문은 프롬프트까지 도달했는데 산출에서만 덮였다 = 모델 준수 드리프트.
#
#   비용이 큰 이유 = 뷰어 모달이 원문 제목 줄(.md-srct)을 「frontmatter title ≠ H1」일 때만 그린다
#   (viewer/index.html 4948행 · 옛 분석분의 제목 2줄 중복을 지우려고 260805 에 넣은 정당한 가드).
#   title 이 H1 과 같아지면 그 가드가 정상 동작해 **기자가 뽑은 직설 제목 줄이 통째로 사라진다** →
#   화면에 남는 건 추상 헤드 하나뿐이라 요약 상자만 봐서는 무슨 사건인지 알 수 없다(운영자 260813 신고).
#
# 판정 = 위반 서명일 때만 손댄다(모델이 계약을 지킨 산출은 한 글자도 안 건드린다):
#   ⓐ title 이 비었거나 ⓑ 선두 토픽 이모지·공백을 무시한 title 이 본문 첫 `# ` 헤드와 같다.
#   ⓑ 의 대조 술어 = 뷰어 `_tkey`(index.html 4949행)·build-viewer `stripLeadEmoji` 와 같은 관용구
#   (화면이 「같은 제목」이라 판정하는 기준과 정확히 같은 자를 써야 화면 증상과 게이트가 안 갈린다).
#
# 무주입(= 종전 동작 그대로 = 악화 경로 0) = 원문 제목 없음 · frontmatter 미검출 · title 줄 없음 ·
#   본문 헤드 없음 · 위반 서명 아님 · 원문 제목이 이미 현재 title 과 같음.
import re
import sys

# \u26A0\uFE0F \uD30C\uC774\uC36C re \uB294 \p{Extended_Pictographic} \uB97C \uBAA8\uB978\uB2E4(\uBDF0\uC5B4 JS \uC220\uC5B4\uC758 \uC9C1\uC5ED\uC774 \uBD88\uAC00) \u2192 \uAC19\uC740 \uBC94\uC704\uB97C \uCF54\uB4DC\uD3EC\uC778\uD2B8\uB85C \uD3B8\uB2E4.
#   \uBC94\uC704 \uC6D0\uCC9C = build-viewer.mjs stripLeadEmoji \uAC00 \uC7A1\uB294 \uC120\uB450 \uD1A0\uD53D \uC774\uBAA8\uC9C0\uB300(\uAE30\uD638\u00B7\uD654\uC0B4\uD45C\u00B7\uADF8\uB9BC\uBB38\uC790) \u00B7 \uC0C8 \uBC94\uC704 \uCC3D\uC791 0.
_LEAD_EMOJI = re.compile(r"^\s*(?:[\U0001F000-\U0001FAFF\u2190-\u21FF\u2300-\u27BF\u2B00-\u2BFF]\uFE0F?\s*)+")


def key(s):
    """선두 토픽 이모지·모든 공백을 무시한 비교키 — 뷰어 _tkey(index.html 4949행) 동일 술어."""
    return re.sub(r"\s+", "", _LEAD_EMOJI.sub("", s or ""))


def main():
    orig = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    raw = sys.stdin.read()
    if not orig:
        print(raw, end="")
        sys.stderr.write("원문 제목 없음 — 무주입\n")
        return
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.S)
    if not fm:
        print(raw, end="")
        sys.stderr.write("frontmatter 미검출 — 무주입\n")
        return
    tm = re.search(r'^title:[ \t]*"?(.*?)"?[ \t]*$', fm.group(1), re.M)
    if not tm:
        print(raw, end="")
        sys.stderr.write("title 줄 미검출 — 무주입\n")
        return
    cur = tm.group(1).strip()
    h1m = re.search(r"^#[ \t]+(.+?)[ \t]*$", raw[fm.end():], re.M)
    h1 = h1m.group(1).strip() if h1m else ""
    if cur and not h1:
        print(raw, end="")
        sys.stderr.write("본문 헤드 미검출 — 무주입\n")
        return
    if cur and key(cur) != key(h1):
        print(raw, end="")
        sys.stderr.write("계약 준수(title ≠ 후킹 헤드) — 무주입\n")
        return
    if key(cur) == key(orig):
        print(raw, end="")
        sys.stderr.write("이미 원문 제목 — 무주입\n")
        return
    val = orig.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")
    lo = fm.start(1) + tm.start()
    hi = fm.start(1) + tm.end()
    print(raw[:lo] + 'title: "' + val + '"' + raw[hi:], end="")
    sys.stderr.write("복원 완료(후킹 헤드가 덮고 있었음)\n")


if __name__ == "__main__":
    main()
