# engine.py
# LipisEngine 1.2 with alpha-beta pruning
import chess
from math import inf
from functools import lru_cache

DEFAULT_DEPTH = 4
MAX_DEPTH = 8
MATE_SCORE = 10_000 # Matin arvio, jotta mate N toimii järkevästi

# Painotukset
ISOLATED_PAWN_PENALTY = 0.25
DOUBLED_PAWN_PENALTY = 0.2
CONNECTED_PAWN_BONUS = 0.15
PASSED_PAWN_BONUS = 0.3

# Keskusruudut globaalina vakiomuuttujana
CENTER_SQUARES = [chess.D4, chess.D5, chess.E4, chess.E5]

# Pawn-hashin muodostus
def pawn_hash(board):
    return hash((board.pieces(chess.PAWN, chess.WHITE), board.pieces(chess.PAWN, chess.BLACK)))

@lru_cache(maxsize=4096)
def pawn_structure_score_cached(pawn_hash_value):
    return pawn_structure_score_unhashed(pawn_hash_value)

def pawn_structure_score_unhashed(pawn_hash_value):
    # Tämä versio ei käytä boardia suoraan, mutta placeholder-toiminnallisuudessa tarvitaan board
    # Tämä voidaan refaktoroida tarkemmin myöhemmin
    return 0  # Käytetään alempaa funktiota suoraan evaluate-funktiossa toistaiseksi

def material_score(board):
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3.05,
        chess.BISHOP: 3.1,
        chess.ROOK: 5,
        chess.QUEEN: 9
    }
    score = 0
    for piece_type, value in piece_values.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value
    return score

def center_control_bonus(board):
    bonus = 0
    for square in CENTER_SQUARES:
        piece = board.piece_at(square)
        if piece:
            if piece.color == chess.WHITE:
                bonus += 0.1
            else:
                bonus -= 0.1
    return bonus

def pawn_structure_score(board):
    score = 0
    for color in [chess.WHITE, chess.BLACK]:
        pawns = board.pieces(chess.PAWN, color)
        files = [0] * 8
        connected = 0

        for square in pawns:
            file = chess.square_file(square)
            files[file] += 1

        for file in range(8):
            count = files[file]
            if count > 1:
                score += -DOUBLED_PAWN_PENALTY * (count - 1) if color == chess.WHITE else DOUBLED_PAWN_PENALTY * (count - 1)
            if count > 0:
                has_left = file > 0 and files[file - 1] > 0
                has_right = file < 7 and files[file + 1] > 0
                if has_left or has_right:
                    score += CONNECTED_PAWN_BONUS if color == chess.WHITE else -CONNECTED_PAWN_BONUS
                else:
                    score += -ISOLATED_PAWN_PENALTY if color == chess.WHITE else ISOLATED_PAWN_PENALTY

        for square in pawns:
            rank = chess.square_rank(square)
            file = chess.square_file(square)
            passed = True
            for f in [file - 1, file, file + 1]:
                if not (0 <= f < 8):
                    continue
                for r in range(rank + 1, 8) if color == chess.WHITE else range(rank - 1, -1, -1):
                    target = chess.square(f, r)
                    if target in board.pieces(chess.PAWN, not color):
                        passed = False
                        break
                if not passed:
                    break
            if passed:
                score += PASSED_PAWN_BONUS if color == chess.WHITE else -PASSED_PAWN_BONUS

    return score

def evaluate(board):
    score = 0
    score += material_score(board)
    score += center_control_bonus(board)
    score += pawn_structure_score(board)  # suoraan kutsuttuna toistaiseksi
    return score


def order_moves(board):
    """Järjestää lailliset siirrot heuristisesti (kaappaukset, shakki, korotus, keskustan hallinta)"""
    def move_score(move):
        score = 0

        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                score += 10 * victim.piece_type - attacker.piece_type

        if board.gives_check(move):
            score += 5

        if move.promotion:
            score += 20 + (move.promotion * 2)

        if board.is_castling(move):
            score += 3

        if move.to_square in CENTER_SQUARES:
            score += 1

        return score

    return sorted(board.legal_moves, key=move_score, reverse=True)


def alphabeta(board, remaining_depth, initial_depth, alpha, beta, maximizing):
    """
    Alpha-beta-pruningilla varustettu minimax.
    Palauttaa evaluaation ja parhaan siirtosarjan (pv).
    """
    current_depth = initial_depth - remaining_depth

    if remaining_depth == 0 or board.is_game_over(claim_draw=True):
        if board.is_checkmate():
            mate_score = -MATE_SCORE + current_depth
            return (mate_score if maximizing else -mate_score), []
        elif board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0, []
        else:
            return evaluate(board), []

    best_pv = []

    if maximizing:
        max_eval = -inf
        for move in order_moves(board):
            board.push(move)
            eval, pv = alphabeta(board, remaining_depth - 1, initial_depth, alpha, beta, False)
            board.pop()
            if eval > max_eval:
                max_eval = eval
                best_pv = [move] + pv
            alpha = max(alpha, eval)
            if beta <= alpha:
                break  # Beta-karsinta
        return max_eval, best_pv

    else:
        min_eval = inf
        for move in order_moves(board):
            board.push(move)
            eval, pv = alphabeta(board, remaining_depth - 1, initial_depth, alpha, beta, True)
            board.pop()
            if eval < min_eval:
                min_eval = eval
                best_pv = [move] + pv
            beta = min(beta, eval)
            if beta <= alpha:
                break  # Alpha-karsinta
        return min_eval, best_pv


def find_best_move(board, depth=DEFAULT_DEPTH):
    maximizing = board.turn == chess.WHITE
    eval_score, pv = alphabeta(board, depth, depth, -inf, inf, maximizing)
    return eval_score, pv
