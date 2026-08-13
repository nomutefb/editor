import React from 'react';
import {Composition} from 'remotion';
import {NewsCard, defaultCard} from './NewsCard';

// 뉴스 요약 카드 → 세로 숏폼(1080×1920 · 30fps · 10초). 내용은 --props=out/props.json 으로 주입(scripts/card2props.mjs 산출).
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="newscard"
      component={NewsCard}
      durationInFrames={300}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={defaultCard}
    />
  );
};
