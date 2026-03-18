# engine.py
# LipisEngine 1.4 with alpha-beta pruning, tranposition tables
# Improved evaluation and move ordering
import chess
import chess.polyglot
from math import inf
from functools import lru_cache

DEFAULT_DEPTH = 4
MAX_DEPTH = 8
MATE_SCORE = 10_000 # Matin arvio, jotta mate N toimii järkevästi

# Keskusruudut globaalina vakiomuuttujana
CENTER_SQUARES = [chess.D4, chess.D5, chess.E4, chess.E5]
EXTENDED_CENTER_SQUARES = [
    chess.C3, chess.C4, chess.C5, chess.C6,
    chess.D3, chess.E3, chess.D6, chess.E6,
    chess.F3, chess.F4, chess.F5, chess.F6
]


def material_score(board):
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3.1,
        chess.BISHOP: 3.2,
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
        # Nappulat keskustassa
        piece = board.piece_at(square)
        if piece:
            bonus += 0.25 if piece.color == chess.WHITE else -0.25

        # Uhkaus
        bonus += 0.11 * len(board.attackers(chess.WHITE, square))
        bonus -= 0.11 * len(board.attackers(chess.BLACK, square))


    for square in EXTENDED_CENTER_SQUARES:
        # Nappulat laajennetussa keskustassa
        piece = board.piece_at(square)
        if piece:
            bonus += 0.06 if piece.color == chess.WHITE else -0.06

        # Uhkaus
        bonus += 0.03 * len(board.attackers(chess.WHITE, square))
        bonus -= 0.03 * len(board.attackers(chess.BLACK, square))


    return bonus


def check_bonus(board):
    if board.is_check():
        if board.turn == chess.WHITE:
            return -0.04  # Valkoinen on shakin alla → huonompi valkoiselle
        else:
            return 0.04   # Musta on shakin alla → parempi valkoiselle
    return 0


def castling_bonus(board):
    bonus = 0

    white_king_sq = board.king(chess.WHITE)
    black_king_sq = board.king(chess.BLACK)

    # Valkean turvalliset ruudut ja tornien alkuasetelmat
    if white_king_sq in [chess.G1, chess.H1]:
        if board.piece_at(chess.H1) != chess.Piece(chess.ROOK, chess.WHITE):
            bonus += 0.19
    if white_king_sq in [chess.C1, chess.B1]:
        if board.piece_at(chess.A1) != chess.Piece(chess.ROOK, chess.WHITE):
            bonus += 0.19

    # Mustan turvalliset ruudut ja tornien alkuasetelmat
    if black_king_sq in [chess.G8, chess.H8]:
        if board.piece_at(chess.H8) != chess.Piece(chess.ROOK, chess.BLACK):
            bonus -= 0.19
    if black_king_sq in [chess.C8, chess.B8]:
        if board.piece_at(chess.A8) != chess.Piece(chess.ROOK, chess.BLACK):
            bonus -= 0.19

    return bonus


def queen_move_penalty(board):
    penalty = 0
    # Valkea kuningatar
    if board.piece_at(chess.D1) != chess.Piece(chess.QUEEN, chess.WHITE):
        penalty -= 1.1
    # Valkea kuningatar
    if board.piece_at(chess.D8) != chess.Piece(chess.QUEEN, chess.BLACK):
        penalty += 1.1
    
    return penalty


def evaluate(board):
    score = 0
    score += material_score(board)
    score += center_control_bonus(board)
    score += check_bonus(board)
    score += castling_bonus(board)
    score += queen_move_penalty(board)
    return score


def order_moves(board, principal_variations):
    pv_bonus_moves = []

    for depth in sorted(principal_variations.keys(), reverse=True):
        pv = principal_variations[depth]
        if pv:
            move = pv[0]
            if move in board.legal_moves and move not in pv_bonus_moves:
                pv_bonus_moves.append(move)

    def move_score(move):
        if move in pv_bonus_moves:
            return 10000  # Iso bonus PV-siirrolle

        score = 0

        # MVV-LVA
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                score += 100 * victim.piece_type - attacker.piece_type

        if board.gives_check(move):
            score += 50

        if move.promotion:
            promotion_value = {chess.QUEEN: 90, chess.ROOK: 50, chess.BISHOP: 40, chess.KNIGHT: 30}
            score += 80 + promotion_value.get(move.promotion, 0)

        if board.is_castling(move):
            score += 20

        if move.to_square in CENTER_SQUARES:
            score += 10
        elif move.to_square in EXTENDED_CENTER_SQUARES:
            score += 5

        if move.from_square in CENTER_SQUARES:
            score += 5
        elif move.from_square in EXTENDED_CENTER_SQUARES:
            score += 2

        return score

    # Järjestä loput siirrot heuristiikalla
    return sorted(board.legal_moves, key=move_score, reverse=True)


transposition_table = {}  # Tyhjennetään jokaisen haun alussa (find_best_move)


def alphabeta(board, remaining_depth, initial_depth, alpha, beta, maximizing, principal_variations):
    key = chess.polyglot.zobrist_hash(board)

    if key in transposition_table:
        entry = transposition_table[key]
        if entry["depth"] >= remaining_depth:
            return entry["value"], entry["pv"]

    current_depth = initial_depth - remaining_depth

    if remaining_depth == 0 or board.is_game_over(claim_draw=True):
        if board.is_checkmate():
            score = -MATE_SCORE + current_depth if maximizing else MATE_SCORE - current_depth
            return score, []
        return evaluate(board), []

    best_value = -inf if maximizing else inf
    best_pv = []

    ordered_moves = order_moves(board, principal_variations)

    for move in ordered_moves:
        board.push(move)
        eval, pv = alphabeta(board, remaining_depth - 1, initial_depth, alpha, beta, not maximizing, principal_variations)
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

    transposition_table[key] = {
        "depth": remaining_depth,
        "value": best_value,
        "pv": best_pv
    }

    return best_value, best_pv


def find_best_move(board, max_depth=DEFAULT_DEPTH):
    best_move = None
    principal_variations = {}
    maximizing = board.turn == chess.WHITE

    for current_depth in range(1, max_depth + 1):
        transposition_table.clear()
        score, pv = alphabeta(board, current_depth, current_depth, -inf, inf, maximizing, principal_variations)
        principal_variations[current_depth] = pv

        if pv:
            best_move = pv[0]

        tmp_board = board.copy()
        pv_san = []
        for move in pv:
            if move in tmp_board.legal_moves:
                pv_san.append(tmp_board.san(move))
                tmp_board.push(move)
            else:
                break

        print(f"info depth {current_depth} score cp {int(score * 100)} pv {' '.join(pv_san)}")

    pv_final = principal_variations.get(max_depth, [])
    return score, pv_final
