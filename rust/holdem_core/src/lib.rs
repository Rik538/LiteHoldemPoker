
pub fn hello() -> &'static str {
    "Hello from Rust!"
}

pub mod cards;
pub mod deck;
pub mod actions;
pub mod state;
pub mod engine;
pub mod errors;
pub mod evaluator;
pub mod equity_builder;
pub mod equity_cache;
pub mod equity_cache_access;
pub mod cfr;
pub mod observed_state;

pub mod python_evaluator;


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hello() {
        assert_eq!(hello(), "Hello from Rust!");
    }
}