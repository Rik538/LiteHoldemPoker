use crate::cards::{Card,Suit,Rank};
use crate::actions::Action;
use crate::state::Street;
use crate::observed_state::ObservedState;

use serde_json::json;


fn card_to_code(card: &Card) -> String {
    let suit: &str = match card.suit {
        Suit::Club => "C",
        Suit::Diamond => "D",
        Suit::Heart => "H",
        Suit::Spade => "S",
    };

    let rank = match card.rank {
        Rank::Ace => "A",
        Rank::King => "K",
        Rank::Queen => "Q",
        Rank::Jack => "J",
        Rank::Ten => "T"
    };

    format!("{}{}",rank,suit)

}

fn action_to_code(action: &Action) -> &'static str {
    match action{
        Action::Bet => "BET",
        Action::Call => "CALL",
        Action::Check => "CHECK",
        Action::Fold => "FOLD",
        Action::Raise => "RAISE"
    }
}

fn street_to_code(street: Street) -> &'static str {
    match street {
        Street::Flop =>"FLOP",
        Street::Preflop=>"PREFLOP",
        Street::River=>"RIVER",
        Street::Turn=>"TURN"
    }
}

pub fn observation_to_json(
    observation: &ObservedState<'_>,
) -> Result<String, serde_json::Error> {

    let private_cards: Vec<String> = observation.private_cards
        .iter()
        .map(card_to_code)
        .collect();

    let public_cards: Vec<String> = observation.public_cards
        .iter()
        .map(card_to_code)
        .collect();

    let legal_actions: Vec<&str> = observation.legal_actions
        .iter()
        .flatten()
        .map(action_to_code)
        .collect();

    let json_value = json!({
        "player": observation.player,
        "current_player": observation.current_player,
        "button_player": observation.button_player,
        "private_cards": private_cards,
        "public_cards": public_cards,
        "street": street_to_code(observation.street),
        "pot": observation.pot,
        "amount_to_call": observation.amount_to_call,
        "raises_this_round": observation.raises_this_round,
        "legal_actions": legal_actions,
    });

    serde_json::to_string(&json_value)
}




#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{json, Value};

    #[test]
    fn test_observation_to_json() {
        let observation = ObservedState::test_state();

        let json_string =
            observation_to_json(&observation).unwrap();

        let data: Value =
            serde_json::from_str(&json_string).unwrap();

        assert_eq!(data["player"], 0);
        assert_eq!(data["current_player"], 0);
        assert_eq!(data["button_player"], 0);

        assert_eq!(data["private_cards"], json!(["AH", "KD"]));
        assert_eq!(data["public_cards"], json!([]));

        assert_eq!(data["street"], "PREFLOP");
        assert_eq!(data["pot"], 3);
        assert_eq!(data["amount_to_call"], 1);
        assert_eq!(data["raises_this_round"], 0);

        assert_eq!(
            data["legal_actions"],
            json!(["FOLD", "CALL", "RAISE"])
        );
    }
}