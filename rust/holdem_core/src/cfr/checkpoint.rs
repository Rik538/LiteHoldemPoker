use crate::cfr::infoset::InfoSet;
use crate::cfr::node::CFRNode;


use std::collections::HashMap;
use bincode::{Encode, Decode};



#[derive(Encode, Decode)]
pub struct MCCFRCheckpoint {
    pub version: u32,
    pub iterations_trained: usize,
    pub nodes: HashMap<InfoSet, CFRNode>,
}