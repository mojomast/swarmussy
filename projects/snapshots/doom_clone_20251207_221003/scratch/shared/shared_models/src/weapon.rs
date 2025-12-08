#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Weapon {
    pub name: &'static str,
    pub damage: i32,
}
