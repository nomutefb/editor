import React, {useEffect, useState} from 'react';
import {
  AbsoluteFill,
  continueRender,
  delayRender,
  Easing,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {T} from './tokens';

// 뉴스 요약 카드 1건 → 10초 세로 모션 카드.
// 모션 톤 = 하우스 곡선 계승(감쇠 스프링 = 튐 없음 · 게이지류 = 센 ease-out) — 뉴스 소재라 절제 우선.
export const defaultCard = {
  title: '노뮤트 코드 영상 시제품',
  hook: '코드가 그린 첫 영상',
  summary: '이 영상은 편집 프로그램 없이 코드만으로 그려졌습니다. 내용은 큐 카드에서 자동으로 옮겨 담습니다.',
  facts: ['글자·도형·움직임 전부 코드가 계산합니다', '틀 하나에 내용만 갈아끼우면 됩니다', '깃허브 러너에서 자동으로 뽑을 수 있습니다'],
  media: '노뮤트',
  date: '2026-08-13',
  tag: '',
};
type Card = typeof defaultCard;

const PAD = 96; // 좌우 여백(1080폭 기준 내용폭 888)

export const NewsCard: React.FC<Card> = ({hook, summary, facts, media, date, tag}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames, width, height} = useVideoConfig();

  // 프리텐다드(가변) 로드 완료까지 렌더 대기 — 폴백 활자로 첫 프레임이 찍히는 것 차단.
  const [fontHandle] = useState(() => delayRender('pretendard'));
  useEffect(() => {
    const f = new FontFace(
      'Pretendard Variable',
      `url(${staticFile('fonts/pretendard.woff2')}) format('woff2-variations')`,
      {weight: '45 920'},
    );
    f.load()
      .then((loaded) => {
        (document.fonts as FontFaceSet).add(loaded);
        continueRender(fontHandle);
      })
      .catch(() => continueRender(fontHandle)); // 글꼴 실패 = 시스템 한글 폴백으로 계속(빈 화면보다 낫다)
  }, [fontHandle]);

  // 감쇠 스프링(튐 0) — 등장 공용
  const up = (f0: number) =>
    spring({frame: frame - f0, fps, config: {damping: 200}, durationInFrames: 34});
  const rise = (f0: number, dist = 26) => ({
    opacity: up(f0),
    transform: `translateY(${(1 - up(f0)) * dist}px)`,
  });

  // 상단 진행선(재생 위치 표시 · 선형)
  const progress = interpolate(frame, [0, durationInFrames - 1], [0, 100]);
  // 제목 밑 강조선 스윕(센 ease-out = 게이지 곡선 취지 계승)
  const sweep = interpolate(frame, [58, 92], [0, 100], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  // 전체 미세 드리프트(정지화면 느낌 방지 · 1% 이내)
  const drift = interpolate(frame, [0, durationInFrames], [1, 1.012]);

  const words = hook.split(' ');

  return (
    <AbsoluteFill style={{background: T.spaceBg, fontFamily: T.font, color: T.fg}}>
      {/* 상단 글로우 = 우주톤(--space-bg + --space-hi-rgb 라디얼) */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(120% 55% at 50% -12%, rgba(${T.spaceHiRgb},.55), rgba(${T.spaceHiRgb},0) 62%)`,
        }}
      />
      {/* 진행선 */}
      <div style={{position: 'absolute', top: 0, left: 0, height: 6, width: `${progress}%`, background: T.accent}} />

      <AbsoluteFill style={{transform: `scale(${drift})`}}>
        {/* 브랜드 줄 */}
        <div style={{position: 'absolute', top: 88, left: PAD, right: PAD, display: 'flex', alignItems: 'center', gap: 18, ...rise(4)}}>
          <span style={{fontWeight: 800, fontSize: 34, letterSpacing: 7, color: T.fg}}>NOMUTE</span>
          <span style={{width: 10, height: 10, borderRadius: T.rPill, background: T.accent, display: 'inline-block'}} />
          <span style={{fontSize: 26, color: T.mut}}>AI 뉴스 요약</span>
          {tag ? (
            <span
              style={{
                marginLeft: 'auto', fontSize: 24, fontWeight: 700, color: T.accent,
                border: `2px solid rgba(${T.accentRgb},.35)`, borderRadius: T.rPill, padding: '8px 22px',
              }}
            >
              {tag}
            </span>
          ) : null}
        </div>

        {/* 제목(단어 단위 순차 등장) */}
        <div style={{position: 'absolute', top: 250, left: PAD, right: PAD}}>
          <h1 style={{margin: 0, fontSize: 78, lineHeight: 1.28, fontWeight: 800, letterSpacing: -0.5}}>
            {words.map((w, i) => (
              <span key={i} style={{display: 'inline-block', whiteSpace: 'pre', ...rise(16 + i * 3, 34)}}>
                {w + (i < words.length - 1 ? ' ' : '')}
              </span>
            ))}
          </h1>
          <div style={{marginTop: 34, height: 8, width: `${sweep}%`, maxWidth: 320, background: T.accent, borderRadius: 4}} />
        </div>

        {/* 한줄 요약 */}
        <div style={{position: 'absolute', top: 760, left: PAD, right: PAD, ...rise(100)}}>
          <div style={{fontSize: 27, fontWeight: 800, color: T.accent, letterSpacing: 2, marginBottom: 22}}>한줄 요약</div>
          <p style={{margin: 0, fontSize: 36, lineHeight: 1.62, color: T.fg, opacity: 0.94}}>{summary}</p>
        </div>

        {/* 확인된 사실 3줄(순차) */}
        <div style={{position: 'absolute', top: 1210, left: PAD, right: PAD}}>
          <div style={{fontSize: 27, fontWeight: 800, color: T.accent, letterSpacing: 2, marginBottom: 26, ...rise(146)}}>
            확인된 사실
          </div>
          {facts.slice(0, 3).map((t, i) => (
            <div key={i} style={{display: 'flex', gap: 20, marginBottom: 30, ...rise(158 + i * 26)}}>
              <span style={{flex: 'none', width: 12, height: 12, borderRadius: T.rPill, background: T.accent, marginTop: 16}} />
              <span style={{fontSize: 31, lineHeight: 1.55, color: T.fg, opacity: 0.9}}>{t}</span>
            </div>
          ))}
        </div>

        {/* 출처 줄 */}
        <div
          style={{
            position: 'absolute', bottom: 84, left: PAD, right: PAD, paddingTop: 30,
            borderTop: `2px solid ${T.line}`, display: 'flex', justifyContent: 'space-between',
            fontSize: 25, color: T.mut, ...rise(252),
          }}
        >
          <span>출처 {media}</span>
          <span>{date} · 노뮤트 AI 요약</span>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
