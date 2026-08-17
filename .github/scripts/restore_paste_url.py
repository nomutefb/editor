#!/usr/bin/env python3
# 전문 붙여넣기 원문 주소 도장 — 폰 공유 본문 꼬리에 실려 온 원문 URL 을 산출 frontmatter `url` 에 심는다.
#   CONTRACT: check_paste_url_stamp
#
# 왜(260817 실사고 · 운영자 「요약끝난곳에도 좌측상단에 바로가기 버튼 있어서 원문으로 갈 수 있어야 하는데 떼어진듯」):
#   뷰어 요약 모달 좌상단 원문 버튼(#src)은 frontmatter `url` 이 있을 때만 활성이고, 없으면 회색 비활성
#   (viewer/index.html 4978~4979행 — 버튼이 사라진 게 아니라 갈 곳이 없어 꺼진 것이다).
#   전문 붙여넣기 경로는 analyze.sh 가 art_url="" 로 두므로 그 값을 **모델이 WebSearch 로 찾아야만** 채워졌고,
#   프롬프트가 「몇 번에 안 나오면 빈 문자열로 둔다」라 확률 축이었다 → 같은 날 같은 주소가 본문에 실려 온
#   두 건에서 결과가 갈렸다(실측 = 260817-1001 채움 / 260817-0954 빈값 · 둘 다 본문 꼬리에
#   `https://news.nate.com/view/20260817n03329` 가 들어 있었다).
#
#   그런데 그 주소는 **이미 우리 손에 있다** — 폰이 '페이지 전체선택 텍스트' 맨 뒤에 그 페이지 주소를 붙여 보낸다.
#   검색으로 다시 찾을 이유가 없으므로 스크립트가 결정론으로 박는다(모델 변덕 무관 = restore_orig_title 도장 문법 계승).
#
# 추출 술어 = functions/api/pending.js `shareUrl()` 와 같은 값이어야 한다(언어가 달라 사본이지만 규칙은 1:1) —
#   갈리면 대기열 행 바로가기와 요약 카드 바로가기가 **서로 다른 곳으로 간다**.
#   ⓐ 텍스트 조각(`#:~:text=`) 제거 = 폰이 붙이는 조각이 네비 문구라 그대로 열면 엉뚱한 자리로 스크롤
#   ⓑ 경로 없는 주소(매체 홈) 제외 = 본문 중간 인용으로 섞여 온다
#   ⓒ 여러 개면 맨 뒤 = 폰이 붙인 그 페이지 주소가 본문 인용 주소보다 뒤에 온다
#
# 무주입(= 종전 동작 그대로 = 악화 경로 0) = 본문에 주소 없음 · frontmatter 미검출 · url 줄 없음 ·
#   url 이 이미 채워짐(모델이 원매체를 찾았으면 포털 주소보다 그쪽이 낫다 = 한 글자도 안 건드린다).
import re
import sys

_URL = re.compile(r'https?://[^\s"<>)\]]+')


def share_url(body):
    """폰이 본문 꼬리에 붙인 그 페이지 주소 — pending.js shareUrl() 동일 술어."""
    out = []
    for m in _URL.finditer(body or ""):
        u = m.group(0).split("#:~:")[0].rstrip(".,);]』」”'\"")
        rest = u.split("//", 1)[1] if "//" in u else ""
        path = rest.split("/", 1)[1] if "/" in rest else ""
        if len(path) < 3:   # 경로 없음 = 매체 홈(기사 아님)
            continue
        out.append(u)
    return out[-1][:400] if out else ""


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else ""
    raw = sys.stdin.read()
    try:
        txt = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        print(raw, end="")
        sys.stderr.write("대기열 파일 열기 실패 — 무주입\n")
        return
    bi = txt.find("\n# body:")
    url = share_url(txt[bi + 8:] if bi >= 0 else "")
    if not url:
        print(raw, end="")
        sys.stderr.write("본문에 원문 주소 없음 — 무주입\n")
        return
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.S)
    if not fm:
        print(raw, end="")
        sys.stderr.write("frontmatter 미검출 — 무주입\n")
        return
    um = re.search(r'^url:[ \t]*"?(.*?)"?[ \t]*$', fm.group(1), re.M)
    if not um:
        print(raw, end="")
        sys.stderr.write("url 줄 미검출 — 무주입\n")
        return
    if um.group(1).strip():
        print(raw, end="")
        sys.stderr.write("url 이미 채워짐(모델이 원매체 확보) — 무주입\n")
        return
    val = url.replace("\\", "\\\\").replace('"', '\\"')
    lo = fm.start(1) + um.start()
    hi = fm.start(1) + um.end()
    print(raw[:lo] + 'url: "' + val + '"' + raw[hi:], end="")
    sys.stderr.write("원문 주소 주입 완료(폰 공유 본문 꼬리) — " + url + "\n")


if __name__ == "__main__":
    main()
