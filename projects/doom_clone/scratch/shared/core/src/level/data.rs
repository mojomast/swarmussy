use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Level {
    pub id: u32,
    pub name: String,
    pub width: u32,
    pub height: u32,
    pub nodes: Vec<LevelNode>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LevelNode {
    pub id: u32,
    pub x: i32,
    pub y: i32,
    pub t: String,
}
