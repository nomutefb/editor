#!/usr/bin/env python3
"""모델 승격 일괄 치환기 — 정본 = `shared/models.json` (운영자 260725 한 수).

왜: 모델 ID가 20+ 호출처(스크립트·워크플로·functions·뷰어·지침·법령)에 리터럴로 흩어져 있다.
   승격(260725 Opus 4.8→5 실측 = 22곳)마다 전수 grep = 빠뜨림·시행착오. 런타임 결합(전 호출처가
   이 json을 읽게)은 Cloudflare Functions·정적 뷰어에 파일 접근이 없어 불가 + 20+ 스크립트의
   모델 해석 변경 = 고위험 → 「정본 1곳 + 기계 치환(이 파일) + 드리프트 게이트(check_model_ids)」.

사용:
    python3 shared/apply_models.py opus claude-opus-6 "Opus 6" "오퍼스 6"
    python3 shared/apply_models.py opus claude-opus-6 "Opus 6" "오퍼스 6" --dry   # 미리보기만
    python3 shared/apply_models.py sonnet claude-sonnet-6                          # 표시명 생략 = ID만 교체
    python3 shared/apply_models.py fable --follow opus                             # 대행 시작 = 페이블 티어가 오퍼스 티어 모델을 쓴다
    python3 shared/apply_models.py fable claude-fable-6 "Fable 6" "페이블 6"        # 대행 해제 = 페이블 티어가 새 페이블로 복귀

절차(정본 = 법령 제26조 ③): 이 명령 → `git diff` 확인 → `python3 shared/check_refs.py`(rc=0) → 커밋.
치환 범위·제외 = models.json `scan`(원장·보고서·동결본은 과거 기록이라 제외 = CLAUDE.md [11]).

경계 가드(치환·게이트 공용 — check_refs.check_model_ids가 이 파일의 id_rx·name_rx를 그대로 쓴다):
  · 표시명 뒤 인원 접미사(`Opus 5인`·`Opus 5명`)는 모델명이 아니다. 인원은 항상 '명'으로 써라 — '인'은 모델명과 붙어 읽힌다.
  · 옛 이름이 새 이름의 앞머리인 승격(`claude-opus-5` ⊂ `claude-opus-5-5` · `Opus 5` ⊂ `Opus 5.5`)에서 새 이름을
    옛 이름으로 오인하지 않게, 버전이 이어지는 자리(숫자 · `.숫자` · `-영숫자`)는 경계로 보지 않는다(260923 실측:
    가드 없이 승격하면 게이트가 새 이름 전부를 '구세대 잔존'으로 막고, 다음 승격에선 `claude-opus-5-5-5`가 된다).

대행(follow · 운영자 260923 "페이블 5.1과 오퍼스 5.5 중엔 5.5 · 새 페이블 티어가 나오면 비용이 높아도 페이블"):
  한 티어(페이블)가 다른 티어(오퍼스)의 모델을 대신 쓰는 상태. 두 티어가 같은 ID·표시명을 공유하면 글자 치환으로는
  한쪽만 못 고른다 → 대행 티어의 값은 models.json `keyed` 자리(`<티어>_MODEL` 변수 · `<티어>: '표시명'` 라벨)에만 두고
  호출처는 그 변수만 쓴다(`tiers.<티어>.sites` · check_model_ids 강제).
  · 따라가는 대상(오퍼스) 승격 = 글자 치환이 대행 자리까지 같이 바꾸고(같은 값) 정본의 대행 티어 값도 동기.
  · 대행 시작·해제 = 키 기준 치환만(글자 치환 없음) · 공유 중인 옛 이름은 은퇴 등재 안 함(상대 티어가 아직 쓴다).
"""

import os
import re
import sys
import json
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, 'shared', 'models.json')
# 표시명 뒤 = 인원 접미사(인·명) · 버전 연장(`Opus 5` ⊂ `Opus 5.5`·`Opus 50`) → 모델명 아님
NAME_GUARD = r'(?![인명0-9]|\.[0-9])'
# ID 뒤 = 버전 연장(`claude-opus-5` ⊂ `claude-opus-5-5`·`claude-opus-5.1`·`claude-opus-50`) → 다른 모델 · 문장 끝 마침표·따옴표·괄호는 경계
ID_GUARD = r'(?![0-9a-z]|[-.][0-9a-z])'
# ID 본체 = 끝의 `.`·`-`는 ID가 아니다(문장 끝 마침표 `claude-opus-5.` = 경계 — ID_GUARD와 같은 규약)
ID_PAT = r'claude-[a-z]+-[0-9](?:[0-9a-z]|[.-](?=[0-9a-z]))*'


def id_rx(model_id):
    return re.compile(re.escape(model_id) + ID_GUARD)


def name_rx(name):
    return re.compile(re.escape(name) + NAME_GUARD)


def keyed_id_rx(tier):
    """대행 자리의 ID — 셸 `FABLE_MODEL="${FABLE_MODEL:-<ID>}"` · 파이썬 `os.environ.get("FABLE_MODEL", "<ID>")`."""
    return re.compile(r'(\b%s_MODEL\b[^\n]{0,24}?)(%s)' % (re.escape(tier.upper()), ID_PAT))


def keyed_label_rx(tier):
    """티어 키 라벨 — `fable: 'Opus 5.5'`(viewer/nm-models.js 사전 · api/sb.js DIRECTOR_NM · edit.html CLIP_NM)."""
    return re.compile(r"(\b%s:\s*')([^'\n]*)(')" % re.escape(tier))


def load():
    with open(REG, encoding='utf-8') as f:
        return json.load(f)


def save(reg):
    with open(REG, 'w', encoding='utf-8') as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)
        f.write('\n')


def read(path):
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def scan_files(reg):
    """models.json scan.include - scan.exclude 를 해석해 대상 파일 절대경로 목록을 준다."""
    inc, exc = reg['scan']['include'], reg['scan']['exclude']
    drop = set()
    for g in exc:
        drop |= {os.path.abspath(p) for p in glob.glob(os.path.join(ROOT, g), recursive=True)}
    out = []
    for g in inc:
        for p in glob.glob(os.path.join(ROOT, g), recursive=True):
            ap = os.path.abspath(p)
            if not os.path.isfile(ap) or ap in drop:
                continue
            # 제외 글롭이 디렉터리를 가리킨 경우(_versions/** 등)도 접두사로 차단
            if any(ap.startswith(d + os.sep) for d in drop):
                continue
            out.append(ap)
    return sorted(set(out))


def keyed_paths(reg, kind=None):
    """키 기준 치환 자리(models.json `keyed.ids`·`keyed.labels`) 절대경로 — kind 생략 = 둘 다."""
    kd = reg.get('keyed', {})
    kinds = [kind] if kind else ['ids', 'labels']
    return sorted({os.path.join(ROOT, p) for k in kinds for p in kd.get(k, [])})


def name_variants(en):
    """표시명 대소문자 변형 3종 — 산문에서 `Opus 5`·`opus 5`·`OPUS 5`가 섞여 쓰인다(실측)."""
    head, _, tail = en.partition(' ')
    return [en, '%s %s' % (head.lower(), tail), '%s %s' % (head.upper(), tail)]


def build_pairs(old, new):
    """(정규식, 새 문자열) 목록 — ID·표시명 모두 경계 가드(인원 접미사·버전 연장)."""
    pairs = [(id_rx(old['id']), new['id'])] if old['id'] != new['id'] else []
    for key in ('en', 'ko'):
        o, n = old.get(key), new.get(key)
        if not o or not n or o == n:
            continue
        if key == 'en':
            for ov, nv in zip(name_variants(o), name_variants(n)):
                pairs.append((name_rx(ov), nv))
        else:
            pairs.append((name_rx(o), n))
    return pairs


def rewrite(paths, subs, dry):
    """paths 각각에 subs([(정규식, 대체 문자열|함수)]) 적용 → (파일 수, 곳 수) · dry = 파일 미변경."""
    files = hits = 0
    for path in paths:
        src = read(path)
        if src is None:
            continue
        out, n_all = src, 0
        for rx, repl in subs:
            out, n = rx.subn(repl, out)
            n_all += n
        if n_all:
            files += 1
            hits += n_all
            print('   %-58s %d곳' % (os.path.relpath(path, ROOT), n_all))
            if not dry:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(out)
    return files, hits


def retire(reg, values):
    retired = list(reg.get('retired', []))
    for v in values:
        if v and v not in retired:
            retired.append(v)
    reg['retired'] = retired
    return len(retired)


def _apply_vendor(reg, key, new_id, dry):
    """벤더(비-Claude 종량제) 교체 — ID 1종만 치환. 표시명·은퇴 등재 없음(공급사 ID는 회수되면 문서 잔존도 오해를 부른다)."""
    v = reg['vendors'][key]
    old_id = v['id']
    if old_id == new_id:
        print('변경 없음 — 벤더[%s] 정본이 이미 %s' % (key, old_id))
        return 0
    print('벤더 교체: [%s] %s → %s%s' % (key, old_id, new_id, '  (--dry = 미리보기)' if dry else ''))
    files, hits = rewrite(scan_files(reg), [(id_rx(old_id), new_id)], dry)
    if dry:
        print('— 미리보기 끝: %d파일 %d곳(파일 미변경 · 정본 미갱신).' % (files, hits))
        return 0
    reg['vendors'][key] = dict(v, id=new_id)
    save(reg)
    print('✅ %d파일 %d곳 치환 + 정본 갱신. 다음: git diff → python3 shared/check_refs.py (rc=0) → 커밋' % (files, hits))
    print('   ⚠️ 종량제 축 = 새 ID가 실제 서빙되는지 실호출 1회로 확인해라(모델 부재 = 런타임 실패).')
    return 0


def promote(reg, tier, old, new, dry):
    """일반 승격 = 글자 치환(경계 가드) + 이 티어를 대행 중인 티어 값 동기 + 옛 값 은퇴 등재."""
    tiers = reg['tiers']
    if old['id'] == new['id'] and old.get('en') == new.get('en') and old.get('ko') == new.get('ko'):
        print('변경 없음 — 정본이 이미 %s(%s / %s)' % (old['id'], old.get('en'), old.get('ko')))
        return 0
    followers = [k for k, t in tiers.items() if t.get('follow') == tier]
    # 같은 ID를 쓰는 다른 티어 = 대행만 허용 — 아니면 글자 치환이 그 티어 호출처까지 바꾼다
    clash = [k for k, t in tiers.items() if k != tier and k not in followers and t['id'] == old['id']]
    if clash:
        print('❌ 옛 ID %s를 [%s] 티어도 쓴다(대행 아님) — 글자 치환이 그 티어까지 바꾼다. '
              '같은 모델을 계속 쓸 거면 `python3 shared/apply_models.py %s --follow %s`로 먼저 묶어라.'
              % (old['id'], ', '.join(clash), clash[0], tier))
        return 2
    taken = [k for k, t in tiers.items() if k != tier and t['id'] == new['id']]
    if taken:
        print('❌ 새 ID %s는 [%s] 티어가 이미 쓴다 — 같은 모델을 쓰게 하려면 `python3 shared/apply_models.py %s --follow %s`(대행).'
              % (new['id'], ', '.join(taken), tier, taken[0]))
        return 2

    pairs = build_pairs(old, new)
    print('승격: [%s] %s → %s  ·  표시명 %s → %s / %s → %s%s'
          % (tier, old['id'], new['id'], old.get('en'), new.get('en'), old.get('ko'), new.get('ko'),
             '  (--dry = 미리보기)' if dry else ''))
    files, hits = rewrite(sorted(set(scan_files(reg)) | set(keyed_paths(reg))), pairs, dry)
    if followers:
        print('   대행 티어 동기: %s (대행 자리 값이 같아 위 치환에 포함)' % ', '.join(followers))
    if dry:
        print('— 미리보기 끝: %d파일 %d곳(파일 미변경 · 정본 미갱신).' % (files, hits))
        return 0

    # 정본 갱신 + 대행 티어 동기 + 구세대 은퇴 등재(게이트가 이 목록으로 '빠뜨림'을 잡는다)
    tiers[tier] = new
    for k in followers:
        tiers[k] = dict(tiers[k], id=new['id'], en=new.get('en'), ko=new.get('ko'))
    n = retire(reg, [old['id']] + (name_variants(old['en']) if old.get('en') else []) + [old.get('ko')])
    save(reg)
    print('✅ %d파일 %d곳 치환 + 정본 갱신(구세대 %d종 은퇴 등재).' % (files, hits, n))
    print('   다음: git diff 확인 → python3 shared/check_refs.py (rc=0) → 커밋')
    return 0


def follow(reg, tier, target, dry):
    """대행 시작 = tier가 target의 모델을 쓴다. 키 기준 치환만(대행 자리·라벨) + 옛 ID 은퇴(표시명은 산문 이력으로 남김)."""
    tiers = reg['tiers']
    if tier not in tiers or target not in tiers or tier == target:
        print('❌ 대행: 티어 키 확인 — %s → %s (티어 = %s)' % (tier, target, ', '.join(tiers)))
        return 2
    if tiers[target].get('follow'):
        print('❌ 대행 대상 [%s]도 대행 중 — 1단만 허용(연쇄 대행은 승격 때 추적이 끊긴다)' % target)
        return 2
    if any(t.get('follow') == tier for t in tiers.values()):
        print('❌ [%s]를 대행 중인 티어가 있다 — 대행 티어를 또 대행시키면 연쇄가 된다' % tier)
        return 2
    cur, lead = tiers[tier], tiers[target]
    if cur.get('follow') == target:
        print('변경 없음 — [%s]는 이미 [%s] 대행(%s)' % (tier, target, cur['id']))
        return 0
    subs_id = [(keyed_id_rx(tier), lambda m: m.group(1) + lead['id'])]
    subs_lb = [(keyed_label_rx(tier), lambda m: m.group(1) + lead['en'] + m.group(3))] if lead.get('en') else []

    # 호출처가 옛 ID를 아직 직접 쓰면 대행 불가 — 글자 치환을 안 하므로 그 호출처만 옛 모델에 남는다
    ids_paths = keyed_paths(reg, 'ids')
    old_rx, left = id_rx(cur['id']), []
    for path in sorted(set(scan_files(reg)) | set(keyed_paths(reg))):
        src = read(path)
        if src is None:
            continue
        if path in ids_paths:
            for rx, repl in subs_id:
                src = rx.sub(repl, src)
        if old_rx.search(src):
            left.append(os.path.relpath(path, ROOT))
    if left:
        print('❌ 대행 불가 — 아래 파일이 옛 ID %s를 직접 쓴다. 호출처는 `%s_MODEL` 변수로 바꾸고(정본 = models.json tiers.%s.sites) '
              '산문은 티어 이름으로 고친 뒤 다시:' % (cur['id'], tier.upper(), tier))
        for p in left:
            print('   -', p)
        return 2

    print('대행: [%s] %s(%s) → [%s] 모델 %s(%s)%s'
          % (tier, cur['id'], cur.get('en'), target, lead['id'], lead.get('en'), '  (--dry = 미리보기)' if dry else ''))
    f1, h1 = rewrite(ids_paths, subs_id, dry)
    f2, h2 = rewrite(keyed_paths(reg, 'labels'), subs_lb, dry)
    if dry:
        print('— 미리보기 끝: 대행 자리 %d곳 · 라벨 %d곳(파일 미변경 · 정본 미갱신).' % (h1, h2))
        return 0
    new = dict(cur, id=lead['id'], en=lead.get('en'), ko=lead.get('ko'), follow=target)
    if not cur.get('follow'):
        new['원래'] = {k: cur[k] for k in ('id', 'en', 'ko') if cur.get(k)}
    tiers[tier] = new
    if not any(k != tier and t['id'] == cur['id'] for k, t in tiers.items()):
        retire(reg, [cur['id']])   # 옛 ID만 — 표시명(페이블 5 등)은 티어의 원래 이름이라 산문(도입 이유·이력)에 남긴다
    save(reg)
    print('✅ 대행 자리 %d곳 · 라벨 %d곳 + 정본 갱신([%s] follow=%s · 원래 = %s).' % (h1, h2, tier, target, new.get('원래', {}).get('id')))
    print('   다음: git diff 확인 → python3 shared/check_refs.py (rc=0) → 커밋')
    return 0


def unfollow(reg, tier, new, dry):
    """대행 해제 = tier가 자기 모델(new)로 복귀. 키 기준 치환만 · 공유하던 옛 값은 대상 티어가 계속 쓰므로 은퇴 등재 안 함."""
    tiers = reg['tiers']
    cur = tiers[tier]
    lead = cur['follow']
    if new['id'] == tiers[lead]['id']:
        print('변경 없음 — [%s]는 이미 [%s] 대행으로 %s를 쓴다' % (tier, lead, new['id']))
        return 0
    if not new.get('en') or new.get('en') == cur.get('en'):
        print('❌ 대행 해제엔 새 표시명이 필요 — 예: python3 shared/apply_models.py %s %s "Fable 6" "페이블 6"' % (tier, new['id']))
        return 2
    taken = [k for k, t in tiers.items() if k != tier and t['id'] == new['id']]
    if taken:
        print('❌ 새 ID %s는 [%s] 티어가 이미 쓴다 — 같은 모델이면 `--follow %s`(대행)로.' % (new['id'], ', '.join(taken), taken[0]))
        return 2
    subs_id = [(keyed_id_rx(tier), lambda m: m.group(1) + new['id'])]
    subs_lb = [(keyed_label_rx(tier), lambda m: m.group(1) + new['en'] + m.group(3))]
    print('대행 해제: [%s] %s(%s · %s 대행) → %s(%s)%s'
          % (tier, cur['id'], cur.get('en'), lead, new['id'], new['en'], '  (--dry = 미리보기)' if dry else ''))
    f1, h1 = rewrite(keyed_paths(reg, 'ids'), subs_id, dry)
    f2, h2 = rewrite(keyed_paths(reg, 'labels'), subs_lb, dry)
    if dry:
        print('— 미리보기 끝: 대행 자리 %d곳 · 라벨 %d곳(파일 미변경 · 정본 미갱신).' % (h1, h2))
        return 0
    t = {k: v for k, v in cur.items() if k not in ('follow', '원래')}
    t.update(id=new['id'], en=new['en'], ko=new.get('ko') or cur.get('ko'))
    tiers[tier] = t
    save(reg)
    print('✅ 대행 자리 %d곳 · 라벨 %d곳 + 정본 갱신. 공유하던 옛 값(%s)은 [%s] 티어가 계속 쓰므로 은퇴 등재 안 함.'
          % (h1, h2, cur['id'], lead))
    print('   산문 속 대행 서술("현재 … 대행")은 손으로 정리 — 후보 파일:')
    for path in scan_files(reg):
        src = read(path)
        if src and '대행' in src:
            print('   -', os.path.relpath(path, ROOT))
    return 0


def main(argv):
    dry = '--dry' in argv
    if '--follow' in argv:
        i = argv.index('--follow')
        if i != 2 or i + 1 >= len(argv) or argv[i + 1].startswith('--'):
            print(__doc__)
            return 2
        return follow(load(), argv[1], argv[i + 1], dry)
    args = [a for a in argv[1:] if not a.startswith('--')]
    if len(args) < 2:
        print(__doc__)
        return 2
    tier, new_id, rest = args[0], args[1], args[2:]
    reg = load()
    vend = reg.get('vendors', {})
    if tier not in reg['tiers'] and tier not in vend:
        print('❌ 모르는 키: %s — 티어 = %s · 벤더 = %s' % (tier, ', '.join(reg['tiers']), ', '.join(vend) or '없음'))
        return 2
    if tier in vend:   # 벤더(비-Claude 종량제) = 표시명 없이 ID만 · 은퇴 등재도 안 한다(공급사가 구 ID를 회수해 문서 잔존도 위험)
        return _apply_vendor(reg, tier, new_id, dry)
    old = dict(reg['tiers'][tier])
    new = dict(old, id=new_id)
    if rest:
        new['en'] = rest[0]
    if len(rest) > 1:
        new['ko'] = rest[1]
    if old.get('follow'):
        return unfollow(reg, tier, new, dry)
    return promote(reg, tier, old, new, dry)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
