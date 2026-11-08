use crate::equity_cache_access::MemoryCache;
use crate::cfr::infoset::InfoSet;
use crate::cfr::node::{CFRNode,action_index};
use crate::actions::Action;
use crate::state::GameState;
use crate::errors::TrainerError;
use crate::cfr::checkpoint::MCCFRCheckpoint;

use std::collections::HashMap;
use rand::rngs::StdRng;
use rand::{RngExt, SeedableRng};
use std::path::Path;

pub struct MCCFRTrainer {
    pub nodes: HashMap<InfoSet, CFRNode>,
    pub memory_cache: MemoryCache,
    pub iterations_trained: usize,
    rng: StdRng,

}

impl MCCFRTrainer {

    pub fn new(memory_cache:MemoryCache,seed: u64) -> Self {

        MCCFRTrainer { 
            nodes: HashMap::new(), 
            memory_cache: memory_cache, 
            iterations_trained: 0,
            rng: StdRng::seed_from_u64(seed) }
    }

    pub fn get_node(&mut self, infoset_key: InfoSet) -> &mut CFRNode {
        self.nodes
            .entry(infoset_key)
            .or_insert_with(CFRNode::new)
    }

    pub fn sample_action(
        &mut self,
        legal_actions: &[Option<Action>; 3],
        strategy: &[f64; 5],
    ) -> Action {
        let roll: f64 = self.rng.random();
        let mut cumulative = 0.0;

        let mut last_action = None;

        for action in legal_actions.iter().flatten() {
            let idx = action_index(action);
            cumulative += strategy[idx];

            last_action = Some(*action);

            if roll < cumulative {
                return *action;
            }
        }

        last_action.expect("No legal actions available")
    }

    pub fn external_sampling_cfr(
        &mut self,
        state: &GameState,
        traverser: usize,
        reach_traverser: f64,
        reach_opponent: f64,
        average_weight: f64,
    ) -> Result<f64, TrainerError> {

        if state.terminal {
            return Ok(state.payoffs[traverser]);
        }

        let player = state.current_player;
        let legal_actions: [Option<Action>; 3] = state.legal_actions();

        if legal_actions == [None, None, None] {
            return Err(TrainerError::NoLegalActions);
        }

        let observation = state.get_observation(&player).ok_or(TrainerError::ObservationError)?;
        let infoset = InfoSet::from_observation(&observation, &self.memory_cache).ok_or(TrainerError::InfosetError)?;

        let reach_probability = if player == traverser {
            reach_traverser
        } else {
            reach_opponent
        };

        let strategy = {
            let node = self.get_node(infoset);

            let strategy = node.get_strategy(
                &legal_actions,
                reach_probability,
                false,
            );

            Self::accumulate_average_strategy(
                node,
                &legal_actions,
                &strategy,
                reach_probability,
                average_weight,
            );

            strategy
        };

        if player == traverser {
            self.traverser_node(
                state,
                traverser,
                reach_traverser,
                reach_opponent,
                &legal_actions,
                &strategy,
                average_weight,
                infoset,
            )
        } else {
            self.opponent_node(
                state,
                traverser,
                reach_traverser,
                reach_opponent,
                &legal_actions,
                &strategy,
                average_weight,
            )
        }
        
        
    }

    fn accumulate_average_strategy(
        node: &mut CFRNode,
        legal_actions: &[Option<Action>; 3],
        strategy: &[f64; 5],
        reach_probability: f64,
        average_weight: f64,
    ) {

        if average_weight > 0.0 {
            for action in legal_actions.iter().flatten() {
                let idx = action_index(action);

                node.strategy_sum[idx] += average_weight*reach_probability*strategy[idx];
            }
        }

    }

    fn opponent_node(
        &mut self,
        state: &GameState,
        traverser: usize,
        reach_traverser: f64,
        reach_opponent: f64,
        legal_actions: &[Option<Action>; 3],
        strategy: &[f64; 5],
        average_weight: f64,
    ) -> Result<f64, TrainerError>{

        let sampled_action = self.sample_action(legal_actions, strategy);
        let sampled_idx = action_index(&sampled_action);

        let mut next_state = state.clone();
        next_state.apply_action(sampled_action)?;

        self.external_sampling_cfr(
            &next_state, 
            traverser, 
            reach_traverser, 
            reach_opponent*strategy[sampled_idx], 
            average_weight
        )
        

    }

    fn traverser_node (
        &mut self,
        state: &GameState,
        traverser: usize,
        reach_traverser: f64,
        reach_opponent: f64,
        legal_actions: &[Option<Action>; 3],
        strategy: &[f64; 5],
        average_weight: f64,
        infoset: InfoSet,
    ) -> Result<f64, TrainerError>{

        let mut node_value = 0.0;
        let mut action_values: [f64;5] = [0.0;5];

        for action in legal_actions.iter().flatten() {
            let idx = action_index(&action);

            let mut next_state = state.clone();
            next_state.apply_action(*action)?;

            let action_value = self.external_sampling_cfr(
                &next_state, 
                traverser, 
                reach_traverser*strategy[idx], 
                reach_opponent, 
                average_weight
            )?;

            action_values[idx] = action_value;
            node_value += strategy[idx] * action_value;

        }

        let node = self.get_node(infoset);

        for action in legal_actions.iter().flatten() {
            let idx = action_index(&action);
            let regret = action_values[idx] - node_value;
            node.regret_sum[idx] += reach_opponent * regret;

        }

        return Ok(node_value)

    }

    pub fn train(
        &mut self,
        iterations: usize,
        print_every: Option<usize>,
        update_both_players: bool,
        checkpoint_path: Option<&Path>,
        save_every: Option<usize>,
    ) -> Result<(), TrainerError> {

        let mut utility_sum = 0.0;
        let mut utility_window = 0.0;
        let mut traversals = 0;

        let mut state = GameState::new();


        for iteration in 1..=iterations {
            

            state.start_hand(&mut self.rng)?;


            let traversers: &[usize] = if update_both_players {
                &[0, 1]
            } else {
                &[iteration % 2]
            };

            for &traverser in traversers {
                let initial_state = state.clone();

                let utility = self.external_sampling_cfr(
                    &initial_state,
                    traverser,
                    1.0,
                    1.0,
                    1.0,
                )?;

                utility_sum += utility;
                utility_window += utility;
                traversals += 1;
            }

            self.iterations_trained += 1;

            if let (Some(path), Some(interval)) = (checkpoint_path, save_every) {
                if interval > 0 && self.iterations_trained % interval == 0 {
                    self.save_checkpoint(path)?;
                }
            }

            if let Some(interval) = print_every {
                if interval > 0 && iteration % interval == 0 {
                    let avg_total = utility_sum / traversals.max(1) as f64;

                    let avg_window = utility_window
                        / (interval * traversers.len()).max(1) as f64;

                    println!(
                        "Iteration {} | infosets: {} | avg utility total: {:.4} | avg utility window: {:.4}",
                        self.iterations_trained,
                        self.nodes.len(),
                        avg_total,
                        avg_window,
                    );

                    utility_window = 0.0;
                }
            }

        }

        Ok(())

    }


    pub fn save_checkpoint(
        &self,
        path: &Path,
    ) -> Result<(), TrainerError> {
        let checkpoint = MCCFRCheckpoint {
            version: 1,
            iterations_trained: self.iterations_trained,
            nodes: self.nodes.clone(),
        };

        let encoded = bincode::encode_to_vec(
            &checkpoint,
            bincode::config::standard(),
        )
        .map_err(TrainerError::CheckpointEncode)?;

        if let Some(parent) = path.parent() {
            if !parent.as_os_str().is_empty() {
                std::fs::create_dir_all(parent)
                    .map_err(TrainerError::CheckpointIo)?;
            }
        }

        let temp_path = path.with_extension("tmp");

        std::fs::write(&temp_path, encoded)
            .map_err(TrainerError::CheckpointIo)?;

        std::fs::rename(&temp_path, path)
            .map_err(TrainerError::CheckpointIo)?;

        Ok(())
    }

    pub fn load_checkpoint(
        path: &Path,
        memory_cache: MemoryCache,
        seed: u64,
    ) -> Result<Self, TrainerError> {
        let bytes = std::fs::read(path)
            .map_err(TrainerError::CheckpointIo)?;

        let (checkpoint, _bytes_read): (MCCFRCheckpoint, usize) =
            bincode::decode_from_slice(
                &bytes,
                bincode::config::standard(),
            )
            .map_err(TrainerError::CheckpointDecode)?;

        if checkpoint.version != 1 {
            return Err(TrainerError::CheckpointVersion(checkpoint.version));
        }

        Ok(Self {
            nodes: checkpoint.nodes,
            memory_cache,
            iterations_trained: checkpoint.iterations_trained,
            rng: StdRng::seed_from_u64(seed),
        })
    }

    
}


#[cfg(test)]
mod tests {
    use super::*;
    use crate::equity_cache_access::{Cache,MemoryCache};
    use crate::observed_state::ObservedState;

    pub fn create_memory_cache() -> MemoryCache{
        let cache = Cache::new("/home/richard.dunbar101/Projects/LiteHoldemPoker/cache/equity_cache_rust.sqlite").unwrap();
        
        let memory_cache: MemoryCache = cache.load_into_memory().unwrap();

        assert_eq!(memory_cache.len(), 2_364_550);

        return memory_cache;

    }

    #[test]
    fn test_mccfr_create() {

        
        let memory_cache: MemoryCache = create_memory_cache();

        let trainer = MCCFRTrainer::new(memory_cache,69);

        assert_eq!(trainer.iterations_trained,0);
        assert_eq!(trainer.memory_cache.len(),2_364_550);

    }
    
    #[test]
    fn test_get_node() {

        let memory_cache = create_memory_cache();

        let observation = ObservedState::test_state();

        let mut trainer = MCCFRTrainer::new(memory_cache,69);

        let infoset = InfoSet::from_observation(
            &observation,
            &trainer.memory_cache,
        ).unwrap();

        //check that its empty
        assert_eq!(trainer.nodes.len(),0);

        //add 1 node
        trainer.get_node(infoset);

        assert_eq!(trainer.nodes.len(),1);



    }


#[cfg(test)]
mod checkpoint_tests {
    use super::*;

    use crate::cfr::checkpoint::MCCFRCheckpoint;
    use crate::state::Street;

    use std::collections::HashMap;
    use tempfile::tempdir;

    fn test_infoset(player: u8, pot_bucket: u8) -> InfoSet {
        InfoSet {
            player,
            street: Street::Preflop,
            equity_bucket: 2,
            pot_bucket,
            texture_bucket: 0,
            position: player,
            facing_bet: true,
            raises_this_round: 0,
        }
    }

    #[test]
    fn test_save_and_load_checkpoint() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("mccfr.bin");

        let mut trainer = MCCFRTrainer::new(
            MemoryCache::new(),
            42,
        );

        let key_0 = test_infoset(0, 1);
        let key_1 = test_infoset(1, 2);

        // Populate two nodes with known values.
        let node_0 = trainer.get_node(key_0);
        node_0.regret_sum = [1.0, 2.0, 3.0, 4.0, 5.0];
        node_0.strategy_sum = [10.0, 20.0, 30.0, 40.0, 50.0];

        let node_1 = trainer.get_node(key_1);
        node_1.regret_sum = [-1.0, 0.0, 2.5, 0.0, 1.5];
        node_1.strategy_sum = [5.0, 0.0, 15.0, 0.0, 10.0];

        trainer.iterations_trained = 100_000;

        // Save the checkpoint.
        trainer.save_checkpoint(&path).unwrap();

        assert!(path.exists());

        // Release the original trainer before loading.
        drop(trainer);

        // Load into a new trainer.
        let loaded = MCCFRTrainer::load_checkpoint(
            &path,
            MemoryCache::new(),
            42,
        )
        .unwrap();

        // Check iteration count and number of nodes.
        assert_eq!(loaded.iterations_trained, 100_000);
        assert_eq!(loaded.nodes.len(), 2);

        // Verify first node.
        let loaded_0 = loaded.nodes.get(&key_0).unwrap();

        assert_eq!(
            loaded_0.regret_sum,
            [1.0, 2.0, 3.0, 4.0, 5.0]
        );

        assert_eq!(
            loaded_0.strategy_sum,
            [10.0, 20.0, 30.0, 40.0, 50.0]
        );

        // Verify second node.
        let loaded_1 = loaded.nodes.get(&key_1).unwrap();

        assert_eq!(
            loaded_1.regret_sum,
            [-1.0, 0.0, 2.5, 0.0, 1.5]
        );

        assert_eq!(
            loaded_1.strategy_sum,
            [5.0, 0.0, 15.0, 0.0, 10.0]
        );
    }

    #[test]
    fn test_checkpoint_overwrite() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("mccfr.bin");

        let mut trainer = MCCFRTrainer::new(
            MemoryCache::new(),
            42,
        );

        let key = test_infoset(0, 0);

        // First checkpoint.
        trainer.iterations_trained = 1_000;
        trainer.get_node(key).regret_sum[0] = 5.0;

        trainer.save_checkpoint(&path).unwrap();

        // Continue training (simulated).
        trainer.iterations_trained = 10_000;
        trainer.get_node(key).regret_sum[0] = 25.0;

        // Overwrite the previous checkpoint.
        trainer.save_checkpoint(&path).unwrap();

        drop(trainer);

        let loaded = MCCFRTrainer::load_checkpoint(
            &path,
            MemoryCache::new(),
            42,
        )
        .unwrap();

        assert_eq!(loaded.iterations_trained, 10_000);
        assert_eq!(loaded.nodes.get(&key).unwrap().regret_sum[0], 25.0);
    }

    #[test]
    fn test_missing_checkpoint_returns_error() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("does_not_exist.bin");

        let result = MCCFRTrainer::load_checkpoint(
            &path,
            MemoryCache::new(),
            42,
        );

        assert!(matches!(
            result,
            Err(TrainerError::CheckpointIo(_))
        ));
    }

    #[test]
    fn test_invalid_checkpoint_version() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("invalid_version.bin");

        // Create a checkpoint with an unsupported version.
        let checkpoint = MCCFRCheckpoint {
            version: 999,
            iterations_trained: 100,
            nodes: HashMap::new(),
        };

        let encoded = bincode::encode_to_vec(
            &checkpoint,
            bincode::config::standard(),
        )
        .unwrap();

        std::fs::write(&path, encoded).unwrap();

        let result = MCCFRTrainer::load_checkpoint(
            &path,
            MemoryCache::new(),
            42,
        );

        assert!(matches!(
            result,
            Err(TrainerError::CheckpointVersion(999))
        ));
    }

    #[test]
    fn test_corrupted_checkpoint_returns_error() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("corrupted.bin");

        // An empty file cannot contain a valid checkpoint.
        std::fs::write(&path, b"").unwrap();

        let result = MCCFRTrainer::load_checkpoint(
            &path,
            MemoryCache::new(),
            42,
        );

        assert!(matches!(
            result,
            Err(TrainerError::CheckpointDecode(_))
        ));
    }
}

}