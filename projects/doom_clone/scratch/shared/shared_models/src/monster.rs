#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Monster {
    pub name: &'static str,
    pub health: i32,
}
