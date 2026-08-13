// nm-styles.js — 화풍·세부 화풍 **단일정본**.
//
// ⚠ 왜 파일로 뽑았나(운영자 260813 「화풍 선택 칸 · 이미지 스튜디오의 여러 화풍 - 세부화풍을
//   따라하면 될것 같다」) = 콘티 화면이 같은 목록을 쓰는데, 사본을 두면 한쪽에 화풍을 더한 날
//   나머지가 조용히 낡는다(이 레포가 반복해 겪은 드리프트). 목록은 서버 STYLE_SUB 와도 키를
//   맞춰야 해서 갈리면 화면에 있는 화풍이 서버에서 없는 값이 된다.
// ⚠ 값·주석은 index 원본 **그대로 옮긴 것**이다(창작 0 · 한 글자도 안 고쳤다).
// ⚠ window 에도 붙인다 — 최상위 const 는 window 속성이 **안 된다**(nm-svg.js 260806 실사고와
//   같은 축: 분리 파일의 상수가 상시 undefined 가 됐다). 이름으로도, window 로도 닿게 둔다.

const GENI_SUB = {   // 화풍별 세부 분기 — 서버 STYLE_SUB와 동일 키 · 260707 2차 확장(운영자 "게키카도 여러 화풍·라이브러리 참고 보완" — 어휘 = /k 라이브러리 실코드)
  photo: [['auto', '기본'], ['film', '필름'], ['bw', '흑백'], ['cinedoc', '시네다큐'], ['newsreel', '뉴스릴']],
  webtoon: [['auto', '기본'], ['gekiga', '게키카'], ['hardboiled', '하드보일드'], ['jidai', '시대극'], ['sunjung', '순정'], ['chibi', '명랑']],   // 대표만(운영자 260707 3차 "기본+분열 4~5") · 한국웹툰 = 전 화풍 공통 토글(#geniKweb)로 이동
  cartoon: [['auto', '기본'], ['brush', '붓선'], ['flat', '플랫'], ['woodcut', '판화']],
  watercolor: [['auto', '기본'], ['bleed', '번짐'], ['fine', '세밀'], ['sumuk', '수묵'], ['gouache', '과슈'], ['oil', '유화']],
  cinematic: [['auto', '기본'], ['noir', '누아르'], ['neon', '네온'], ['film35', '35mm'], ['expressionism', '표현주의']],
  illust: [['auto', '기본'], ['riso', '리소'], ['paper', '페이퍼'], ['anime', '애니'], ['retro80', '레트로80']],
  iso3d: [['auto', '기본'], ['clay', '클레이'], ['lowpoly', '로우폴리'], ['diorama', '디오라마']],
  pictogram: [['auto', '기본'], ['line', '라인'], ['blueprint', '청사진']],
};
const GENI_STYLE_MAIN = [['webtoon', '극화'], ['watercolor', '수채'], ['photo', '실사']];   // 나열 선두 3종(구 상용 노출축 — 260713 전량 나열 전환 뒤엔 순서 의미만) · 기본 극화(운영자 260710)
const GENI_STYLE_ETC = [['cartoon', '만평'], ['cinematic', '시네마틱'], ['illust', '일러스트'], ['iso3d', '3D'], ['pictogram', '픽토'], ['lego', '레고']];   // 나열 후미 6종(구 '기타' 선택박스 수납 — 운영자 260713 "칸 남는 곳 다 이렇게" 전량 노출 전환) · 레고 = 세부 화풍 없음(운영자 260727 "얘는 세부 화풍없이" → GENI_SUB 키 미신설 = 세부 레일 '자동' 단독)
const GENI_ALL_STYLES = [...GENI_STYLE_MAIN, ...GENI_STYLE_ETC];

window.GENI_SUB = GENI_SUB;
window.GENI_STYLE_MAIN = GENI_STYLE_MAIN;
window.GENI_STYLE_ETC = GENI_STYLE_ETC;
window.GENI_ALL_STYLES = GENI_ALL_STYLES;
