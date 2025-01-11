'use client';

import { useState } from 'react';

export default function LandingVideo() {
  const [isPaused, setIsPaused] = useState(false);

  return (
    <video
      src="/demo.mp4"
      autoPlay
      loop
      muted
      playsInline
      className="w-full rounded-2xl shadow-lg transition-opacity duration-300 group-hover:opacity-80"
      onClick={(e) => {
        setIsPaused(!isPaused);
        isPaused ? e.currentTarget.play() : e.currentTarget.pause();
      }}
    />
  );
}
