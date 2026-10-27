
pub fn hello() -> &'static str {
    "Hello from Rust!"
}

pub mod cards;
pub mod deck;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hello() {
        assert_eq!(hello(), "Hello from Rust!");
    }
}