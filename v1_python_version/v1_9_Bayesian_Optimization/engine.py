# engine.py
# LipisEngine 1.7 with StatsCollector
# Improved file structure

import chess
from stats import StatsCollector
from constants import *
from search_context import SearchContext
from search import *
import math
import time


def find_best_move(board, max_depth=DEFAULT_DEPTH, max_time=DEFAULT_TIME, max_nodes=DEFAULT_MAX_NODES):  
    maximizing = board.turn == chess.WHITE
    score = 0  # ⬅️ alustetaan varmuuden vuoksi
    pv_final = []

    context = SearchContext(
        max_nodes=max_nodes,
        initial_depth=max_depth,
        principal_variations={},
        max_time=max_time,
        start_time = time.time()  # ⏱️ 1. Aloita ajastin
    )
    context.killer_moves = {depth: [None, None] for depth in range(max_depth)}

    for current_depth in range(1, max_depth + 1):
        iteration_start = time.time()
        context.node_count = 0

        if context.time_exceeded():
            break

        score, pv = alphabeta(board, current_depth, -math.inf, math.inf, maximizing, context)
        pv_final = pv

        elapsed_time = time.time() - iteration_start
        nps = int(context.node_count / elapsed_time) if elapsed_time > 0 else 0

        tmp_board = board.copy()
        pv_san = []
        for move in pv:
            if move in tmp_board.legal_moves:
                pv_san.append(tmp_board.san(move))
                tmp_board.push(move)
            else:
                break

        pv_part = f"pv {' '.join(pv_san)}" if pv_san else ""
        print(f"info depth {current_depth} score cp {int(score * 100)} nodes {context.node_count} nps {nps} {pv_part}".strip())

        if context.time_exceeded():
            break
        if context.node_count >= max_nodes:
            break

    return score, pv_final
