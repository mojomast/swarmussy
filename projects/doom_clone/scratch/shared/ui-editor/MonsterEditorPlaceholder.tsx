import React from 'react';
import type { Monster } from '../types/EngineTypes';

export type MonsterEditorPlaceholderProps = {
  item?: Monster;
  onChange?: (patch: Partial<Monster>) => void;
};

const MonsterEditorPlaceholder: React.FC<MonsterEditorPlaceholderProps> = ({ item, onChange }) => {
  const [name, setName] = React.useState(item?.name ?? '');
  const [hp, setHp] = React.useState(item?.hp ?? 10);
  const onName = (e) => { setName(e.target.value); onChange?.({ name: e.target.value }); };
  const onHp = (e) => { setHp(parseInt(e.target.value || '0', 10)); onChange?.({ hp: parseInt(e.target.value || '0', 10) }); };
  return (
    <div className="panel">
      <h3>Monster</h3>
      <label>Name</label>
      <input value={name} onChange={onName} />
      <label>HP</label>
      <input type="number" value={hp} onChange={onHp} />
    </div>
  );
};

export { MonsterEditorPlaceholder };
export default MonsterEditorPlaceholder;
