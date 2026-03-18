# engine.py
# LipisEngine 1.5 with alpha-beta pruning, tranposition tables
# Improved evaluation and move ordering, quiescene search
import chess
import chess.polyglot
from math import inf
from typing import Optional
from dataclasses import dataclass, field
import time

DEFAULT_DEPTH = 4
MAX_DEPTH = 8
MAX_QUIESCENCE_DEPTH = 2  # maksimisyvyys quiescence-hakulle
DEFAULT_MAX_NODES = 1_000_000
DEFAULT_TIME = 120 # Maksimiaika, jos ei määritelty
MATE_SCORE = 10_000 # Matin arvio, jotta mate N toimii järkevästi

# Keskusruudut globaalina vakiomuuttujana
CENTER_SQUARES = [chess.D4, chess.D5, chess.E4, chess.E5]
EXTENDED_CENTER_SQUARES = [
    chess.C3, chess.C4, chess.C5, chess.C6,
    chess.D3, chess.E3, chess.D6, chess.E6,
    chess.F3, chess.F4, chess.F5, chess.F6
]


@dataclass
class SearchContext:
    node_count: int = 0
    max_nodes: int = 1_000_000
    initial_depth: int = 0
    principal_variations: dict = field(default_factory=dict)
    
    max_time: float = DEFAULT_TIME     # sekunteina
    start_time: Optional[float] = None

    def time_exceeded(self) -> bool:
        """Tarkistaa, onko hakuaika ylitetty."""
        if self.start_time is None:
            return False
        return (time.time() - self.start_time) >= self.max_time


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
            bonus += 0.26 if piece.color == chess.WHITE else -0.26

        # Uhkaus
        bonus += 0.12 * len(board.attackers(chess.WHITE, square))
        bonus -= 0.12 * len(board.attackers(chess.BLACK, square))


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
            return -0.09  # Valkoinen on shakin alla → huonompi valkoiselle
        else:
            return 0.09   # Musta on shakin alla → parempi valkoiselle
    return 0


def castling_bonus(board):
    bonus = 0

    white_king_sq = board.king(chess.WHITE)
    black_king_sq = board.king(chess.BLACK)

    # Valkean turvalliset ruudut ja tornien alkuasetelmat
    if white_king_sq in [chess.G1, chess.H1]:
        if board.piece_at(chess.H1) != chess.Piece(chess.ROOK, chess.WHITE):
            bonus += 0.27
    if white_king_sq in [chess.C1, chess.B1]:
        if board.piece_at(chess.A1) != chess.Piece(chess.ROOK, chess.WHITE):
            bonus += 0.27

    # Mustan turvalliset ruudut ja tornien alkuasetelmat
    if black_king_sq in [chess.G8, chess.H8]:
        if board.piece_at(chess.H8) != chess.Piece(chess.ROOK, chess.BLACK):
            bonus -= 0.27
    if black_king_sq in [chess.C8, chess.B8]:
        if board.piece_at(chess.A8) != chess.Piece(chess.ROOK, chess.BLACK):
            bonus -= 0.27

    return bonus


def development_bonus(board):
    bonus = 0
    starting_squares = {
        chess.WHITE: [chess.B1, chess.G1, chess.C1, chess.F1],
        chess.BLACK: [chess.B8, chess.G8, chess.C8, chess.F8],
    }
    knight_value = 0.15
    bishop_value = 0.13

    for color in [chess.WHITE, chess.BLACK]:
        for square in board.pieces(chess.KNIGHT, color):
            if square not in starting_squares[color]:
                bonus += knight_value if color == chess.WHITE else -knight_value
        for square in board.pieces(chess.BISHOP, color):
            if square not in starting_squares[color]:
                bonus += bishop_value if color == chess.WHITE else -bishop_value
    return bonus


def mobility_bonus(board):
    white_board = board.copy()
    white_board.turn = chess.WHITE
    white_mobility = len(list(white_board.legal_moves))

    black_board = board.copy()
    black_board.turn = chess.BLACK
    black_mobility = len(list(black_board.legal_moves))

    return 0.01 * (white_mobility - black_mobility)


def evaluate(board):
    score = 0
    score += material_score(board)
    score += center_control_bonus(board)
    score += check_bonus(board)
    score += castling_bonus(board)
    score += development_bonus(board)
    score += mobility_bonus(board)
    return score    


def generate_quiescence_moves(board):
    yield from board.generate_legal_captures()


def quiescence(board, alpha, beta, maximizing, context, depth=0):
    if context.node_count >= context.max_nodes:
        return evaluate(board), []
    context.node_count += 1
    stand_pat = evaluate(board)

    if maximizing:
        if stand_pat >= beta:
            return beta, []
        if alpha < stand_pat:
            alpha = stand_pat
    else:
        if stand_pat <= alpha:
            return alpha, []
        if beta > stand_pat:
            beta = stand_pat

    if depth >= MAX_QUIESCENCE_DEPTH:
        return stand_pat, []

    best_value = stand_pat
    best_pv = []

    for move in generate_quiescence_moves(board):
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


def order_moves(board, context):
    moves = list(board.legal_moves)

    key = chess.polyglot.zobrist_hash(board)
    tt_move = None
    if key in transposition_table:
        tt_entry = transposition_table[key]
        tt_move = tt_entry.get("best_move", None)

    pv_bonus_moves = set(context.principal_variations) if context.principal_variations else set()

    # Erottele TT-siirto ja muut
    if tt_move is not None and tt_move in moves:
        moves.remove(tt_move)
    else:
        tt_move = None  # Ei ole käytössä

    def move_score(move):
        if move in pv_bonus_moves:
            return 10000
        # pisteytys muutoin
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

        # Keskus
        if move.to_square in CENTER_SQUARES:
            score += 10
        elif move.to_square in EXTENDED_CENTER_SQUARES:
            score += 5

        if move.from_square in CENTER_SQUARES:
            score += 5
        elif move.from_square in EXTENDED_CENTER_SQUARES:
            score += 2

        # Kehitys
        starting_squares = {
            chess.WHITE: [chess.B1, chess.G1, chess.C1, chess.F1],
            chess.BLACK: [chess.B8, chess.G8, chess.C8, chess.F8],
        }
        piece = board.piece_at(move.from_square)
        if piece and move.from_square in starting_squares[board.turn]:
            if piece.piece_type == chess.KNIGHT:
                score += 15
            elif piece.piece_type == chess.BISHOP:
                score += 13
            
        return score

    sorted_moves = sorted(moves, key=move_score, reverse=True)

    if tt_move is not None:
        return [tt_move] + sorted_moves
    else:
        return sorted_moves


transposition_table = {}  # Tyhjennetään jokaisen haun alussa (find_best_move)


def alphabeta(board, remaining_depth, alpha, beta, maximizing, context):
    if context.node_count >= context.max_nodes:
        return evaluate(board), []
    context.node_count += 1

    alpha_orig = alpha
    key = chess.polyglot.zobrist_hash(board)
    
    if key in transposition_table:
        entry = transposition_table[key]
        if entry["depth"] >= remaining_depth:
            flag = entry.get("flag", "EXACT")
            if flag == "EXACT":
                return entry["value"], entry["pv"]
            elif flag == "LOWERBOUND" and entry["value"] > alpha:
                alpha = entry["value"]
            elif flag == "UPPERBOUND" and entry["value"] < beta:
                beta = entry["value"]
            if alpha >= beta:
                return entry["value"], entry["pv"]

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

    ordered_moves = order_moves(board, context)

    for move in ordered_moves:
        board.push(move)
        eval, pv = alphabeta(board, remaining_depth - 1, alpha, beta, not maximizing, context)
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
    
    # Arvioinnin tallennus ja boundin määrittely
    if best_value <= alpha_orig:
        flag = "UPPERBOUND"
    elif best_value >= beta:
        flag = "LOWERBOUND"
    else:
        flag = "EXACT"

    # Vain jos ei ole olemassa tai nyt tutkitaan syvemmälle
    if key not in transposition_table or remaining_depth > transposition_table[key]["depth"]:
        transposition_table[key] = {
            "depth": remaining_depth,
            "value": best_value,
            "pv": best_pv,
            "best_move": best_pv[0] if best_pv else None,
            "flag": (
                "EXACT" if alpha_orig < best_value < beta
                else "LOWERBOUND" if best_value >= beta
                else "UPPERBOUND"
            )
        }

    context.principal_variations[current_depth] = best_pv


    return best_value, best_pv


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

    for current_depth in range(1, max_depth + 1):
        iteration_start = time.time()
        context.node_count = 0

        if context.time_exceeded():
            break

        score, pv = alphabeta(board, current_depth, -inf, inf, maximizing, context)
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

        print(f"info depth {current_depth} score cp {int(score * 100)} nodes {context.node_count} nps {nps} pv {' '.join(pv_san)}")

        if context.time_exceeded():
            break
        if context.node_count >= max_nodes:
            break

    return score, pv_final
