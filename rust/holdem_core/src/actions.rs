
#[derive(Debug, Copy, Clone, PartialEq, Eq, Hash)]
pub enum Action {
    Call,
    Check,
    Bet,
    Raise,
    Fold,
}

pub fn describe_action(action: &Action) -> String {
    match action {
        Action::Fold => String::from("Fold"),
        Action::Call => String::from("Call"),
        Action::Check => String::from("Check"),
        Action::Bet => String::from("Bet"),
        Action::Raise => String::from("Raise"),
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fold() {
        let my_action = Action::Fold;

        assert_eq!(describe_action(&my_action),"Fold");

    }
    
    #[test]
    fn test_call() {
        let my_action = Action::Call;

        assert_eq!(describe_action(&my_action),"Call");

    }

    #[test]
    fn test_check() {
        let my_action = Action::Check;

        assert_eq!(describe_action(&my_action),"Check");

    }

    #[test]
    fn test_raise() {
        let my_action = Action::Raise;

        assert_eq!(describe_action(&my_action),"Raise");

    }

    #[test]
    fn test_bet() {
        let my_action = Action::Bet;

        assert_eq!(describe_action(&my_action),"Bet");

    }

}