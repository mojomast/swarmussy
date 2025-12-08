use shared_models::{Level, Cell, Weapon, Monster};

#[test]
fn level_new_dimensions() {
    let lvl = Level::new(3, 2);
    assert_eq!(lvl.width, 3);
    assert_eq!(lvl.height, 2);
    assert_eq!(lvl.cells.len(), 6);
}

#[test]
fn weapon_basic_fields() {
    let w = Weapon { name: "Pistol", damage: 12 };
    assert_eq!(w.name, "Pistol");
    assert_eq!(w.damage, 12);
}

#[test]
fn monster_basic_fields() {
    let m = Monster { name: "Goblin", health: 30 };
    assert_eq!(m.name, "Goblin");
    assert_eq!(m.health, 30);
}
