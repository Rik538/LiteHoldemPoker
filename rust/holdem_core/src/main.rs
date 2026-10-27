use rand::seq::SliceRandom;

fn main() {


    use holdem_core::deck::Deck;





    let mut test_deck = Deck::new();

    let card = test_deck.draw();

    println!("Card: {:?}", card);

    println!("Next Card Idx: {:?}", test_deck);

    //rand::seq::SliceRandom;

    let mut rng = rand::rng();

    let mut vec: Vec<usize> = (0..10).collect();
    println!("{:?}", vec);
    vec.shuffle(&mut rng);
    println!("{:?}", vec);

    



}
