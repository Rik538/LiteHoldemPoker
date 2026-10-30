
pub fn hello() -> &'static str {
    "Hello from Rust!"
}

pub mod cards;
pub mod deck;
pub mod actions;
pub mod state;
pub mod engine;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hello() {
        assert_eq!(hello(), "Hello from Rust!");
    }
}