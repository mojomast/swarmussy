export const CanvasPanel = () => {
  return (
    <div style={{ display: 'grid', gridTemplateRows: 'auto 1fr', height: '100%', width: '100%' }}>
      <div className="toolbar" aria-label="canvas-toolbar">
        {/* Toolbar will be fleshed out in integration */}
        <span style={{ color: '#cbd5e6' }}>Canvas</span>
      </div>
      <canvas id="renderSurface" width={800} height={600} aria-label="render-canvas"/>
    </div>
  );
};
