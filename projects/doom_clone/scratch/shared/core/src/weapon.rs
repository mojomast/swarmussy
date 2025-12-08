use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Weapon {
    pub id: u32,
    pub name: String,
    pub damage: f32,
    pub range: f32,
}
