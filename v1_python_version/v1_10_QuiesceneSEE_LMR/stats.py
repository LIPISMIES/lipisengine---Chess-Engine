from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import collections

@dataclass
class StatsCollector:
    node_count: int = 0
    cutoff_count: int = 0
    quiescence_node_count: int = 0
    move_order_ranks: List[int] = field(default_factory=list)
    max_history_score: float = 0.0

    # ⬇️ Päällekkäisyyksien mittaamiseen:
    zobrist_hits: Dict[int, int] = field(default_factory=lambda: collections.defaultdict(int))
    move_eval_hits: Dict[Tuple[int, int], int] = field(default_factory=lambda: collections.defaultdict(int))
    
    def record_node(self, zobrist_hash: Optional[int] = None):
        self.node_count += 1
        if zobrist_hash is not None:
            self.zobrist_hits[zobrist_hash] += 1

    def record_cutoff(self):
        self.cutoff_count += 1

    def record_quiescence_node(self):
        self.quiescence_node_count += 1

    def record_move_order_rank(self, index: int):
        self.move_order_ranks.append(index)

    def record_move_eval(self, move):
        key = (move.from_square, move.to_square)
        self.move_eval_hits[key] += 1

    def update_max_history(self, val: float):
        self.max_history_score = max(self.max_history_score, val)

    def summary(self) -> dict:
        avg_rank = (sum(self.move_order_ranks) / len(self.move_order_ranks)) if self.move_order_ranks else None
        total_duplicate_zobrist = sum(v for v in self.zobrist_hits.values() if v > 1)
        total_duplicate_moves = sum(v for v in self.move_eval_hits.values() if v > 1)

        return {
            "nodes": self.node_count,
            "cutoffs": self.cutoff_count,
            "cutoff_ratio": self.cutoff_count / self.node_count if self.node_count else 0,
            "q_nodes": self.quiescence_node_count,
            "avg_move_order_rank": avg_rank,
            "max_history_score": self.max_history_score,
            "duplicate_positions": total_duplicate_zobrist,
            "duplicate_move_evals": total_duplicate_moves,
        }

    def print_summary(self):
        print("\n==== STATS SUMMARY ====")
        for key, val in self.summary().items():
            print(f"{key}: {val}")
