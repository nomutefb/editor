#!/usr/bin/env python3
"""게시물 표지에 박힌 **제목 오버레이**를 읽어 원장에 굽는다 — 채널 요약이 게시물을 실명으로 지목할 때 쓰는 이름의 정본.

운영자 260812: "이 ai 요약 안에 있는 게시물들의 타이틀, 아마 첫줄을 가져올텐데, 게시물 오버레이나
게시물 첫장에 쓰인 타이틀(무조건 양식이 거의 고정), 헤더 포함해서 썸네일을 ocr로 읽어서 이를 가져오게
할 수 있나? 기사 인트로 첫줄보다, 오버레이가 가장 정확한 내용이거든."

[왜 캡션 첫 줄로는 안 되나 — 260812 실측]
  post_refs·posts 의 `name` = `first_line(caption)` = **인스타 글의 첫 줄**인데, 노뮤트는 카드에 박는
  제목과 글 첫 줄을 **각각 따로 쓴다**. 소유 커버 2장 실판독:
    글 첫줄 「🚨 엿새 만에 다시 쐈다, 이번에도 북은 말이 없다」
      ↔ 카드 「북한, 엿새 만에 '또 쐈다' || 동쪽 방향 미상 발사체 발사」
    글 첫줄 「🚇 열차는 서지 않았다…전장연 71차 출근길 시위」
      ↔ 카드 「"우리를 가두지 마십시오" || 전장연, 매주 출근길 시위 진행」
  → 요약이 «…» 로 게시물을 지목할 때 **화면에 실제로 뜬 제목과 다른 말**을 하고 있었다. 운영자가 그 요약을
    읽고 판단하는 축이라(어느 카드가 터졌나) 이름이 어긋나면 판단 자체가 어긋난다.

[비용 = 사실상 0]
  · 읽을 바이트가 **이미 우리 것** = `viewer/insta_covers/<id>.jpg`(260810 소유층) → 다운로드·네트워크 0
  · 판독 = Claude 헤드리스(구독 축 = 종량제 0 · 벤더 신설 0 · 폴오버·계측 SSOT 경유 = ask_srcocr 문법 계승)
  · 미디어 id별 **1회만**(원장 적중 = 재판독 0) → 첫 회차만 2콜, 이후 신규분(하루 1~3장) = 1콜
  · 브리프 레인에 이미 claude CLI 가 깔려 돈다(insta-fetch.yml) = 설치 스텝 신설 0

[⚠ 원장이 영속층인 이유]
  커버 파일은 화면 12칸분만 남고 밖은 **삭제된다**(insta_signals COVER 롤링 · 무한 비대 방지).
  삭제 전에 읽어 텍스트로 남기면 그 게시물 제목은 영구히 안 사라진다 = 원장은 지우지 않는다(텍스트라 가볍다).

[⚠ 사진에 원래 박힌 글자와 갈라야 한다]
  운영자 "썸네일에 자막이 포함될 수 있으니" — 커버 사진 자체에 현수막·간판·방송 자막·기사 캡처·언론사
  로고가 찍혀 있다(실측 = 전장연 커버의 현수막 「이동권보장 중앙정부 책임」, 북한 커버의 「조선중앙통신」
  워터마크). 그걸 제목으로 주우면 요약이 엉뚱한 문장을 게시물 이름이라고 부른다 → 프롬프트가 오버레이
  양식(머리줄+받침줄)만 집도록 명시하고, 못 가르면 `(없음)` 으로 빠지게 한다(안전측 실패 = 캡션 폴백).

사용: python3 insta_cover_ocr.py [--limit N] [--model M] [--timeout S] [--force <id…>]
출력: 원장 `apps/insta/data/cover_titles.json` 갱신 · stdout = 요약 1줄 · ⚠️ 항상 rc=0(fail-soft).
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'shared'))
from claude_py import run_claude   # 쿼터 한도 시 자동 폴오버(SSOT · 자체 쿼터처리 금지 게이트 준수)  # noqa: E402

DATA = os.path.join(ROOT, 'apps', 'insta', 'data')
COVER_DIR = os.path.join(ROOT, 'viewer', 'insta_covers')
LEDGER = os.path.join(DATA, 'cover_titles.json')
MEDIA = [os.path.join(DATA, 'media_latest.json'), os.path.join(DATA, 'media_all.json')]

# 기계 판독 축 = sonnet(models.json 「기계 분류 운영」 티어) · 판독 정확도가 중요해 최저 티어는 안 쓴다(ask_srcocr 동값).
MODEL = os.environ.get('COVER_OCR_MODEL', os.environ.get('ASK_OCR_MODEL', 'claude-sonnet-5'))
BATCH = 8          # 1콜당 이미지 수(ask_srcocr MAX_IMGS 동값)
MAX_BATCH = 4      # 1회차 상한 = 32장(첫 시드 회차만 도달 · 평시 1배치)
SEP = ' || '       # 머리줄/받침줄 구분자

PROMPT = """아래 이미지들은 뉴스 카드 게시물의 **표지(첫 장)** 다. 표지 아래쪽에는 제작자가 얹은 **제목 오버레이**가 큰 글자로 있고, 그 위에 채널 워드마크가 있다.

각 이미지에서 **그 제목 오버레이만** 그대로 옮겨 적어라.

규칙:
- 출력 = 이미지마다 정확히 한 줄. 형식 = `[N] 첫째 줄 || 둘째 줄 || 셋째 줄`
- ⚠ **줄 수는 정해져 있지 않다**(한 줄일 수도, 두세 줄일 수도 있다). 보이는 줄을 다 옮긴다.
- ⚠ **위에서 아래로 보이는 순서 그대로** 옮긴다. 글자 색(흰색·초록색)은 줄마다 다르게 칠해져 있고
  카드마다 배치가 다르다 — **색으로 순서를 정하지 마라. 위치(위→아래)만이 순서다.**
  한 문장이 두 줄에 걸쳐 있으면 그 줄들을 그 순서대로 이어 적는다(순서를 바꾸면 문장이 깨진다).
- 제목 오버레이가 없으면 `[N] (없음)` 한 줄만 쓴다.
- **사진에 원래 찍혀 있던 글자는 제외한다.** 현수막·팻말·간판·방송 자막·기사 캡처·언론사 로고·출처
  워터마크·웹주소는 오버레이가 아니다. 제작자가 얹은 큰 제목 두 줄만 고른다.
- 채널 워드마크(NOmute 등)도 제외한다.
- 오버레이인지 사진 속 글자인지 **가릴 수 없으면** `[N] (없음)` 으로 둔다(틀린 제목보다 빈칸이 낫다).
- 해석·요약·의역·맞춤법 교정 금지. 보이는 그대로 옮긴다(따옴표·말줄임표·이모지 포함).
- 머리말·설명·총평 금지. 위 형식 줄만 출력한다.

파일:
%s
"""

LINE_RE = re.compile(r'^\s*\[(\d+)\]\s*(.*)$')


def _load_ledger():
    try:
        with open(LEDGER, encoding='utf-8') as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save_ledger(led):
    os.makedirs(DATA, exist_ok=True)
    tmp = LEDGER + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(led, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, LEDGER)   # 원자적 교체 = 중단 시 반쪽 원장 0


def _owned_covers():
    """레포가 소유한 커버 [(media_id, path)] — 최신 게시물 우선(수집 목록 순서 = 최신순)."""
    try:
        have = {n[:-4] for n in os.listdir(COVER_DIR) if n.endswith('.jpg')}
    except OSError:
        return []
    order, seen = [], set()
    for mp in MEDIA:   # media_latest(최근 25) 먼저 = 신선한 것부터 읽는다
        try:
            with open(mp, encoding='utf-8') as f:
                for m in (json.load(f).get('media') or []):
                    mid = str(m.get('id') or '')
                    if mid and mid in have and mid not in seen:
                        seen.add(mid)
                        order.append(mid)
        except Exception:
            continue
    order += sorted(have - seen, reverse=True)   # 목록에 없는 잔여분(롤링 경계)도 빠뜨리지 않는다
    return [(mid, os.path.join(COVER_DIR, mid + '.jpg')) for mid in order]


def parse(out, ids):
    """모델 출력 → {media_id: 제목} · 형식 밖 줄·(없음)은 버린다(빈칸 = 캡션 폴백 = 안전측 실패)."""
    got = {}
    for ln in (out or '').split('\n'):
        m = LINE_RE.match(ln)
        if not m:
            continue
        i = int(m.group(1)) - 1
        t = (m.group(2) or '').strip()
        if not (0 <= i < len(ids)) or not t or t.startswith('(없'):
            continue
        t = re.sub(r'\s*\|\|\s*', SEP, t)          # 구분자 정규화
        t = re.sub(r'\s+', ' ', t).strip(' |')
        if t:
            got[ids[i]] = t[:120]
    return got


def read_batch(pairs, model=MODEL, timeout=300):
    """커버 한 배치 판독 — 실패 = {}(fail-soft · 다음 회차가 다시 시도한다)."""
    if not pairs:
        return {}
    prompt = PROMPT % '\n'.join('- ' + p for _, p in pairs)
    cmd = ['claude', '-p', '--model', model, '--safe-mode',
           '--allowedTools', 'Read',
           '--disallowedTools', 'Write,Edit,NotebookEdit,Bash,Task,WebFetch,WebSearch',
           '--max-turns', str(len(pairs) + 4)]
    p, rc, err = run_claude(cmd, prompt, timeout=timeout, source='covocr')
    if rc != 0 or not p or not (p.stdout or '').strip():
        print('커버 판독 실패(rc=%s): %s' % (rc, (err or '')[-300:]), file=sys.stderr)
        return {}
    return parse(p.stdout, [mid for mid, _ in pairs])


def run(limit=BATCH * MAX_BATCH, model=MODEL, timeout=300, force=()):
    led = _load_ledger()
    force = set(force or ())
    todo = [(mid, path) for mid, path in _owned_covers()
            if (mid in force or mid not in led) and os.path.isfile(path)]
    if not todo:
        print('커버 제목: 새로 읽을 표지 없음(원장 %d건)' % len(led))
        return 0
    todo = todo[:max(1, int(limit or BATCH))]
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
    add = 0
    for i in range(0, len(todo), BATCH):
        got = read_batch(todo[i:i + BATCH], model=model, timeout=timeout)
        for mid, t in got.items():
            # head/sub = 참고 분해(줄 수는 가변 = 첫 줄 / 나머지 전부) · 소비처가 쓰는 값은 항상 `t` 전문이다.
            # ⚠ 260812 실측 = 「흰 줄 + 초록 줄」 2단으로 단정한 첫 판이 3단 카드에서 순서를 뒤집고 가운데
            #   줄을 잃었다(「지방 취업 청년 지원금 '더블 인상' || 월 30만 원이 80만 원으로,」 = 읽는 순서 역전).
            #   진범은 모델이 아니라 양식을 고정으로 못박은 프롬프트였다 → 색·줄수 단정을 걷어냈다.
            head, _, sub = t.partition(SEP)
            led[mid] = {'t': t, 'head': head.strip(), 'sub': sub.strip(), 'at': now}
            add += 1
        if not got:
            break   # 한 배치가 통째로 실패하면 그 회차는 접는다(같은 사유로 남은 배치도 실패 = 낭비)
    if add:
        _save_ledger(led)
    print('커버 제목: %d/%d장 판독 · 원장 %d건' % (add, len(todo), len(led)))
    return 0


if __name__ == '__main__':
    a, limit, model, timeout, force = sys.argv[1:], BATCH * MAX_BATCH, MODEL, 300, []
    i = 0
    while i < len(a):
        if a[i] == '--limit' and i + 1 < len(a):
            limit = max(1, int(a[i + 1] or BATCH)); i += 2
        elif a[i] == '--model' and i + 1 < len(a):
            model = a[i + 1]; i += 2
        elif a[i] == '--timeout' and i + 1 < len(a):
            timeout = max(30, int(a[i + 1] or 300)); i += 2
        elif a[i] == '--force':
            i += 1
            while i < len(a) and not a[i].startswith('--'):
                force.append(a[i]); i += 1
        else:
            i += 1
    try:
        run(limit=limit, model=model, timeout=timeout, force=force)
    except Exception as e:   # fail-soft 절대 — 표지 판독 실패가 수집·요약 파이프를 죽이면 안 된다
        print('커버 판독 예외: %s: %s' % (type(e).__name__, e), file=sys.stderr)
    raise SystemExit(0)
