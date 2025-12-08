pub mod level;
pub mod weapon;
pub mod monster;
pub mod engine;
pub mod editor;
pub mod editors;
pub mod assets;

pub use level::{Level, LevelNode};
pub use weapon::Weapon;
pub use monster::Monster;

#[cfg(test)] mod tests {
    use super::*;

    #[test]
    fn test_level_json_roundtrip() {
        let lvl = Level {
            id: 1,
            name: "Demo Level".to_string(),
            width: 8,
            height: 6,
            nodes: vec![LevelNode { id: 1, x: 0, y: 0, t: "floor".to_string() }],
        };
        let json = serde_json::to_string(&lvl).unwrap();
        let dec: Level = serde_json::from_str(&json).unwrap();
        assert_eq!(lvl.id, dec.id);
        assert_eq!(lvl.nodes.len(), dec.nodes.len());
    }
}
