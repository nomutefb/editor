// ys_out 라이브 서빙(260928) — 유튜브 숏폼 워크플로가 R2에 단계마다 게시하는 progress.json·result.json 과
// 맥 표시등(_mac/heartbeat.json)을 배포 전에 즉시 서빙 · 미스 = 정적 폴백(공용부 = functions/_r2live.js 단일정본)
import { r2live } from '../_r2live.js';
export const onRequestGet = (ctx) => r2live('ys_out', ctx);
