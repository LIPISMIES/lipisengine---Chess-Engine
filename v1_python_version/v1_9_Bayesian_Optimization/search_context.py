# search_context.py
# LipisEngine 1.7 – SearchContext-luokka ja hakuajan hallinta

import time
from typing import Optional
from dataclasses import dataclass, field
from stats import StatsCollector
from constants import MAX_DEPTH, DEFAULT_TIME
from constants import *

@dataclass
class SearchContext:
    node_count: int = 0
    max_nodes: int = DEFAULT_MAX_NODES
    initial_depth: int = 0
    max_time: float = DEFAULT_TIME     # sekunteina
    start_time: Optional[float] = None

    principal_variations: dict = field(default_factory=dict)
    killer_moves: dict = field(default_factory=lambda: {d: [None, None] for d in range(MAX_DEPTH + 1)})
    counter_moves: dict = field(default_factory=dict)
    
    history_heuristic: dict = field(default_factory=dict)
    max_history_score: dict = field(default_factory=dict)
    
    capture_history: dict = field(default_factory=dict)
    max_capture_history_score: dict = field(default_factory=dict)

    stats: StatsCollector = field(default_factory=StatsCollector)

    def time_exceeded(self) -> bool:
        """Tarkistaa, onko hakuaika ylitetty."""
        if self.start_time is None:
            return False
        return (time.time() - self.start_time) >= self.max_time