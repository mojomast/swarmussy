use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Monster {
    pub id: u32,
    pub kind: String,
    pub health: i32,
    pub position: (f32, f32),
}
