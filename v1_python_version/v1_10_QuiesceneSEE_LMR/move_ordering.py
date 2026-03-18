# move_ordering.py
# LipisEngine 1.10 - Siirtojärjestyslogiikka ja heuristiikat

import chess
from chess.polyglot import zobrist_hash
from stats import StatsCollector
from constants import *
from weights import MOVE_SCORE_WEIGHTS as weights
from ttable import ttable


def static_exchange_eval(board, move):
    """
    Iteratiivinen SEE pinolla. Palauttaa arvioidun nettotuloksen siirrolle.
    """
    from_square = move.from_square
    to_square = move.to_square
    us = board.piece_at(from_square).color
    them = not us

    # Alustavat tiedot
    piece_map = board.piece_map().copy()
    gain = []
    occupied = set(piece_map.keys())

    # Hyökkääjien lista
    def attackers(square, color):
        return {sq for sq in board.attackers(color, square) if sq in occupied}

    # Alustetaan vaihtosimulaatio
    side = us
    gain.append(PIECE_VALUES[piece_map[to_square].piece_type] if to_square in piece_map else 0)

    occupied.remove(from_square)
    piece_map[to_square] = piece_map[from_square]
    del piece_map[from_square]

    attackers_us = attackers(to_square, us)
    attackers_them = attackers(to_square, them)
    all_attackers = list(attackers_us | attackers_them)

    def least_valuable_attacker(squares):
        return min(squares, key=lambda sq: PIECE_VALUES[piece_map[sq].piece_type])

    # Simuloi vaihtoketju
    while True:
        current_attackers = attackers(to_square, side)
        current_attackers = current_attackers & occupied
        if not current_attackers:
            break
        sq = least_valuable_attacker(current_attackers)
        gain.append(PIECE_VALUES[piece_map[sq].piece_type] - gain[-1])
        occupied.remove(sq)
        piece_map[to_square] = piece_map[sq]
        del piece_map[sq]
        side = not side  # vuoro vaihtuu

    # Backpropagation: min-max logiikka
    for i in reversed(range(1, len(gain))):
        gain[i - 1] = max(-gain[i], gain[i - 1])

    return gain[0]


...

def order_moves(board, context, current_depth, last_move=None): 
    moves = list(board.legal_moves)

    counter_move = context.counter_moves.get(last_move) if last_move else None
    key = zobrist_hash(board)
    tt_entry = ttable.get(key)
    tt_move = tt_entry.get("best_move") if tt_entry else None

    pv_list = context.principal_variations.get(current_depth)
    pv_move = pv_list[0] if pv_list else None
    # Erottele TT-siirto ja muut
    if tt_move is not None and tt_move in moves:
        moves.remove(tt_move)
    else:
        tt_move = None  # Ei ole käytössä

    def move_score(move):
        score = 0
        if move == pv_move:
            score += weights["pv_bonus"]

        # Killer-move etusijalle, jos quiet ja killer
        is_quiet = not board.is_capture(move) and not board.gives_check(move)
        if is_quiet:
            killers = context.killer_moves.get(current_depth, [])
            if len(killers) >= 2:
                if move == killers[0]:
                    score += weights["killer_0_bonus"]
                elif move == killers[1]:
                    score += weights["killer_1_bonus"]

            # ⬇️ Historiaheuristiikka-bonus skaalattuna maksimiarvoon
            key = (move.from_square, move.to_square)
            hist_score = context.history_heuristic.get(key, 0)
            max_hist_score = context.max_history_score.get(key, 1)
            score += weights["quiet_history_scale"] * hist_score / (max_hist_score + 1e-5)

            # Counter-move-heuristiikka
            if move == counter_move:
                score += weights["counter_move_scale"]

        # SEE + capture history, skaalaus kertoimilla
        if board.is_capture(move):
            score += weights["see_scale"] * static_exchange_eval(board, move)

            attacker = board.piece_at(move.from_square)
            victim = board.piece_at(move.to_square)
            if attacker and victim:
                key = (attacker.piece_type, victim.piece_type)
                capture_hist_score = context.capture_history.get(key, 0)
                max_capture_hist_score = context.max_capture_history_score.get(key, 1)
                score += weights["capture_history_scale"] * capture_hist_score / (max_capture_hist_score + 1e-5)
        
        # Shakki, korotus ja tornitus
        if board.gives_check(move):
            score += CHECK_BONUS
        if move.promotion:
            score += PROMOTION_BONUS
            # Hae promootion arvo PROMOTION_VALUES-sanakirjasta, oletusarvona 0 jos ei löydy
            score += PROMOTION_VALUES.get(move.promotion, 0)
        if board.is_castling(move):
            score += CASTLING_BONUS

        # Keskustan hallinta
        if move.to_square in CENTER_SQUARES:
            score += CENTER_SQUARE_BONUS
            score += CENTER_SQUARE_ATTACK_BONUS
        elif move.to_square in EXTENDED_CENTER_SQUARES:
            score += EXTENDED_CENTER_SQUARE_BONUS
            score += EXTENDED_CENTER_SQUARE_ATTACK_BONUS
        elif move.to_square in C_FILE_CENTER_SQUARES:
            score += C_FILE_CENTER_SQUARE_BONUS
            score += C_FILE_CENTER_SQUARE_ATTACK_BONUS
        elif move.to_square in F_FILE_CENTER_SQUARES:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.PAWN:
                score -= F_FILE_CENTER_SQUARE_BONUS
            else:
                score += F_FILE_CENTER_SQUARE_BONUS
                score += F_FILE_CENTER_SQUARE_ATTACK_BONUS

        # Kehitys
        piece = board.piece_at(move.from_square)
        if piece and move.from_square in MINOR_PIECE_STARTING_SQUARES[board.turn]:
            if piece.piece_type == chess.KNIGHT:
                score += KNIGHT_DEV_BONUS
            elif piece.piece_type == chess.BISHOP:
                score += BISHOP_DEV_BONUS

        return score

    sorted_moves = sorted(moves, key=move_score, reverse=True)

    if tt_move is not None:
        return [tt_move] + sorted_moves
    else:
        return sorted_moves
