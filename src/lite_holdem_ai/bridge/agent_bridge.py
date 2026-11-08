# lite_holdem_ai/bridge/agent_bridge.py

import sys
import json

import sys
from contextlib import redirect_stdout

from lite_holdem_ai import (
    LiteHoldemEnv,
)

from lite_holdem_ai.cfr.infoset import (
    CachedEquityBucketProvider,
    MemoizedBucketProvider,
)

from lite_holdem_ai.cfr.agent import CFRAgent

from lite_holdem_ai.cfr.infoset import (
    StreetAwarePotBucketTextureNoHistoryInfosetKeyBuilder,
    StreetAwarePotBucketNoHistoryInfosetKeyBuilder,
)
from lite_holdem_ai.cfr.mccfr_trainer import MCCFRTrainer
from lite_holdem_ai.equity.cache import EquityCache

from lite_holdem_ai.game.actions import Action


def make_infoset_builder(cache_path, infoset_builder_cls):
    """Create an infoset builder and keep its equity cache available for closing."""
    equity_cache = EquityCache(cache_path)
    raw_bucket_provider = CachedEquityBucketProvider(equity_cache)
    bucket_provider = MemoizedBucketProvider(raw_bucket_provider)

    infoset_builder = infoset_builder_cls(bucket_provider)

    return infoset_builder, equity_cache


def load_mccfr_agent(
    *,
    checkpoint_path,
    cache_path,
    name,
    seed,
    infoset_builder_cls,
):
    """Load a CFR-style agent from a checkpoint using the correct infoset abstraction."""
    infoset_builder, equity_cache = make_infoset_builder(
        cache_path=cache_path,
        infoset_builder_cls=infoset_builder_cls,
    )

    trainer = MCCFRTrainer(
        infoset_builder=infoset_builder,
        env_factory=lambda: LiteHoldemEnv(),
    )
    trainer.load_checkpoint(checkpoint_path)

    agent = CFRAgent(
        nodes=trainer.nodes,
        infoset_builder=infoset_builder,
        name=name,
        seed=seed,
    )

    # Allows RepeatedTournamentRunner to close the database connection
    # if CFRAgent.close() checks for self.equity_cache.
    agent.equity_cache = equity_cache

    return agent


def select_action(observation: dict) -> str:
    """
    Temporary agent policy.

    Receives an observation from Rust and returns
    one of the legal action names.
    """

    legal_actions = observation.get("legal_actions", [])

    if not legal_actions:
        raise ValueError("No legal actions available")

    # Prefer checking when possible.
    if "CHECK" in legal_actions:
        return "CHECK"

    # Otherwise prefer calling.
    if "CALL" in legal_actions:
        return "CALL"

    # Fallback to the first legal action.
    return legal_actions[0]


def process_observation(message: dict, agent) -> dict:
    observation = convert_observation(message)

    legal_actions = convert_legal_actions(message["legal_actions"])

    action = agent.select_action(
        observation,
        legal_actions,
    )

    rust_action = action_to_rust(
        action,
        observation["amount_to_call"],
    )

    if rust_action not in message["legal_actions"]:
        raise ValueError(f"Agent returned illegal action: {rust_action}")

    return {"action": rust_action}


def initialise_agent(checkpoint_path, cache_path):
    with redirect_stdout(sys.stderr):
        agent = load_mccfr_agent(
            checkpoint_path=checkpoint_path,
            cache_path=cache_path,
            name="Python CFR",
            seed=42,
            infoset_builder_cls=StreetAwarePotBucketNoHistoryInfosetKeyBuilder,
        )

    return agent


RANK_IDS = {"T": 0, "J": 1, "Q": 2, "K": 3, "A": 4}
SUIT_IDS = {
    "C": 0,
    "D": 1,
    "H": 2,
    "S": 3,
}

STREET_IDS = {
    "PREFLOP": 0,
    "FLOP": 1,
    "TURN": 2,
    "RIVER": 3,
}


def card_code_to_int(code: str) -> int:
    """Convert e.g. AH into a Python card ID."""
    if len(code) != 2:
        raise ValueError(f"Invalid card: {code}")

    return RANK_IDS[code[0]] * 4 + SUIT_IDS[code[1]]


def convert_observation(message: dict) -> dict:
    """Convert a Rust JSON observation into Python format."""
    return {
        "player": message["player"],
        "current_player": message["current_player"],
        "button_player": message["button_player"],
        "private_cards": [card_code_to_int(card) for card in message["private_cards"]],
        "public_cards": [card_code_to_int(card) for card in message["public_cards"]],
        "street": STREET_IDS[message["street"]],
        "pot": message["pot"],
        "amount_to_call": message["amount_to_call"],
        "raises_this_round": message["raises_this_round"],
        # Required by build_infoset_context().
        # Your current eight-field builder doesn't use either.
        "actions_this_round": [],
        "action_history": [],
    }


def convert_legal_actions(names: list[str]) -> list[Action]:
    """Map Rust's five actions onto Python's three actions."""
    mapping = {
        "FOLD": Action.FOLD,
        "CHECK": Action.CHECK_CALL,
        "CALL": Action.CHECK_CALL,
        "BET": Action.BET_RAISE,
        "RAISE": Action.BET_RAISE,
    }

    return [mapping[name] for name in names]


def action_to_rust(action: Action, amount_to_call: int) -> str:
    """Translate the Python-selected action back into Rust."""
    if action == Action.FOLD:
        return "FOLD"

    if action == Action.CHECK_CALL:
        return "CALL" if amount_to_call > 0 else "CHECK"

    if action == Action.BET_RAISE:
        return "RAISE" if amount_to_call > 0 else "BET"

    raise ValueError(f"Unknown Python action: {action}")


def main():
    agent = initialise_agent(
        checkpoint_path="checkpoints/rfd_lite_holdem_nohist_500k.pkl",
        cache_path="cache/equity_cache.sqlite",
    )

    for line in sys.stdin:
        if not line.strip():
            continue

        try:
            observation = json.loads(line)

            # Next stage: convert observation and call agent
            response = process_observation(observation, agent)

        except (json.JSONDecodeError, ValueError, TypeError) as error:
            response = {"error": str(error)}

        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
