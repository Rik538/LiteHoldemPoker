# -*- coding: utf-8 -*-
"""
Created on Sun May 31 13:47:48 2026

@author: Richard
"""

from collections import Counter
from dataclasses import dataclass, field
from lite_holdem_ai.game.actions import Action
from lite_holdem_ai.game.state import GameState
import math
import numpy as np




@dataclass
class MatchResult:
    agent0_name: str
    agent1_name: str
    hands_played: int = 0

    agent0_total_payoff: float = 0.0
    agent1_total_payoff: float = 0.0

    # Per-hand payoff storage
    agent0_hand_payoffs: list[float] = field(default_factory=list)
    agent1_hand_payoffs: list[float] = field(default_factory=list)

    # Net payoff outcomes
    agent0_net_wins: int = 0
    agent1_net_wins: int = 0
    net_draws: int = 0

    # Terminal type
    terminal_by_fold: int = 0
    terminal_by_showdown: int = 0

    # Terminal street distribution
    terminal_street_counts: Counter = field(default_factory=Counter)

    # Fold outcomes
    agent0_fold_wins: int = 0
    agent1_fold_wins: int = 0
    agent0_folds: int = 0
    agent1_folds: int = 0

    # Showdown outcomes
    agent0_showdown_wins: int = 0
    agent1_showdown_wins: int = 0
    showdown_splits: int = 0

    # Pot diagnostics
    final_pots: list[float] = field(default_factory=list)
    fold_pots: list[float] = field(default_factory=list)
    showdown_pots: list[float] = field(default_factory=list)

    # Basic action counts
    action_counts: Counter = field(default_factory=Counter)
    action_counts_by_street: Counter = field(default_factory=Counter)

    # Agent-specific action counts
    action_counts_by_agent: Counter = field(default_factory=Counter)
    action_counts_by_agent_street: Counter = field(default_factory=Counter)

    # Facing-bet response counts
    facing_bet_counts_by_agent: Counter = field(default_factory=Counter)
    facing_bet_action_counts_by_agent: Counter = field(default_factory=Counter)
    facing_bet_action_counts_by_agent_street: Counter = field(default_factory=Counter)

    # VPIP / aggression counts
    vpip_counts_by_agent: Counter = field(default_factory=Counter)
    aggression_counts_by_agent: Counter = field(default_factory=Counter)
    total_actions_by_agent: Counter = field(default_factory=Counter)
    non_fold_actions_by_agent: Counter = field(default_factory=Counter)

    def record_hand(
        self,
        payoff_for_agent0: float,
        payoff_for_agent1: float,
        state: "GameState",
    ):
        assert abs(payoff_for_agent0 + payoff_for_agent1) < 1e-9
        assert state.terminal

        self.hands_played += 1

        self.agent0_total_payoff += payoff_for_agent0
        self.agent1_total_payoff += payoff_for_agent1

        self.agent0_hand_payoffs.append(payoff_for_agent0)
        self.agent1_hand_payoffs.append(payoff_for_agent1)

        self.final_pots.append(state.pot)
        self.terminal_street_counts[state.street] += 1

        # Net payoff outcome
        if payoff_for_agent0 > payoff_for_agent1:
            self.agent0_net_wins += 1
        elif payoff_for_agent1 > payoff_for_agent0:
            self.agent1_net_wins += 1
        else:
            self.net_draws += 1

        # Terminal/outcome type
        if state.folded_player is not None:
            self.terminal_by_fold += 1
            self.fold_pots.append(state.pot)

            loser = state.folded_player
            winner = 1 - loser

            if winner == 0:
                self.agent0_fold_wins += 1
            else:
                self.agent1_fold_wins += 1

            if loser == 0:
                self.agent0_folds += 1
            else:
                self.agent1_folds += 1

        else:
            self.terminal_by_showdown += 1
            self.showdown_pots.append(state.pot)

            if payoff_for_agent0 > payoff_for_agent1:
                self.agent0_showdown_wins += 1
            elif payoff_for_agent1 > payoff_for_agent0:
                self.agent1_showdown_wins += 1
            else:
                self.showdown_splits += 1

        self.record_actions(state)

    def record_actions(self, state: "GameState"):
        for item in state.action_history:

            # Preferred shape:
            # (player, street, action, to_call)
            if isinstance(item, tuple) and len(item) == 4:
                player, street, action, to_call = item

                self.action_counts[action] += 1
                self.action_counts_by_street[(street, action)] += 1

                self.action_counts_by_agent[(player, action)] += 1
                self.action_counts_by_agent_street[(player, street, action)] += 1

                self.total_actions_by_agent[player] += 1

                if action != Action.FOLD:
                    self.non_fold_actions_by_agent[player] += 1

                if action == Action.BET_RAISE:
                    self.aggression_counts_by_agent[player] += 1

                # Facing a bet
                if to_call > 0:
                    self.facing_bet_counts_by_agent[player] += 1
                    self.facing_bet_action_counts_by_agent[(player, action)] += 1
                    self.facing_bet_action_counts_by_agent_street[(player, street, action)] += 1

                # VPIP-style stat:
                # voluntarily putting money in beyond forced blinds
                if action == Action.BET_RAISE:
                    self.vpip_counts_by_agent[player] += 1
                elif to_call > 0 and action == Action.CHECK_CALL:
                    self.vpip_counts_by_agent[player] += 1

            # Older shape:
            # (street, action)
            elif isinstance(item, tuple) and len(item) == 2:
                street, action = item
                self.action_counts[action] += 1
                self.action_counts_by_street[(street, action)] += 1

            # Oldest fallback:
            # action only
            else:
                action = item
                self.action_counts[action] += 1

    # ------------------------------------------------------------------
    # Basic payoff properties
    # ------------------------------------------------------------------

    @property
    def agent0_avg_payoff(self):
        return self.agent0_total_payoff / self.hands_played if self.hands_played else 0.0

    @property
    def agent1_avg_payoff(self):
        return self.agent1_total_payoff / self.hands_played if self.hands_played else 0.0

    @property
    def total_payoff_check(self):
        return self.agent0_total_payoff + self.agent1_total_payoff

    # ------------------------------------------------------------------
    # Variance / standard error / confidence intervals
    # ------------------------------------------------------------------

    @property
    def agent0_std(self):
        if self.hands_played <= 1:
            return 0.0
        return float(np.std(self.agent0_hand_payoffs, ddof=1))

    @property
    def agent1_std(self):
        if self.hands_played <= 1:
            return 0.0
        return float(np.std(self.agent1_hand_payoffs, ddof=1))

    @property
    def agent0_std_err(self):
        if self.hands_played == 0:
            return 0.0
        return self.agent0_std / math.sqrt(self.hands_played)

    @property
    def agent1_std_err(self):
        if self.hands_played == 0:
            return 0.0
        return self.agent1_std / math.sqrt(self.hands_played)

    @property
    def agent0_ci95(self):
        return self.agent0_std_err * 1.96

    @property
    def agent1_ci95(self):
        return self.agent1_std_err * 1.96

    # ------------------------------------------------------------------
    # Terminal rates
    # ------------------------------------------------------------------

    @property
    def fold_terminal_rate(self):
        return self.terminal_by_fold / self.hands_played if self.hands_played else 0.0

    @property
    def showdown_terminal_rate(self):
        return self.terminal_by_showdown / self.hands_played if self.hands_played else 0.0

    # ------------------------------------------------------------------
    # Fold rates
    # ------------------------------------------------------------------

    @property
    def agent0_fold_rate(self):
        return self.agent0_folds / self.hands_played if self.hands_played else 0.0

    @property
    def agent1_fold_rate(self):
        return self.agent1_folds / self.hands_played if self.hands_played else 0.0

    # ------------------------------------------------------------------
    # Showdown rates
    # ------------------------------------------------------------------

    @property
    def agent0_showdown_win_rate(self):
        if self.terminal_by_showdown == 0:
            return 0.0
        return self.agent0_showdown_wins / self.terminal_by_showdown

    @property
    def agent1_showdown_win_rate(self):
        if self.terminal_by_showdown == 0:
            return 0.0
        return self.agent1_showdown_wins / self.terminal_by_showdown

    @property
    def showdown_split_rate(self):
        if self.terminal_by_showdown == 0:
            return 0.0
        return self.showdown_splits / self.terminal_by_showdown

    # ------------------------------------------------------------------
    # Pot diagnostics
    # ------------------------------------------------------------------

    @property
    def avg_final_pot(self):
        return self.mean(self.final_pots)

    @property
    def avg_fold_pot(self):
        return self.mean(self.fold_pots)

    @property
    def avg_showdown_pot(self):
        return self.mean(self.showdown_pots)

    # ------------------------------------------------------------------
    # Agent action-rate diagnostics
    # ------------------------------------------------------------------

    def agent_action_count(self, player, action):
        return self.action_counts_by_agent[(player, action)]

    def agent_action_rate(self, player, action):
        total = self.total_actions_by_agent[player]
        if total == 0:
            return 0.0
        return self.agent_action_count(player, action) / total

    def agent_aggression_rate(self, player):
        total = self.total_actions_by_agent[player]
        if total == 0:
            return 0.0
        return self.aggression_counts_by_agent[player] / total

    def agent_aggression_rate_non_fold(self, player):
        total = self.non_fold_actions_by_agent[player]
        if total == 0:
            return 0.0
        return self.aggression_counts_by_agent[player] / total

    def agent_vpip_rate(self, player):
        total = self.total_actions_by_agent[player]
        if total == 0:
            return 0.0
        return self.vpip_counts_by_agent[player] / total

    # ------------------------------------------------------------------
    # Facing-bet diagnostics
    # ------------------------------------------------------------------

    def agent_facing_bet_count(self, player):
        return self.facing_bet_counts_by_agent[player]

    def agent_facing_bet_action_count(self, player, action):
        return self.facing_bet_action_counts_by_agent[(player, action)]

    def agent_facing_bet_action_rate(self, player, action):
        total = self.facing_bet_counts_by_agent[player]
        if total == 0:
            return 0.0
        return self.facing_bet_action_counts_by_agent[(player, action)] / total

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def mean(self, values):
        if not values:
            return 0.0
        return sum(values) / len(values)

    def pct(self, value):
        return value * 100

    def agent_name(self, player):
        return self.agent0_name if player == 0 else self.agent1_name

    # ------------------------------------------------------------------
    # Summary dictionary
    # ------------------------------------------------------------------

    def summary(self):
        return {
            "agent0": self.agent0_name,
            "agent1": self.agent1_name,
            "hands_played": self.hands_played,

            "agent0_total_payoff": self.agent0_total_payoff,
            "agent1_total_payoff": self.agent1_total_payoff,
            "total_payoff_check": self.total_payoff_check,

            "agent0_avg_payoff": self.agent0_avg_payoff,
            "agent1_avg_payoff": self.agent1_avg_payoff,

            "agent0_std": self.agent0_std,
            "agent1_std": self.agent1_std,
            "agent0_std_err": self.agent0_std_err,
            "agent1_std_err": self.agent1_std_err,
            "agent0_ci95": self.agent0_ci95,
            "agent1_ci95": self.agent1_ci95,

            "agent0_net_wins": self.agent0_net_wins,
            "agent1_net_wins": self.agent1_net_wins,
            "net_draws": self.net_draws,

            "terminal_by_fold": self.terminal_by_fold,
            "terminal_by_showdown": self.terminal_by_showdown,
            "fold_terminal_rate": self.fold_terminal_rate,
            "showdown_terminal_rate": self.showdown_terminal_rate,

            "terminal_street_counts": dict(self.terminal_street_counts),

            "agent0_fold_wins": self.agent0_fold_wins,
            "agent1_fold_wins": self.agent1_fold_wins,
            "agent0_folds": self.agent0_folds,
            "agent1_folds": self.agent1_folds,
            "agent0_fold_rate": self.agent0_fold_rate,
            "agent1_fold_rate": self.agent1_fold_rate,

            "agent0_showdown_wins": self.agent0_showdown_wins,
            "agent1_showdown_wins": self.agent1_showdown_wins,
            "showdown_splits": self.showdown_splits,
            "agent0_showdown_win_rate": self.agent0_showdown_win_rate,
            "agent1_showdown_win_rate": self.agent1_showdown_win_rate,
            "showdown_split_rate": self.showdown_split_rate,

            "avg_final_pot": self.avg_final_pot,
            "avg_fold_pot": self.avg_fold_pot,
            "avg_showdown_pot": self.avg_showdown_pot,

            "agent0_vpip_rate": self.agent_vpip_rate(0),
            "agent1_vpip_rate": self.agent_vpip_rate(1),
            "agent0_aggression_rate": self.agent_aggression_rate(0),
            "agent1_aggression_rate": self.agent_aggression_rate(1),
            "agent0_aggression_rate_non_fold": self.agent_aggression_rate_non_fold(0),
            "agent1_aggression_rate_non_fold": self.agent_aggression_rate_non_fold(1),

            "agent0_facing_bet_count": self.agent_facing_bet_count(0),
            "agent1_facing_bet_count": self.agent_facing_bet_count(1),
            "agent0_fold_facing_bet_rate": self.agent_facing_bet_action_rate(0, Action.FOLD),
            "agent1_fold_facing_bet_rate": self.agent_facing_bet_action_rate(1, Action.FOLD),
            "agent0_call_facing_bet_rate": self.agent_facing_bet_action_rate(0, Action.CHECK_CALL),
            "agent1_call_facing_bet_rate": self.agent_facing_bet_action_rate(1, Action.CHECK_CALL),
            "agent0_raise_facing_bet_rate": self.agent_facing_bet_action_rate(0, Action.BET_RAISE),
            "agent1_raise_facing_bet_rate": self.agent_facing_bet_action_rate(1, Action.BET_RAISE),

            "action_counts": dict(self.action_counts),
            "action_counts_by_street": dict(self.action_counts_by_street),
            "action_counts_by_agent": dict(self.action_counts_by_agent),
            "action_counts_by_agent_street": dict(self.action_counts_by_agent_street),
            "facing_bet_action_counts_by_agent": dict(self.facing_bet_action_counts_by_agent),
            "facing_bet_action_counts_by_agent_street": dict(self.facing_bet_action_counts_by_agent_street),
        }

    # ------------------------------------------------------------------
    # Printing
    # ------------------------------------------------------------------

    def print_summary(self):
        print("=" * 70)
        print(f"Match: {self.agent0_name} vs {self.agent1_name}")
        print(f"Hands played: {self.hands_played}")
        print("-" * 70)

        print("Payoff:")
        print(
            f"{self.agent0_name}: total={self.agent0_total_payoff:.2f}, "
            f"avg={self.agent0_avg_payoff:.6f}, "
            f"std={self.agent0_std:.4f}, "
            f"stderr={self.agent0_std_err:.6f}, "
            f"95% CI=±{self.agent0_ci95:.6f}"
        )
        print(
            f"{self.agent1_name}: total={self.agent1_total_payoff:.2f}, "
            f"avg={self.agent1_avg_payoff:.6f}, "
            f"std={self.agent1_std:.4f}, "
            f"stderr={self.agent1_std_err:.6f}, "
            f"95% CI=±{self.agent1_ci95:.6f}"
        )
        print(f"Total payoff check: {self.total_payoff_check:.6f}")

        print("-" * 70)
        print("Net payoff outcomes:")
        print(f"{self.agent0_name} net wins: {self.agent0_net_wins}")
        print(f"{self.agent1_name} net wins: {self.agent1_net_wins}")
        print(f"Net draws: {self.net_draws}")

        print("-" * 70)
        print("Terminal types:")
        print(
            f"Ended by fold: {self.terminal_by_fold} "
            f"({self.pct(self.fold_terminal_rate):.2f}%)"
        )
        print(
            f"Ended by showdown: {self.terminal_by_showdown} "
            f"({self.pct(self.showdown_terminal_rate):.2f}%)"
        )

        print("-" * 70)
        print("Terminal street counts:")
        for street, count in sorted(self.terminal_street_counts.items()):
            print(f"  Street {street}: {count}")

        print("-" * 70)
        print("Pot sizes:")
        print(f"Average final pot: {self.avg_final_pot:.4f}")
        print(f"Average fold pot: {self.avg_fold_pot:.4f}")
        print(f"Average showdown pot: {self.avg_showdown_pot:.4f}")

        print("-" * 70)
        print("Fold outcomes:")
        print(
            f"{self.agent0_name}: fold wins={self.agent0_fold_wins}, "
            f"folds={self.agent0_folds}, "
            f"fold rate={self.pct(self.agent0_fold_rate):.2f}%"
        )
        print(
            f"{self.agent1_name}: fold wins={self.agent1_fold_wins}, "
            f"folds={self.agent1_folds}, "
            f"fold rate={self.pct(self.agent1_fold_rate):.2f}%"
        )

        print("-" * 70)
        print("Showdown outcomes:")
        print(
            f"{self.agent0_name}: wins={self.agent0_showdown_wins}, "
            f"win rate={self.pct(self.agent0_showdown_win_rate):.2f}%"
        )
        print(
            f"{self.agent1_name}: wins={self.agent1_showdown_wins}, "
            f"win rate={self.pct(self.agent1_showdown_win_rate):.2f}%"
        )
        print(
            f"Showdown splits: {self.showdown_splits} "
            f"({self.pct(self.showdown_split_rate):.2f}%)"
        )

        print("-" * 70)
        print("Agent style stats:")
        for player in [0, 1]:
            print(f"{self.agent_name(player)}:")
            print(f"  VPIP rate: {self.pct(self.agent_vpip_rate(player)):.2f}%")
            print(f"  Aggression rate: {self.pct(self.agent_aggression_rate(player)):.2f}%")
            print(
                f"  Aggression rate non-fold: "
                f"{self.pct(self.agent_aggression_rate_non_fold(player)):.2f}%"
            )
            print(f"  Facing bet count: {self.agent_facing_bet_count(player)}")
            print(
                f"  Fold vs bet: "
                f"{self.pct(self.agent_facing_bet_action_rate(player, Action.FOLD)):.2f}%"
            )
            print(
                f"  Call vs bet: "
                f"{self.pct(self.agent_facing_bet_action_rate(player, Action.CHECK_CALL)):.2f}%"
            )
            print(
                f"  Raise vs bet: "
                f"{self.pct(self.agent_facing_bet_action_rate(player, Action.BET_RAISE)):.2f}%"
            )

        print("-" * 70)
        print("Action counts:")
        for action, count in self.action_counts.items():
            print(f"  {action}: {count}")

        print("-" * 70)
        print("Action counts by street:")
        for key, count in sorted(self.action_counts_by_street.items(), key=lambda x: str(x[0])):
            street, action = key
            print(f"  Street {street}, {action}: {count}")

        print("-" * 70)
        print("Action counts by agent:")
        for key, count in sorted(self.action_counts_by_agent.items(), key=lambda x: str(x[0])):
            player, action = key
            print(f"  {self.agent_name(player)}, {action}: {count}")

        print("-" * 70)
        print("Action counts by agent and street:")
        for key, count in sorted(self.action_counts_by_agent_street.items(), key=lambda x: str(x[0])):
            player, street, action = key
            print(f"  {self.agent_name(player)}, Street {street}, {action}: {count}")

        print("=" * 70)
        
              