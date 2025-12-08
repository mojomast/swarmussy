// Engine facade for core crate re-exporting common data models

pub struct Engine {
    pub name: String,
}

impl Engine {
    pub fn new(name: &str) -> Self {
        Engine { name: name.to_string() }
    }
}

// Re-export core data models for engine consumers
pub use super::level::{Level, LevelNode};
pub use super::weapon::Weapon;
pub use super::monster::Monster;
