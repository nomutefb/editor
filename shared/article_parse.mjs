// 요약 md(queue/*.md) 해석 정본 — 빌드(build-viewer.mjs)와 라이브 요약 서빙(functions/api/feedlive.js)이 같은 규칙으로 읽는다(260924 · 운영자 「추천 순서대로」 ⑥).
//   두 곳이 따로 파싱하면 빌드 전 라이브 행과 빌드 후 정적 행의 제목·필드가 어긋난다 = 한 벌.
export function parseFrontmatter(raw) {
  // 첫 두 '---' 사이를 단순 key: "value" 파싱(중첩 없음).
  // frontmatter 앞 모델 사족 허용 — 첫 '---' 줄부터 파싱(구버전 파일 호환).
  const start = raw.search(/^---\s*$/m);
  if (start > 0) raw = raw.slice(start);
  let m = raw.match(/^---\s*\n([\s\S]*?)\n---\s*\n?([\s\S]*)$/);
  // 닫는 '---' 누락 방어(260704 실측: ask 렌터카 — LLM이 frontmatter 닫는 표식을 생략) — 여는 '---'만 있으면
  // key: value 필드 줄이 끝나는 지점(빈 줄·본문 헤딩)에서 관용 분리. 정상(여닫이 다 있음) 파일은 위 정규식이 이미
  // 매치하므로 이 분기는 안 탐 = 기존 동작 100% 불변, 깨진 케이스만 구제. 생성 측(ask/analyze.sh)의 닫는 '---' 보증과 한 쌍.
  if (!m && /^---\s*\n/.test(raw)) {
    const lines = raw.replace(/^---\s*\n/, '').split('\n');
    let i = 0;
    while (i < lines.length && /^[A-Za-z_][A-Za-z0-9_]*:/.test(lines[i])) i++;   // 콜론 뒤 공백 요구 제거 = 아래 필드파서(:\s* 관용)와 경계 일치 — 빈 값 필드(`reporter:`)에서 스캔이 멈춰 후속 url까지 body로 새던 것 봉합(평의회 260713 ⑧)
    if (i > 0) m = [null, lines.slice(0, i).join('\n'), lines.slice(i).join('\n')];   // 필드가 하나라도 있을 때만(진짜 본문만 있는 파일은 raw 그대로)
  }
  if (!m) return { meta: {}, body: raw };
  const meta = {};
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^([A-Za-z_]+):\s*(.*)$/);
    if (!kv) continue;
    let v = kv[2].trim().replace(/^"(.*)"$/, '$1').replace(/\\"/g, '"');
    if (/^'.*'$/.test(v)) v = v.slice(1, -1).replace(/''/g, "'");   // YAML 작은따옴표 래핑도 벗김(제목에 쌍따옴표 포함 시 모델이 '…' 사용 → 래핑째 노출되던 것 · '' 이스케이프 복원 · 260703 실측)
    meta[kv[1]] = v;
  }
  return { meta, body: m[2].trim() };
}

// 타이틀 선두 토픽 이모지 스트립 — frontmatter title:은 '기사 제목 원문 그대로'(이모지 없음)가 정본인데
// LLM이 간혹(~4%) H1 주제 이모지(🌊/🏛/📉 등)를 title 까지 복사 → 카드에 노출. 선두 이모지·변형선택자(FE0F)·
// ZWJ·키캡·뒤따르는 공백만 결정적 제거(본문/H1 헤드라인 이모지는 불변 · 기존 저장분도 빌드 때 즉시 구제 · 운영자 260625).
export function stripLeadEmoji(s) {
  return String(s || '').replace(/^[\p{Extended_Pictographic}\p{Emoji_Modifier}\u{FE0F}\u{200D}\u{20E3}\s]+/u, '').trimStart();
}
