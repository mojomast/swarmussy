pub struct Asset {
    pub id: u32,
    pub name: String,
}

impl Asset {
    pub fn new(id: u32, name: &str) -> Self { Asset { id, name: name.to_string() } }
}
