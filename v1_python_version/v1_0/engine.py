# engine.py
# LipisEngine 1.0 with alpha-beta pruning
import chess
from math import inf

DEFAULT_DEPTH = 4
MAX_DEPTH = 8
MATE_SCORE = 10_000 # Matin arvio, jotta mate N toimii järkevästi

# Globaali keskiruutujen lista
CENTER_SQUARES = [chess.D4, chess.E4, chess.D5, chess.E5]


def evaluate(board):
    """Yksinkertainen evaluointifunktio: materiaali + keskustan hallinta"""
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3.05,
        chess.BISHOP: 3.1,
        chess.ROOK: 5,
        chess.QUEEN: 9
    }
    score = 0

    # Materiaali
    for piece_type in piece_values:
        score += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]

    # Keskustan hallinta
    for square in CENTER_SQUARES:
        piece = board.piece_at(square)
        if piece:
            if piece.color == chess.WHITE:
                score += 0.1
            else:
                score -= 0.1

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
