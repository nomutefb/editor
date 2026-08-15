// ly_out 라이브 서빙(260815 코워크) — 맥 잡워커 산출을 배포 전 R2에서 즉시 서빙 · 미스 = 정적 폴백(공용부 = functions/_r2live.js 단일정본)
import { r2live } from '../_r2live.js';
export const onRequestGet = (ctx) => r2live('ly_out', ctx);
