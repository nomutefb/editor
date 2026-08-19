// Cloudflare Pages Function — 웹푸시 구독 저장/해제 → push/subscriptions.json 커밋(GitHub Contents API).
// breaking-judge 워크플로가 이 파일을 읽어 pywebpush로 긴급 속보 발송. env: GH_TOKEN(contents:write).
// ⚠️ 구독(엔드포인트)이 레포에 저장됨 — 발송은 VAPID 비밀키 필수라 노출돼도 제3자 발송 불가(가드). 비공개 원하면 KV로 이전.
const REPO = 'nomutefb/editor', FILE = 'push/subscriptions.json';

// ⚠ 260819 확장(운영자 «구독 기기도 알 수 있는지 · 안드로이드 오에스 버전이나 브라우저라도» + «비활성화 시키면 그쪽에는 푸시를 안하는거로»)
//   구판은 {endpoint, keys, ts} 만 담아서 화면에 「등록일」밖에 못 보여줬다 — 주소만으로는 브라우저 계열(fcm=크롬 계열 / apple=사파리 / mozilla=파이어폭스)까지가 한계다.
//   → 등록 요청이 들고 오는 **브라우저 신분 문자열(User-Agent)** 을 같이 담는다. 거기에 안드로이드 버전·기기 모델·브라우저 이름과 판이 전부 들어 있다.
//     (예: `Mozilla/5.0 (Linux; Android 14; SM-S928N) … Chrome/126.0.0.0 Mobile Safari/537.36` → 안드로이드 14 · SM-S928N · 크롬 126)
//   ⚠ 이 값은 요청 헤더에서 서버가 직접 읽는다(클라이언트가 보내는 값이 아니라 위조 여지가 한 겹 적다) ·
//     크롬 계열이 주는 더 정확한 정보(플랫폼 판·모델)는 화면이 `hint` 로 같이 올려 보완한다(있으면 우선).
//   ⚠ **기존 5대는 소급이 안 된다** — 그때 안 받아둔 값이라 없다. 알림을 껐다 켜면 그때부터 붙는다.
//   액션 = subscribe · unsubscribe · list(목록 · 열쇠는 빼고) · toggle(발송 켜고 끄기 = off 표식) · remove(삭제).

export async function onRequestPost({ request, env }) {
  const json = (o, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { 'content-type': 'application/json' } });
  if (!env.GH_TOKEN) return json({ error: 'GH_TOKEN 미설정' }, 500);

  let body; try { body = await request.json(); } catch { return json({ error: '잘못된 요청' }, 400); }
  const ACTIONS = ['subscribe', 'unsubscribe', 'list', 'toggle', 'remove'];
  const action = ACTIONS.includes(body.action) ? body.action : 'subscribe';
  const sub = body.subscription;
  const target = String(body.endpoint || (sub && sub.endpoint) || '');   // list 는 대상 불요 · toggle·remove 는 endpoint 로 지목
  if (action === 'subscribe' && (!sub || !sub.endpoint)) return json({ error: '구독 정보 없음' }, 400);
  if (['unsubscribe', 'toggle', 'remove'].includes(action) && !target) return json({ error: '대상 없음' }, 400);
  const ua = String(request.headers.get('user-agent') || '').slice(0, 400);   // 서버가 직접 읽는다 = 위조 여지 한 겹 적음
  const hint = (body.hint && typeof body.hint === 'object') ? {
    plat: String(body.hint.plat || '').slice(0, 40),        // 크롬 계열 고정밀 = 플랫폼(Android·Windows…)
    pv: String(body.hint.pv || '').slice(0, 20),            // 그 판(15.0 …)
    model: String(body.hint.model || '').slice(0, 60),      // 기기 모델(SM-S928N …)
    br: String(body.hint.br || '').slice(0, 60),            // 브라우저 이름·판
  } : null;

  const H = {
    authorization: `Bearer ${env.GH_TOKEN}`, accept: 'application/vnd.github+json',
    'user-agent': 'nomute-viewer', 'x-github-api-version': '2022-11-28',
  };
  const url = `https://api.github.com/repos/${REPO}/contents/${FILE}`;

  for (let attempt = 0; attempt < 4; attempt++) {
    // 현재 구독 목록 읽기(+ sha)
    let arr = [], sha;
    const g = await fetch(`${url}?ref=main`, { headers: H });
    if (g.ok) {
      const j = await g.json(); sha = j.sha;
      try { arr = JSON.parse(atob((j.content || '').replace(/\n/g, ''))); } catch { arr = []; }
      if (!Array.isArray(arr)) arr = [];
    } else if (g.status !== 404) {
      return json({ error: `GitHub read ${g.status}` }, 502);
    }
    if (action === 'list') {   // 읽기 전용 — 열쇠(keys)는 절대 안 내보낸다(그 값이 있으면 제3자가 그 기기로 발송을 시도할 수 있다)
      return json({ items: arr.filter(s => s && s.endpoint).map(s => ({
        id: s.endpoint.slice(-24), ts: s.ts || 0, ua: s.ua || '', hint: s.hint || null, off: !!s.off,
        host: (() => { try { return new URL(s.endpoint).host; } catch { return ''; } })(),
      })) });
    }
    const idx = arr.findIndex(s => s && s.endpoint && (s.endpoint === target || s.endpoint.slice(-24) === target));
    if (action === 'toggle') {                       // 발송 켜고 끄기 — 구독은 남기고 표식만 뒤집는다(운영자 260819 «비활성화 시키면 그쪽에는 푸시를 안하는거로»)
      if (idx < 0) return json({ error: '대상 없음' }, 404);
      arr[idx] = { ...arr[idx], off: !arr[idx].off };
    } else if (action === 'remove') {                // 목록에서 아예 뺀다
      if (idx < 0) return json({ error: '대상 없음' }, 404);
      arr.splice(idx, 1);
    } else {
      // 같은 endpoint 제거(중복·갱신) → subscribe면 추가
      const prev = idx >= 0 ? arr[idx] : null;
      arr = arr.filter(s => s && s.endpoint && s.endpoint !== target);
      if (action === 'subscribe') arr.push({
        endpoint: sub.endpoint, keys: sub.keys, ts: (prev && prev.ts) || Date.now(),   // 재등록이면 최초 등록일 보존
        ...(ua ? { ua } : {}), ...(hint ? { hint } : {}), ...(prev && prev.off ? { off: true } : {}),
      });
    }

    const bytes = new TextEncoder().encode(JSON.stringify(arr));
    let bin = ''; for (const b of bytes) bin += String.fromCharCode(b);
    const put = await fetch(url, {
      method: 'PUT', headers: H,
      body: JSON.stringify({ message: `push: 구독 ${action}`, content: btoa(bin), branch: 'main', ...(sha ? { sha } : {}) }),
    });
    if (put.ok) return json({ ok: true, count: arr.length });
    if (put.status === 409) continue;   // sha 경합 → 재시도
    return json({ error: `GitHub write ${put.status}: ${(await put.text()).slice(0, 200)}` }, 502);
  }
  return json({ error: '경합 — 재시도 실패' }, 409);
}
