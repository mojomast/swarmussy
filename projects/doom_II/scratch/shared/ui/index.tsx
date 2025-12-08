import React, { useEffect, useState, useRef } from 'react';

export default function HUD() {
  const [fps, setFps] = useState(0);
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    let mounted = true;
    let frames = 0;
    let last = performance.now();
    const loop = () => {
      frames++;
      const now = performance.now();
      if (now - last >= 500) {
        if (mounted) setFps(Math.round((frames * 1000) / (now - last)));
        last = now;
        frames = 0;
      }
      requestAnimationFrame(loop);
    };
    loop();
    return () => { mounted = false; };
  }, []);
  return <div ref={ref} className="hud">FPS: {fps}</div>;
}
