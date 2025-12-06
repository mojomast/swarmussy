import React, { useEffect, useRef, useState } from 'react';

export default function GameCanvas() {
  const canvasRef = useRef(null);
  const [status, setStatus] = useState('idle');

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    // Simple placeholder animation
    let t = 0;
    const id = setInterval(() => {
      t += 0.1;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#222';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#0f0';
      ctx.fillRect((canvas.width/2) - 10, (canvas.height/2) - 10, 20, 20);
    }, 50);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="game-area">
      <canvas ref={canvasRef} width={640} height={360} style={{ border: '1px solid #555' }} />
      <div className="status">Status: idle</div>
      <button onClick={() => setStatus('starting')}>Start</button>
    </div>
  );
}
