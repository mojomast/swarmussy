export const Toolbar = () => {
  const onClick = (label: string) => {
    console.log('Toolbar click:', label);
  };
  return (
    <div style={{ display: 'flex', gap: '8px', padding: '8px', background: '#1a2142', borderRadius: 6 }}>
      <button className="btn" onClick={() => onClick('Play')}>Play</button>
      <button className="btn" onClick={() => onClick('Stop')}>Stop</button>
      <button className="btn" onClick={() => onClick('Save')}>Save</button>
      <button className="btn" onClick={() => onClick('Load')}>Load</button>
      <button className="btn" onClick={() => onClick('Edit')}>Edit</button>
    </div>
  );
};
