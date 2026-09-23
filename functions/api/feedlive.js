// Cloudflare Pages Function — 빌드 전 새 요약 라이브 서빙(운영자 260924 「추천 순서대로」 ⑥ 요약이 화면에 뜨려면 재배포를 기다려야 하던 것).
// 뉴스 요약 목록(articles.json)은 Pages 빌드(build-viewer.mjs)가 queue/*.md 를 모아 만든다 = 요약 커밋 → 빌드·배포(1~2.5분) 뒤에야 보였다.
// 이 함수 = 지금 배포된 정적 인덱스에 **아직 없는** 새 요약만 저장소 main 에서 바로 읽어 행으로 준다(뷰어 load() 가 덧붙임).
//   · 무엇이 새것인가 = 정적 인덱스 생성 시각(generated) 이후 queue/ 를 건드린 커밋의 추가·수정 md 중 인덱스에 없는 파일.
//     ⚠ 폴더 목록 API(contents)는 1,000개 상한이라(queue 967개 · 260924) 곧 **최신 파일부터** 잘린다 → 커밋 목록 경로를 쓴다.
//   · 행 = build-viewer 와 같은 해석기(shared/article_parse.mjs) · 수집함 매칭 필드(cross·grade·이슈)는 비움 = 다음 빌드가 채운다(일시 행).
//   · 빌드가 따라잡으면 정적 인덱스에 들어가 여기서 자동 제외 = 상태 0 · 유효기간 판단 0(260816 얼어붙은 미러 사고의 반대 구조).
// env: GH_TOKEN(없으면 빈 목록 = 종전 동작 그대로).
import { parseFrontmatter, stripLeadEmoji } from '../../shared/article_parse.mjs';

const REPO = 'nomutefb/editor';
const MAX_NEW = 6;          // 한 번에 덧붙일 새 요약 상한(빌드 적체 폭주 가드)
const MAX_COMMITS = 10;     // 조회할 커밋 상한
const H = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' };   // seal-ok: 응답 헤더 = 엔드포인트 표준(_fire·_rate 는 응답을 안 만드는 보조 모듈이라 비대상)
const out = (rows, why) => new Response(JSON.stringify(why ? { rows, why } : { rows }), { status: 200, headers: H });

export function liveRow(f, raw) {
  const { meta, body } = parseFrontmatter(raw);
  const h1m = (body || '').match(/^#\s+(.+)$/m);
  const tko = stripLeadEmoji(meta.title_ko || '');
  return {
    file: f,
    title: tko || stripLeadEmoji(meta.title) || (h1m ? stripLeadEmoji(h1m[1]) : '') || f.replace(/\.md$/, ''),
    title_orig: tko ? (stripLeadEmoji(meta.title) || '') : '',
    url: meta.url || '', date: meta.date || '', time: meta.time || '', time_est: meta.time_est || '',
    media: meta.media || '', reporter: meta.reporter || '', bias: meta.bias || '', hook: meta.hook || '',
    tags: meta.tags || '', tags_why: meta.tags_why || '', image_query_en: meta.image_query_en || '', image_query: meta.image_query || '',
    category: meta.category || '', breaking: /\[\s*(속보|긴급)\s*\]|긴급\s*속보/.test(meta.title || ''),
    cross: 0, event_key: meta.event_key || '', grade: null, issue: false,
    summary: meta.summary || '', guidelines_version: meta.guidelines_version || '', rev: Number(meta.rev) || 0,
    body, has_body: !!body, _live: 1,
  };
}

export async function onRequestGet({ env, request }) {
  if (!env.GH_TOKEN) return out([], 'no-token');
  let have, gen;
  try {
    const u = new URL(request.url); u.pathname = '/articles.json'; u.search = '';
    const j = await (await env.ASSETS.fetch(new Request(u.toString()))).json();
    have = new Set((j.articles || []).map(a => a.file));
    gen = Date.parse(j.generated || '');
  } catch { return out([], 'static'); }
  if (!gen) return out([], 'static');
  const gh = { authorization: `Bearer ${env.GH_TOKEN}`, 'user-agent': 'nomute-viewer', accept: 'application/vnd.github+json' };
  const since = new Date(gen - 15 * 60000).toISOString();   // 빌드 착수~생성 사이 커밋 여유 15분(이미 든 파일은 have 가 거른다)
  let commits = [];
  try {
    const r = await fetch(`https://api.github.com/repos/${REPO}/commits?sha=main&path=queue&since=${encodeURIComponent(since)}&per_page=${MAX_COMMITS}`,
      { headers: gh, cf: { cacheTtl: 20, cacheEverything: true } });
    if (!r.ok) return out([], 'gh ' + r.status);
    commits = await r.json();
  } catch { return out([], 'gh'); }
  const files = [];
  for (const c of Array.isArray(commits) ? commits : []) {
    try {
      const r = await fetch(`https://api.github.com/repos/${REPO}/commits/${c.sha}`, { headers: gh, cf: { cacheTtl: 3600, cacheEverything: true } });   // 커밋 내용은 불변 = 길게 캐시
      if (!r.ok) continue;
      for (const f of (await r.json()).files || []) {
        const name = String(f.filename || '');
        if (!/^queue\/[^/]+\.md$/.test(name) || f.status === 'removed') continue;
        const base = name.slice(6);
        if (!have.has(base) && !files.includes(base)) files.push(base);
      }
    } catch { /* 한 커밋 실패 = 건너뜀 */ }
  }
  const rows = [];
  for (const f of files.sort().reverse().slice(0, MAX_NEW)) {
    try {
      const r = await fetch(`https://api.github.com/repos/${REPO}/contents/queue/${encodeURIComponent(f)}?ref=main`,
        { headers: { ...gh, accept: 'application/vnd.github.raw' }, cf: { cacheTtl: 20, cacheEverything: true } });
      if (r.ok) rows.push(liveRow(f, await r.text()));
    } catch { /* 한 파일 실패 = 건너뜀 */ }
  }
  return out(rows);
}
