use rand::rngs::StdRng;
use rand::SeedableRng;

fn main() {


    use holdem_core::state::GameState;


    let mut rng = StdRng::seed_from_u64(42); 

    let mut state = GameState::new();

    //println!("{:?}",state);

    state.start_hand(&mut rng);

    

    println!("{:?}",state);   



}
