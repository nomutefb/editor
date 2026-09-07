// Three-way collection merge. Only changes relative to the caller's base are applied.
export function mergeItems(current, base, desired, cap) {
  const key = x => x.id || `${x.ts}:${x.kw || ''}`;
  const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const map = a => {
    const m = new Map(a.map(x => [key(x), x]));
    if (m.size !== a.length) throw new Error('중복된 항목 번호가 있어. 새로고침 후 다시 저장해줘.');
    return m;
  };
  const c = map(current), b = map(base), d = map(desired);
  for (const [id, old] of b) {
    const next = d.get(id), live = c.get(id);
    if (eq(old, next)) continue;
    if (!next) {
      if (live && !eq(old, live)) throw new Error('다른 기기에서 수정한 항목은 삭제하지 않았어.');
      c.delete(id);
    } else {
      if (!live) throw new Error('다른 기기에서 삭제한 항목이야.');
      const merged = { ...live };
      for (const field of Object.keys(next)) {
        if (eq(old[field], next[field])) continue;
        if (!eq(live[field], old[field]) && !eq(live[field], next[field]))
          throw new Error('다른 기기에서 같은 항목을 수정했어.');
        merged[field] = next[field];
      }
      c.set(id, merged);
    }
  }
  for (const [id, item] of d) {
    if (b.has(id)) continue;
    if (c.has(id) && !eq(c.get(id), item)) throw new Error('같은 번호의 다른 항목이 있어.');
    c.set(id, item);
  }
  if (c.size > cap) throw new Error(`최대 ${cap}개까지 저장할 수 있어. 기존 항목은 보존했어.`);
  // Preserve the caller's ordering and append independently added remote items.
  return [...d.keys(), ...c.keys()].filter((id, i, a) => c.has(id) && a.indexOf(id) === i).map(id => c.get(id));
}
