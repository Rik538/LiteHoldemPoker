use rusqlite::{params, Connection, OptionalExtension, Result};
use std::path::{Path, PathBuf};
use crate::cards::{Card,cards_to_mask};
use crate::equity_builder::EquityResult;

pub struct Cache {
    #[allow(dead_code)]
    file_path: PathBuf,
    conn: Connection,
}

impl Cache {
    pub fn new(path: impl AsRef<Path>) -> rusqlite::Result<Self> {
        let path = path.as_ref();

        let conn = Connection::open(path)?;

        Ok(Self {
            file_path: path.to_path_buf(),
            conn,
        })
    }
}

impl Cache {

    pub fn get_equity(
        &self,
        private_cards: &[Card],
        board_cards: &[Card],
    ) -> Result<Option<EquityResult>> {

        let private_mask = cards_to_mask(private_cards);
        let board_mask = cards_to_mask(board_cards);

        let mut stmt = self.conn.prepare_cached(
            "SELECT wins, losses, splits, total
            FROM equity_cache
            WHERE private_mask = ?1 AND board_mask = ?2"
        )?;

        stmt.query_row(
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

    pub fn get_equity_score(
        &self,
        private_cards: &[Card],
        board_cards: &[Card],
    ) -> rusqlite::Result<Option<f64>> {
        Ok(self
            .get_equity(private_cards, board_cards)?
            .map(|result| result.equity()))
    }

    pub fn close(self) -> Result<(), (Connection, rusqlite::Error)> {
        self.conn.close()
    }
    
}


//In Memory Hashmap
use std::collections::HashMap;

const TOTAL_EQUITY_STATES: usize = 2_364_550;

pub struct MemoryCache {
    data: HashMap<(u32, u32), EquityResult>,
}

impl MemoryCache {
    pub fn new() -> Self {
        Self {
            data: HashMap::with_capacity(TOTAL_EQUITY_STATES),
        }
    }
}

impl MemoryCache {
    pub fn insert(
        &mut self,
        private_cards: &[Card],
        board_cards: &[Card],
        result: EquityResult,
    ) {
        let private_mask = cards_to_mask(private_cards);
        let board_mask = cards_to_mask(board_cards);

        self.data.insert((private_mask, board_mask), result);
    }

    pub fn get(
        &self,
        private_cards: &[Card],
        board_cards: &[Card],
    ) -> Option<EquityResult> {
        let private_mask = cards_to_mask(private_cards);
        let board_mask = cards_to_mask(board_cards);

        self.data.get(&(private_mask, board_mask)).copied()
    }

    
    pub fn load_from_sqlite(conn: &Connection) -> rusqlite::Result<Self> {
        let mut cache = MemoryCache::new();

        let mut stmt = conn.prepare(
            "SELECT private_mask, board_mask, wins, losses, splits, total
            FROM equity_cache"
        )?;

        let rows = stmt.query_map([], |row| {
            let private_mask: u32 = row.get(0)?;
            let board_mask: u32 = row.get(1)?;

            let result = EquityResult {
                wins: row.get(2)?,
                losses: row.get(3)?,
                splits: row.get(4)?,
                total: row.get(5)?,
            };

            Ok((private_mask, board_mask, result))
        })?;

        for row in rows {
            let (private_mask, board_mask, result) = row?;

            cache.data.insert(
                (private_mask, board_mask),
                result,
            );
        }

        Ok(cache)
    }

    pub fn get_equity_score(
        &self,
        private_cards: &[Card],
        board_cards: &[Card],
    ) -> Option<f64> {
        self.get(private_cards, board_cards)
            .map(|result| result.equity())
    }

    pub fn len(&self) -> usize {
        self.data.len()
    }
}

impl Cache {
    pub fn load_into_memory(&self) -> rusqlite::Result<MemoryCache> {
        MemoryCache::load_from_sqlite(&self.conn)
    }
}



#[cfg(test)]
mod tests {
    use super::*;
    use crate::cards::{Card,Rank,Suit};
    use crate::equity_builder::calculate_equity_result;
    use crate::equity_cache::insert_equity;


     #[test]
    fn test_open_cache() -> Result<()>{
        let path = "/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/equity_cache_rust.sqlite";

        let cache = Cache::new(path)?;

        let table_count: i64 = cache.conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = ?1",
                ["equity_cache"],
                |row| row.get(0),
            )
            .unwrap();

        assert_eq!(table_count, 1);

        Ok(())
    }

    #[test]
    fn test_retrieve() -> Result<()> {

        let path = "/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/equity_cache_rust.sqlite";

        let cache = Cache::new(path)?;

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

        let equity_result: EquityResult = calculate_equity_result(&player_cards, &public_cards);

        let score_result = equity_result.equity();

        let hand_score = cache
            .get_equity_score(&player_cards, &public_cards)?
            .expect("Equity should exist in the completed cache");

        let hand_equity = cache.get_equity(&player_cards, &public_cards)?;

        assert_eq!(hand_equity, Some(equity_result));
        assert_eq!(hand_score, score_result);

        assert_eq!(hand_equity.unwrap().wins,equity_result.wins);
        assert_eq!(hand_equity.unwrap().losses,equity_result.losses);
        assert_eq!(hand_equity.unwrap().splits,equity_result.splits);
        assert_eq!(hand_equity.unwrap().total,equity_result.total);


        Ok(())
    }

    #[test]
    fn test_reversed() -> Result<()> {

        let path = "/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/equity_cache_rust.sqlite";

        let cache = Cache::new(path)?;

        let player_cards1 = [
            Card {
                rank: Rank::Ace,
                suit: Suit::Heart,
            },
            Card {
                rank: Rank::King,
                suit: Suit::Diamond,
            },
        ];

        let player_cards2 = [player_cards1[1],player_cards1[0]];

        let hand1 = cache.get_equity(&player_cards1, &[])?;

        let hand2 = cache.get_equity(&player_cards2, &[])?;
        
        assert!(hand1.is_some(), "Equity entry not found");
        assert_eq!(hand1,hand2);

        Ok(())


    }

    #[test]
    fn test_absent_key() -> Result<()> {

        let conn = Connection::open_in_memory()?;
        conn.execute_batch(include_str!("/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/schema.sql"))?;

        let path = PathBuf::from("/test");

        let test_cache = Cache {
            conn: conn,
            file_path: path,
        };

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

        let equity_result = EquityResult {
            wins: 21,
            losses: 24,
            splits: 33,
            total: 78,
        };

        let private_mask = cards_to_mask(&player_cards);
        let board_mask: u32 = 0;

        insert_equity(
            &test_cache.conn,
            private_mask,
            board_mask,
            &equity_result,
        )?;

        let stored = test_cache.get_equity(&player_cards, &[])?;

        assert_eq!(stored, Some(equity_result));

        let new_cards = [
            Card {
                rank: Rank::Ten,
                suit: Suit::Club,
            },
            Card {
                rank: Rank::King,
                suit: Suit::Diamond,
            },
        ];

        let stored = test_cache.get_equity(&player_cards, &[])?;
        assert_eq!(stored, Some(equity_result));

        let missing = test_cache.get_equity(&new_cards, &[])?;
        assert_eq!(missing, None);

        Ok(())
    }

    


}


