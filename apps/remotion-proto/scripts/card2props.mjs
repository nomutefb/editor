// 큐 카드(queue/*.md) → 영상 속성(out/props.json) 추출 + 글꼴 준비.
// 인자 없으면 최신 카드 자동 선택(파일명 = 날짜 접두라 사전순 최댓값 = 최신).
// 글꼴은 레포 정본(assets/fonts/pretendard.woff2)을 렌더 시점에 public/으로 복사 — 사본 커밋 0(드리프트 축 소멸).
import {copyFileSync, mkdirSync, readdirSync, readFileSync, writeFileSync} from 'node:fs';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const PROJ = resolve(HERE, '..');
const ROOT = resolve(PROJ, '../..');

function latestQueue() {
  const q = join(ROOT, 'queue');
  const md = readdirSync(q).filter((f) => f.endsWith('.md')).sort();
  if (!md.length) throw new Error('queue/*.md 없음');
  return join(q, md[md.length - 1]);
}

const src = process.argv[2] ? resolve(process.argv[2]) : latestQueue();
const md = readFileSync(src, 'utf8');

// 머리 메타(--- 블록) — "키: \"값\"" 한 줄 문법만 읽는다(카드 정본 문법)
const fm = {};
const fmBlock = md.match(/^---\n([\s\S]*?)\n---/);
if (fmBlock) {
  for (const line of fmBlock[1].split('\n')) {
    const m = line.match(/^(\w+):\s*"(.*)"\s*$/);
    if (m && !(m[1] in fm)) fm[m[1]] = m[2];
  }
}

const h1 = (md.match(/^# (.+)$/m) || [])[1] || fm.title || '';
const hook = h1.replace(/^[^0-9A-Za-z가-힣"'‘“]+/, '').trim(); // 머리 이모지 제거

// 절 나누기 = "## " 머리 기준 통 분할(정규식 여러줄 $ 함정 회피 — 첫 판이 첫 줄에서 끊겨 사실이 1개만 잡히던 실측 봉합)
const section = (name) => {
  const chunk = md.split(/\n(?=## )/).find((c) => c.startsWith('## ') && c.split('\n')[0].includes(name));
  return chunk ? chunk.split('\n').slice(1).join('\n').trim() : '';
};

const summary = (section('한줄 요약').split(/\n\n/)[0] || '').replace(/\*\*/g, '').trim();
// 사실 줄 = 앞 3개 · 각 줄은 첫 문장까지(카드 원문 문장 그대로 = 자르다 만 문장 0) · 꼬리 출처 괄호 제거
const firstSentence = (t) => {
  const m = t.match(/^[\s\S]*?다\.(?=\s|$)/);
  return (m ? m[0] : t).replace(/\s*\([^()]*\)\s*$/, '').trim();
};
const facts = section('Fact')
  .split('\n')
  .filter((l) => l.startsWith('- ') && !l.includes('⚠'))
  .slice(0, 3)
  .map((l) => firstSentence(l.slice(2).replace(/\*\*/g, '').trim()));

const props = {
  title: fm.title || hook,
  hook: hook || fm.title || '',
  summary,
  facts,
  media: fm.media || '',
  date: fm.date || '',
  tag: (fm.tags || '').split(/\s+/).find((t) => t.startsWith('#')) || '',   // #표만 인정("해당 없음" 오탐 봉합)
};

mkdirSync(join(PROJ, 'out'), {recursive: true});
writeFileSync(join(PROJ, 'out', 'props.json'), JSON.stringify(props, null, 1) + '\n');

const fdir = join(PROJ, 'public', 'fonts');
mkdirSync(fdir, {recursive: true});
copyFileSync(join(ROOT, 'assets', 'fonts', 'pretendard.woff2'), join(fdir, 'pretendard.woff2'));

console.log('카드 ←', src);
console.log(JSON.stringify(props, null, 1));
