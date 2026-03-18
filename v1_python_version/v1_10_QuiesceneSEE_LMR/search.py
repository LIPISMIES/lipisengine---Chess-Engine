# search.py
# LipisEngine 1.10 – Hakualgoritmit: alphabeta, quiescence, generate_quiescence_moves

import chess
from chess.polyglot import zobrist_hash
from stats import StatsCollector
from evaluate import evaluate
from constants import *
from move_ordering import order_moves, static_exchange_eval
from ttable import ttable
from math import inf


def quiescence(board, alpha, beta, maximizing, context, depth=0):
    if context.node_count >= context.max_nodes:
        return evaluate(board), []

    context.node_count += 1
    stand_pat = evaluate(board)

    if maximizing:
        if stand_pat >= beta:
            return beta, []
        alpha = max(alpha, stand_pat)
    else:
        if stand_pat <= alpha:
            return alpha, []
        beta = min(beta, stand_pat)

    if depth >= MAX_QUIESCENCE_DEPTH:
        return stand_pat, []

    best_value = stand_pat
    best_pv = []

    # Generoi lailliset kaappaukset
    captures = list(board.generate_legal_captures())

    # Laske SEE:t ja rakenna pari (move, see_score)
    scored_captures = []
    for move in captures:
        see_score = static_exchange_eval(board, move)
        if see_score < 0:
            continue  # ⛔ huono kaappaus
        scored_captures.append((move, see_score))

    # Lajitellaan pareittain: paras SEE ensin
    scored_captures.sort(key=lambda x: x[1], reverse=True)

    for move, _ in scored_captures:
        board.push(move)
        eval, pv = quiescence(board, alpha, beta, not maximizing, context, depth + 1)
        board.pop()

        if maximizing:
            if eval > best_value:
                best_value = eval
                best_pv = [move] + pv
            alpha = max(alpha, eval)
        else:
            if eval < best_value:
                best_value = eval
                best_pv = [move] + pv
            beta = min(beta, eval)

        if beta <= alpha:
            break

    return best_value, best_pv



def alphabeta(board, remaining_depth, alpha, beta, maximizing, context, last_move=None):
    if context.node_count >= context.max_nodes:
        return evaluate(board), []
    context.node_count += 1

    alpha_orig = alpha
    beta_orig = beta
    key = zobrist_hash(board)
    tt_entry = ttable.get(key)

    if tt_entry:
        if tt_entry["depth"] >= remaining_depth:
            flag = tt_entry.get("flag", "EXACT")
            if flag == "EXACT":
                return tt_entry["value"], tt_entry["pv"]
            elif flag == "LOWERBOUND" and tt_entry["value"] > alpha:
                alpha = tt_entry["value"]
            elif flag == "UPPERBOUND" and tt_entry["value"] < beta:
                beta = tt_entry["value"]
            if alpha >= beta:
                return tt_entry["value"], tt_entry["pv"]

    current_depth = context.initial_depth - remaining_depth

    if remaining_depth == 0 or board.is_game_over(claim_draw=True):
        if board.is_checkmate():
            score = -MATE_SCORE + current_depth if maximizing else MATE_SCORE - current_depth
            return score, []
        elif board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0, []
        else:
            return quiescence(board, alpha, beta, maximizing, context, depth=0)

    best_value = -inf if maximizing else inf
    best_pv = []

    ordered_moves = order_moves(board, context, current_depth, last_move)

    for i, move in enumerate(ordered_moves):
        is_quiet = not board.is_capture(move) and not board.gives_check(move)
        board.push(move)

        do_lmr = (
            remaining_depth >= LMR_DEPTH_THRESHOLD and
            i >= LMR_MOVE_THRESHOLD and
            is_quiet
        )

        if do_lmr:
            reduced_depth = max(1, remaining_depth - LMR_REDUCTION)
            reduced_eval, _ = alphabeta(board, reduced_depth, alpha, beta, not maximizing, context, move)

            # Jos lyhennetty haku parantaa arvioita, tee uusi täyssyvyinen haku
            if maximizing and reduced_eval > alpha or not maximizing and reduced_eval < beta:
                eval, pv = alphabeta(board, remaining_depth - 1, alpha, beta, not maximizing, context, move)
            else:
                eval = reduced_eval
                pv = []
        else:
            eval, pv = alphabeta(board, remaining_depth - 1, alpha, beta, not maximizing, context, move)

        board.pop()

        if maximizing:
            if eval > best_value:
                best_value = eval
                best_pv = [move] + pv
            alpha = max(alpha, eval)
        else:
            if eval < best_value:
                best_value = eval
                best_pv = [move] + pv
            beta = min(beta, eval)

        if beta <= alpha:
            if is_quiet:
                # Killer move -päivitys: vain quiet moves
                killers = context.killer_moves.get(current_depth, [None, None])
                if move != killers[0] and move != killers[1]:
                    context.killer_moves[current_depth] = [move, killers[0]]
                # Historiaheuristiikka
                key = (move.from_square, move.to_square)
                bonus = 1.7 ** remaining_depth
                context.history_heuristic[key] = context.history_heuristic.get(key, 0) + bonus
                context.max_history_score[key] = max(
                    context.max_history_score.get(key, 0),
                    context.history_heuristic[key]
                )
                # Vastasiirto
                context.counter_moves[last_move] = move
            else:
                attacker = board.piece_at(move.from_square)
                victim = board.piece_at(move.to_square)
                if attacker and victim:
                    key = (attacker.piece_type, victim.piece_type)
                    bonus = 1.5 ** remaining_depth
                    context.capture_history[key] = context.capture_history.get(key, 0) + bonus
                    context.max_capture_history_score[key] = max(
                        context.max_capture_history_score.get(key, 0),
                        context.capture_history[key]
                    )
            break

    # Bound-flag
    if best_value <= alpha_orig:
        flag = "UPPERBOUND"
    elif best_value >= beta_orig:
        flag = "LOWERBOUND"
    else:
        flag = "EXACT"

    # TT-tallennus
    if not tt_entry or remaining_depth >= tt_entry["depth"]:
        ttable.store(
            key=key,
            depth=remaining_depth,
            value=best_value,
            pv=best_pv,
            best_move=best_pv[0] if best_pv else None,
            flag=flag
        )

    context.principal_variations[current_depth] = best_pv

    return best_value, best_pv
