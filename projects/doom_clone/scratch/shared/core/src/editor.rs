pub mod editor {
    pub struct Editor {
        pub name: String,
    }

    impl Editor {
        pub fn new(name: &str) -> Self {
            Editor { name: name.to_string() }
        }
    }
}
