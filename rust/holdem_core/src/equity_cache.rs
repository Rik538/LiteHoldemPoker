
use rusqlite::{params, Connection, OptionalExtension, Result};
use crate::equity_builder::{EquityResult,calculate_equity_result, get_remaining_cards};
use crate::cards::{create_deck,Card,cards_to_mask};

pub fn open_cache(path: &str) -> Result<Connection> {
    Connection::open(path)
}

pub fn insert_equity(conn: &Connection,private_mask: u32, public_mask:u32, equity_result:&EquityResult) -> Result<()> {
    conn.execute(
        "INSERT INTO equity_cache 
        (private_mask, board_mask, wins, losses, splits, total)
        VALUES (?1, ?2, ?3, ?4, ?5, ?6)
        ON CONFLICT(private_mask, board_mask) DO NOTHING", 
        params![private_mask,public_mask,equity_result.wins,equity_result.losses,equity_result.splits,equity_result.total]
    )?;
    Ok(())
}

pub fn build_equity_cache_board(conn: &mut Connection,board_size: usize) -> Result<()>{

    const BATCH_SIZE: usize = 5_000;

    let mut tx = conn.transaction()?;
    let mut batch_count = 0;
    let mut total_processed = 0;

    //building the hand cards and board cards
    let cards = create_deck();

    for i in 0..cards.len() {
        for j in (i + 1)..cards.len() {
            // Evaluate one completed board
            let player_cards: [Card; 2] = [cards[i], cards[j]];

            let remaining_deck: [Card;18] = get_remaining_cards(player_cards)
                .ok_or_else(|| {
                    rusqlite::Error::InvalidParameterName(
                        "missing remaining cards for generated player hand".to_string(),
                    )
                })?;

            match board_size {
                5 => {
                    for i in 0..remaining_deck.len() {
                        for j in (i + 1)..remaining_deck.len() {
                            for k in (j + 1)..remaining_deck.len() {
                                for l in (k + 1)..remaining_deck.len() {
                                    for m in (l + 1)..remaining_deck.len() {
                                        let board_cards = [
                                            remaining_deck[i],
                                            remaining_deck[j],
                                            remaining_deck[k],
                                            remaining_deck[l],
                                            remaining_deck[m],
                                        ];

                                        let equity_result = calculate_equity_result(
                                            &player_cards,
                                            &board_cards,
                                        );

                                        insert_equity(
                                            &tx,
                                            cards_to_mask(&player_cards),
                                            cards_to_mask(&board_cards),
                                            &equity_result,
                                        )?;

                                        batch_count += 1;
                                        total_processed += 1;

                                        if batch_count >= BATCH_SIZE {
                                            tx.commit()?;

                                            println!(
                                                "Board size {}: processed {} records",
                                                board_size, total_processed
                                            );

                                            tx = conn.transaction()?;
                                            batch_count = 0;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                4 => {
                    for i in 0..remaining_deck.len() {
                        for j in (i + 1)..remaining_deck.len() {
                            for k in (j + 1)..remaining_deck.len() {
                                for l in (k + 1)..remaining_deck.len() {
                                    let board_cards = [
                                        remaining_deck[i],
                                        remaining_deck[j],
                                        remaining_deck[k],
                                        remaining_deck[l],
                                    ];

                                    let equity_result = calculate_equity_result(
                                        &player_cards,
                                        &board_cards,
                                    );

                                    insert_equity(
                                        &tx,
                                        cards_to_mask(&player_cards),
                                        cards_to_mask(&board_cards),
                                        &equity_result,
                                    )?;

                                    batch_count += 1;
                                    total_processed += 1;

                                    if batch_count >= BATCH_SIZE {
                                        tx.commit()?;

                                        println!(
                                            "Board size {}: processed {} records",
                                            board_size, total_processed
                                        );

                                        tx = conn.transaction()?;
                                        batch_count = 0;
                                    }
                                }
                            }
                        }
                    }
                }
                3 => {
                    for i in 0..remaining_deck.len() {
                        for j in (i + 1)..remaining_deck.len() {
                            for k in (j + 1)..remaining_deck.len() {
                                let board_cards = [
                                    remaining_deck[i],
                                    remaining_deck[j],
                                    remaining_deck[k],
                                ];

                                let equity_result = calculate_equity_result(
                                    &player_cards,
                                    &board_cards,
                                );

                                insert_equity(
                                    &tx,
                                    cards_to_mask(&player_cards),
                                    cards_to_mask(&board_cards),
                                    &equity_result,
                                )?;

                                batch_count += 1;
                                total_processed += 1;

                                if batch_count >= BATCH_SIZE {
                                    tx.commit()?;

                                    println!(
                                        "Board size {}: processed {} records",
                                        board_size, total_processed
                                    );

                                    tx = conn.transaction()?;
                                    batch_count = 0;
                                }
                            }
                        }
                    }
                }
                0 => {
                    let board_cards: [Card; 0] = [];

                    let equity_result = calculate_equity_result(
                        &player_cards,
                        &board_cards,
                    );

                    insert_equity(
                        &tx,
                        cards_to_mask(&player_cards),
                        cards_to_mask(&board_cards),
                        &equity_result,
                    )?;

                    batch_count += 1;
                    total_processed += 1;

                    if batch_count >= BATCH_SIZE {
                        tx.commit()?;

                        println!(
                            "Board size {}: processed {} records",
                            board_size, total_processed
                        );

                        tx = conn.transaction()?;
                        batch_count = 0;
                    }
                },
                _ => panic!("Invalid board_size"),
            };

        }
    }


    tx.commit()?;

    println!(
        "Finished board size {}: {} records processed",
        board_size, total_processed
    );

    Ok(())
}

pub fn get_equity(
    conn: &Connection,
    private_mask: u32,
    board_mask: u32,
) -> Result<Option<EquityResult>> {
    conn.query_row(
        "SELECT wins, losses, splits, total
         FROM equity_cache
         WHERE private_mask = ?1 AND board_mask = ?2",
        params![private_mask, board_mask],
        |row| {
            Ok(EquityResult {
                wins: row.get(0)?,
                losses: row.get(1)?,
                splits: row.get(2)?,
                total: row.get(3)?,
            })
        },
    )
    .optional()
}

pub fn build_equity_cache(conn: &mut Connection) -> Result<()> {

    for board_size in [5, 4, 3, 0] {
        build_equity_cache_board(conn, board_size)?;
    }

    Ok(())
}







#[cfg(test)]
mod tests {
    use super::*;
    use crate::cards::{Card,Rank,Suit,cards_to_mask};



    #[test]
    fn test_open_cache() {
        let path = "/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/equity_cache_rust.sqlite";

        let conn = open_cache(path).unwrap();

        let table_count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = ?1",
                ["equity_cache"],
                |row| row.get(0),
            )
            .unwrap();

        assert_eq!(table_count, 1);
    }


    #[test]
    fn test_insert_and_query() {
        let conn = Connection::open_in_memory().unwrap();

        // Use your existing CREATE TABLE SQL
        conn.execute_batch(include_str!("/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/schema.sql"))
            .unwrap();

        // Define player_cards and public_cards here
        let player_cards = [
            Card {
                rank: Rank::Ace,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::King,
                suit: Suit::Diamond,
            },
        ];

        let public_cards = [
            Card {
                rank: Rank::Queen,
                suit: Suit::Spade,
            },
            Card {
                rank: Rank::Jack,
                suit: Suit::Club,
            },
            Card {
                rank: Rank::Ten,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::Ten,
                suit: Suit::Diamond,
            },
            Card {
                rank: Rank::Ace,
                suit: Suit::Spade,
            },
        ];

        let equity_result =
            calculate_equity_result(&player_cards, &public_cards);

        let private_mask = cards_to_mask(&player_cards);
        let board_mask = cards_to_mask(&public_cards);

        insert_equity(
            &conn,
            private_mask,
            board_mask,
            &equity_result,
        )
        .unwrap();

        let retrieved = get_equity(
            &conn,
            private_mask,
            board_mask,
        )
        .unwrap();

        assert_eq!(retrieved, Some(equity_result));
    }

    #[test]
    fn test_missing_equity() {
        let conn = Connection::open_in_memory().unwrap();

        conn.execute_batch(include_str!("/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/schema.sql"))
            .unwrap();

        let result = get_equity(&conn, 1, 2).unwrap();

        assert_eq!(result, None);
    }

    #[ignore]
    #[test]
    fn test_board_0() -> Result<()>{
        let mut conn = Connection::open_in_memory().unwrap();

        // Use your existing CREATE TABLE SQL
        conn.execute_batch(include_str!("/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/schema.sql"))?;


        build_equity_cache_board(&mut conn, 0)?;


        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM equity_cache WHERE board_mask = 0",
            [],
            |row| row.get(0),
        )?;

        assert_eq!(count, 190);

        Ok(())

    }
    
    #[test]
    #[ignore] // Prevents this expensive test running with normal tests
    fn test_board_3() -> Result<()> {
        use std::time::Instant;

        let mut conn = Connection::open_in_memory()?;

        conn.execute_batch(include_str!(
            "/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/schema.sql"
        ))?;

        // Start timing
        let start = Instant::now();

        build_equity_cache_board(&mut conn, 3)?;

        let elapsed = start.elapsed().as_secs_f64();

        // Check stored records
        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM equity_cache",
            [],
            |row| row.get(0),
        )?;

        assert_eq!(count, 155_040);

        // Performance statistics
        let records_per_sec = count as f64 / elapsed;

        println!("\n--- Flop Cache Benchmark ---");
        println!("Total records:     {}", count);
        println!("Total time:        {:.4}s", elapsed);
        println!("Records/sec:       {:.0}", records_per_sec);
        println!("Time per record:   {:.4}ms", elapsed * 1000.0 / count as f64);

        let (min_total, max_total): (i64, i64) = conn.query_row(
            "SELECT MIN(total), MAX(total) FROM equity_cache",
            [],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )?;

        assert_eq!(min_total, 8190);
        assert_eq!(max_total, 8190);

        // Previously validated flop hand
        let player_cards = [
            Card { suit: Suit::Heart, rank: Rank::Ace },
            Card { suit: Suit::Diamond, rank: Rank::King },
        ];

        let public_cards = [
            Card { suit: Suit::Spade, rank: Rank::Queen },
            Card { suit: Suit::Club, rank: Rank::Jack },
            Card { suit: Suit::Heart, rank: Rank::Ten },
        ];

        // Generate the cache keys
        let private_mask = cards_to_mask(&player_cards);
        let board_mask = cards_to_mask(&public_cards);

        // Retrieve the stored result
        let stored_result = get_equity(
            &conn,
            private_mask,
            board_mask,
        )?
        .expect("Validated flop equity not found in cache");

        // Expected results from previous validation
        let expected_result = EquityResult {
            wins: 1944,
            losses: 3252,
            splits: 2994,
            total: 8190,
        };

        // Compare entire structs
        assert_eq!(stored_result, expected_result);

        // Verify equity score
        assert!(
            (stored_result.equity() - 0.42014652).abs() < 0.00000001
        );

        println!("Validated flop equity matches stored SQLite result!");

        Ok(())

        
    }


    #[test]
    #[ignore] // Only run when explicitly requested
    fn test_build_persistent_equity_cache() -> Result<()> {
        use std::time::Instant;

        const DB_PATH: &str =
            "/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/equity_cache_rust.sqlite";

        // Open the persistent SQLite database
        let mut conn = open_cache(DB_PATH)?;

        // Ensure the table exists
        conn.execute_batch(include_str!(
            "/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/schema.sql"
        ))?;

        println!("\n=== Building Persistent Equity Cache ===");
        println!("Database: {}", DB_PATH);

        let start = Instant::now();

        // Generates all board sizes: 0, 3, 4, 5
        // Each board size uses your 5,000-record transactions
        build_equity_cache(&mut conn)?;

        let elapsed = start.elapsed().as_secs_f64();

        // Verify total database records
        let count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM equity_cache",
            [],
            |row| row.get(0),
        )?;

        assert_eq!(count, 2_364_550);

        // Verify all 190 preflop records exist
        let preflop_count: i64 = conn.query_row(
            "SELECT COUNT(*) FROM equity_cache WHERE board_mask = 0",
            [],
            |row| row.get(0),
        )?;

        assert_eq!(preflop_count, 190);

        // Verify a known flop result
        let player_cards = [
            Card::new(Suit::Heart, Rank::Ace),
            Card::new(Suit::Diamond, Rank::King),
        ];

        let public_cards = [
            Card::new(Suit::Spade, Rank::Queen),
            Card::new(Suit::Club, Rank::Jack),
            Card::new(Suit::Heart, Rank::Ten),
        ];

        let stored_result = get_equity(
            &conn,
            cards_to_mask(&player_cards),
            cards_to_mask(&public_cards),
        )?
        .expect("Validated flop result missing from database");

        assert_eq!(stored_result.wins, 1944);
        assert_eq!(stored_result.losses, 3252);
        assert_eq!(stored_result.splits, 2994);
        assert_eq!(stored_result.total, 8190);

        // Display benchmark summary
        println!("\n--- Full Equity Cache Summary ---");
        println!("Total records:     {}", count);
        println!("Total time:        {:.2}s", elapsed);
        println!("Total minutes:     {:.2}", elapsed / 60.0);
        println!("Records/sec:       {:.0}", count as f64 / elapsed);
        println!("Time per record:   {:.4}ms", elapsed * 1000.0 / count as f64);
        println!("Validation:        PASSED");

        // Close connection before checking file size
        drop(conn);

        let file_size = std::fs::metadata(DB_PATH)
            .unwrap()
            .len();

        println!("Database size:     {:.2} MB", file_size as f64 / 1_000_000.0);

        Ok(())
    }


#[test]
#[ignore] // Run manually because it scans the full database
fn test_persistent_cache_validation() -> rusqlite::Result<()> {
    use rusqlite::OpenFlags;

    let db_path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../cache/equity_cache_rust.sqlite");

    // Read-only: never create or modify the database
    let conn = Connection::open_with_flags(
        db_path,
        OpenFlags::SQLITE_OPEN_READ_ONLY,
    )?;

    // Counters: preflop, flop, turn, river
    let mut counts = [0u64; 4];
    let valid_mask = (1u32 << 20) - 1;

    // Validate every stored record
    {
        let mut stmt = conn.prepare(
            "SELECT private_mask, board_mask, wins, losses, splits, total
             FROM equity_cache"
        )?;

        let mut rows = stmt.query([])?;

        while let Some(row) = rows.next()? {
            let private_mask: u32 = row.get(0)?;
            let board_mask: u32 = row.get(1)?;
            let wins: u32 = row.get(2)?;
            let losses: u32 = row.get(3)?;
            let splits: u32 = row.get(4)?;
            let total: u32 = row.get(5)?;

            // Exactly two private cards
            assert_eq!(private_mask.count_ones(), 2);

            // No private card may appear on the board
            assert_eq!(private_mask & board_mask, 0);

            // No bits outside the 20-card deck
            assert_eq!((private_mask | board_mask) & !valid_mask, 0);

            // Every scenario must have one outcome
            assert_eq!(wins + losses + splits, total);

            // Validate street and scenario count
            let (index, board_size) = match total {
                668_304 => (0, 0),
                8_190   => (1, 3),
                1_092   => (2, 4),
                78      => (3, 5),
                _ => panic!("Unexpected scenario total: {}", total),
            };

            assert_eq!(board_mask.count_ones(), board_size);

            counts[index] += 1;
        }
    }

    // Verify all expected records
    assert_eq!(
        counts,
        [190, 155_040, 581_400, 1_627_920]
    );

    assert_eq!(counts.iter().sum::<u64>(), 2_364_550);

    println!("All record counts and bitmasks validated!");

    // Previously validated player hand
    let player_cards = [
        Card { suit: Suit::Heart, rank: Rank::Ace },
        Card { suit: Suit::Diamond, rank: Rank::King },
    ];

    // Validated board, extended street by street
    let board = [
        Card { suit: Suit::Spade, rank: Rank::Queen },
        Card { suit: Suit::Club, rank: Rank::Jack },
        Card { suit: Suit::Heart, rank: Rank::Ten },
        Card { suit: Suit::Diamond, rank: Rank::Ten },
        Card { suit: Suit::Spade, rank: Rank::Ace },
    ];

    let private_mask = cards_to_mask(&player_cards);

    // Expected results: preflop, flop, turn, river
    let expected_results = [
        (0, EquityResult {
            wins: 286_899,
            losses: 219_102,
            splits: 162_303,
            total: 668_304,
        }),
        (3, EquityResult {
            wins: 1_944,
            losses: 3_252,
            splits: 2_994,
            total: 8_190,
        }),
        (4, EquityResult {
            wins: 270,
            losses: 552,
            splits: 270,
            total: 1_092,
        }),
        (5, EquityResult {
            wins: 21,
            losses: 24,
            splits: 33,
            total: 78,
        }),
    ];

    for (board_size, expected) in expected_results {
        let board_mask = cards_to_mask(&board[..board_size]);

        let stored = get_equity(
            &conn,
            private_mask,
            board_mask,
        )?
        .expect("Expected equity entry missing from cache");

        assert_eq!(
            stored, expected,
            "Equity mismatch for board size {}",
            board_size
        );

        println!("Board size {}: validated!", board_size);
    }

    println!("\n--- Cache Validation Summary ---");
    println!("Preflop:  {} records", counts[0]);
    println!("Flop:     {} records", counts[1]);
    println!("Turn:     {} records", counts[2]);
    println!("River:    {} records", counts[3]);
    println!("Total:    {}", counts.iter().sum::<u64>());
    println!("Validation: PASSED");

    Ok(())
}


}

