# engine.py
import chess
from math import inf

DEFAULT_DEPTH = 2
MAX_DEPTH = 4
MATE_SCORE = 10_000 # Matin arvio, jotta mate N toimii järkevästi


def evaluate(board):
    """Yksinkertainen materiaalipohjainen evaluointi"""
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3.1,
        chess.BISHOP: 3.2,
        chess.ROOK: 5,
        chess.QUEEN: 9
    }

    score = 0

    # Materiaali
    for piece_type in piece_values:
        score += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]
    
    # Keskustan hallinta
    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    for square in center_squares:
        if board.piece_at(square):
            if board.piece_at(square).color == chess.WHITE:
                score += 0.2
            else:
                score -= 0.2

    return score


def minimax(board, remaining_depth, initial_depth, maximizing):
    """
    Minimax-algoritmi, joka palauttaa: (evaluaatio, siirtosarja [pv])
    """
    current_depth = initial_depth - remaining_depth
    if remaining_depth == 0 or board.is_game_over(claim_draw=True):
        if board.is_checkmate():
            # Jos pelaaja jonka vuoro on, on mattiin joutunut, palauta äärimmäinen huono tulos
            mate_depth = current_depth
            mate_score = -MATE_SCORE + mate_depth
            return (mate_score if maximizing else -mate_score), []
        elif board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0, None  # Tasapeli
        else:
            return evaluate(board), []

    best_move = None
    best_pv = []

    # Valkean vuoro
    # Maksimoidaan eval
    if maximizing:
        max_eval = -inf
        for move in board.legal_moves:
            board.push(move)
            eval, pv = minimax(board, remaining_depth -1, initial_depth, False)
            board.pop()
            if eval > max_eval:
                max_eval = eval
                best_move = move
                best_pv = [best_move] + pv
        return max_eval, best_pv
    # Mustan vuoro
    # Minimoidaan eval
    else:
        min_eval = inf
        for move in board.legal_moves:
            board.push(move)
            eval, pv = minimax(board, remaining_depth - 1, initial_depth, True)
            board.pop()
            if eval < min_eval:
                min_eval = eval
                best_move = move
                best_pv = [best_move] + pv
        return min_eval, best_pv


def find_best_move(board, depth=DEFAULT_DEPTH):
    maximizing=board.turn == chess.WHITE
    return minimax(board, depth, depth, maximizing)
