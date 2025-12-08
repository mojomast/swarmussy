#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Cell(pub i32, pub i32);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Level {
    pub width: usize,
    pub height: usize,
    pub cells: Vec<Cell>,
}

impl Level {
    pub fn new(width: usize, height: usize) -> Self {
        let mut cells = Vec::with_capacity(width * height);
        for y in 0..height {
            for x in 0..width {
                cells.push(Cell(x as i32, y as i32));
            }
        }
        Level { width, height, cells }
    }
}
