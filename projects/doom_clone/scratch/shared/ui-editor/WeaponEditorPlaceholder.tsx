import React from 'react';
import type { Weapon } from '../types/EngineTypes';

export type WeaponEditorPlaceholderProps = {
  item?: Weapon;
  onChange?: (patch: Partial<Weapon>) => void;
};

const WeaponEditorPlaceholder: React.FC<WeaponEditorPlaceholderProps> = ({ item, onChange }) => {
  const [name, setName] = React.useState(item?.name ?? '');
  const [damage, setDamage] = React.useState(item?.damage ?? 0);
  const onName = (e) => { setName(e.target.value); onChange?.({ name: e.target.value }); };
  const onDamage = (e) => { setDamage(parseInt(e.target.value || '0', 10)); onChange?.({ damage: parseInt(e.target.value || '0', 10) }); };
  return (
    <div className="panel">
      <h3>Weapon</h3>
      <label>Name</label>
      <input value={name} onChange={onName} />
      <label>Damage</label>
      <input type="number" value={damage} onChange={onDamage} />
    </div>
  );
};

export { WeaponEditorPlaceholder };
export default WeaponEditorPlaceholder;
