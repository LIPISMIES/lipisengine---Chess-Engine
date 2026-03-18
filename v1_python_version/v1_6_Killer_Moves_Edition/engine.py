# engine.py
# LipisEngine 1.6 with alpha-beta pruning, tranposition tables
# Improved evaluation and move ordering, quiescene search
# AND KILLER MOVES
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

PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3.1,
        chess.BISHOP: 3.2,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0  # Estää KeyErrorin move_score-funktiossa
    }

# Keskusruudut globaalina vakiomuuttujana
CENTER_SQUARES = [chess.D4, chess.D5, chess.E4, chess.E5]
EXTENDED_CENTER_SQUARES = [
    chess.D3, chess.E3, chess.D6, chess.E6,
]
C_FILE_CENTER_SQUARES = [
    chess.C3, chess.C4, chess.C5, chess.C6
]
F_FILE_CENTER_SQUARES = [
    chess.F3, chess.F4, chess.F5, chess.F6
]
CENTER_SQUARE_BONUS = 0.26
CENTER_SQUARE_ATTACK_BONUS = 0.12
EXTENDED_CENTER_SQUARE_BONUS = 0.06
EXTENDED_CENTER_SQUARE_ATTACK_BONUS = 0.03

C_FILE_CENTER_SQUARE_BONUS = 0.07
C_FILE_CENTER_SQUARE_ATTACK_BONUS = 0.02
F_FILE_CENTER_SQUARE_BONUS = 0.07
F_FILE_CENTER_SQUARE_ATTACK_BONUS = 0.02

CHECK_BONUS = 0.09
CASTLING_BONUS = 0.27
MOBILITY_BONUS = 0.01

KNIGHT_DEV_BONUS = 0.15
BISHOP_DEV_BONUS = 0.13


@dataclass
class SearchContext:
    node_count: int = 0
    max_nodes: int = 1_000_000
    initial_depth: int = 0
    principal_variations: dict = field(default_factory=dict)
    killer_moves: dict = field(default_factory=lambda: {d: [None, None] for d in range(MAX_DEPTH + 1)})
    history_heuristic: dict = field(default_factory=dict)
    counter_moves: dict = field(default_factory=dict)
    max_history_score: float = 0

    max_time: float = DEFAULT_TIME     # sekunteina
    start_time: Optional[float] = None

    def time_exceeded(self) -> bool:
        """Tarkistaa, onko hakuaika ylitetty."""
        if self.start_time is None:
            return False
        return (time.time() - self.start_time) >= self.max_time


def material_score(board):
    score = 0
    for piece_type, value in PIECE_VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value
    return score


def center_control_bonus(board):
    bonus = 0
    for square in CENTER_SQUARES:
        # Nappulat keskustassa
        piece = board.piece_at(square)
        if piece:
            bonus += CENTER_SQUARE_BONUS if piece.color == chess.WHITE else -CENTER_SQUARE_BONUS

        # Uhkaus
        bonus += CENTER_SQUARE_ATTACK_BONUS * len(board.attackers(chess.WHITE, square))
        bonus -= CENTER_SQUARE_ATTACK_BONUS * len(board.attackers(chess.BLACK, square))


    for square in EXTENDED_CENTER_SQUARES:
        # Nappulat laajennetussa keskustassa
        piece = board.piece_at(square)
        if piece:
            bonus += EXTENDED_CENTER_SQUARE_BONUS if piece.color == chess.WHITE else -EXTENDED_CENTER_SQUARE_BONUS

        # Uhkaus
        bonus += EXTENDED_CENTER_SQUARE_ATTACK_BONUS * len(board.attackers(chess.WHITE, square))
        bonus -= EXTENDED_CENTER_SQUARE_ATTACK_BONUS * len(board.attackers(chess.BLACK, square))

    for square in C_FILE_CENTER_SQUARES:
        # Nappulat laajennetussa keskustassa
        piece = board.piece_at(square)
        if piece:
            bonus += C_FILE_CENTER_SQUARE_BONUS if piece.color == chess.WHITE else -C_FILE_CENTER_SQUARE_BONUS

        # Uhkaus
        bonus += C_FILE_CENTER_SQUARE_ATTACK_BONUS * len(board.attackers(chess.WHITE, square))
        bonus -= C_FILE_CENTER_SQUARE_ATTACK_BONUS * len(board.attackers(chess.BLACK, square))

    for square in F_FILE_CENTER_SQUARES:
        # Nappulat laajennetussa keskustassa
        piece = board.piece_at(square)
        if piece:
            if piece.piece_type == chess.PAWN:
                bonus += -F_FILE_CENTER_SQUARE_BONUS if piece.color == chess.WHITE else F_FILE_CENTER_SQUARE_BONUS
            else:
                bonus += F_FILE_CENTER_SQUARE_BONUS if piece.color == chess.WHITE else -F_FILE_CENTER_SQUARE_BONUS

        # Uhkaus
        bonus += F_FILE_CENTER_SQUARE_ATTACK_BONUS * len(board.attackers(chess.WHITE, square))
        bonus -= F_FILE_CENTER_SQUARE_ATTACK_BONUS * len(board.attackers(chess.BLACK, square))

    return bonus


def check_bonus(board):
    if board.is_check():
        if board.turn == chess.WHITE:
            return -CHECK_BONUS  # Valkoinen on shakin alla → huonompi valkoiselle
        else:
            return CHECK_BONUS   # Musta on shakin alla → parempi valkoiselle
    return 0


def castling_bonus(board):
    bonus = 0

    white_king_sq = board.king(chess.WHITE)
    black_king_sq = board.king(chess.BLACK)

    # Valkean turvalliset ruudut ja tornien alkuasetelmat
    if white_king_sq in [chess.G1, chess.H1]:
        if board.piece_at(chess.H1) != chess.Piece(chess.ROOK, chess.WHITE):
            bonus += CASTLING_BONUS
    if white_king_sq in [chess.C1, chess.B1]:
        if board.piece_at(chess.A1) != chess.Piece(chess.ROOK, chess.WHITE):
            bonus += CASTLING_BONUS

    # Mustan turvalliset ruudut ja tornien alkuasetelmat
    if black_king_sq in [chess.G8, chess.H8]:
        if board.piece_at(chess.H8) != chess.Piece(chess.ROOK, chess.BLACK):
            bonus -= CASTLING_BONUS
    if black_king_sq in [chess.C8, chess.B8]:
        if board.piece_at(chess.A8) != chess.Piece(chess.ROOK, chess.BLACK):
            bonus -= CASTLING_BONUS

    return bonus


def development_bonus(board):
    bonus = 0
    starting_squares = {
        chess.WHITE: [chess.B1, chess.G1, chess.C1, chess.F1],
        chess.BLACK: [chess.B8, chess.G8, chess.C8, chess.F8],
    }


    for color in [chess.WHITE, chess.BLACK]:
        for square in board.pieces(chess.KNIGHT, color):
            if square not in starting_squares[color]:
                bonus += KNIGHT_DEV_BONUS if color == chess.WHITE else -KNIGHT_DEV_BONUS
        for square in board.pieces(chess.BISHOP, color):
            if square not in starting_squares[color]:
                bonus += BISHOP_DEV_BONUS if color == chess.WHITE else -BISHOP_DEV_BONUS
    return bonus


def mobility_bonus(board):
    white_board = board.copy()
    white_board.turn = chess.WHITE
    white_mobility = len(list(white_board.legal_moves))

    black_board = board.copy()
    black_board.turn = chess.BLACK
    black_mobility = len(list(black_board.legal_moves))

    return MOBILITY_BONUS * (white_mobility - black_mobility)


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


def order_moves(board, context, current_depth, last_move=None):
    moves = list(board.legal_moves)

    counter_move = context.counter_moves.get(last_move) if last_move else None
    key = chess.polyglot.zobrist_hash(board)
    tt_move = None
    if key in transposition_table:
        tt_entry = transposition_table[key]
        tt_move = tt_entry.get("best_move", None)

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
            score += 5.0
        # pisteytys muutoin
        # Killer-move etusijalle, jos quiet ja killer
        if not board.is_capture(move) and not move.promotion:
            killers = context.killer_moves.get(current_depth, [])
            if move == killers[0]:
                score += 1.5
            elif move == killers[1]:
                score += 0.28

            # ⬇️ Historiaheuristiikka-bonus
            key = (move.from_square, move.to_square)
            history_score = context.history_heuristic.get(key, 0)
            max_val = max(context.history_heuristic.values(), default=1)
            context.max_history_score = max_val
            score += history_score / 70

        # Counter-move-heuristiikka.
        if move == counter_move:
            score += 2.5

        # MVV-LVA
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                victim_value = PIECE_VALUES[victim.piece_type]
                attacker_value = PIECE_VALUES[attacker.piece_type]
                score += victim_value * 2.63 - attacker_value

        if board.gives_check(move):
            score += CHECK_BONUS

        if move.promotion:
            promotion_value = {chess.QUEEN: 8, chess.ROOK: 4, chess.BISHOP: 2.2, chess.KNIGHT: 2.2}
            score += 0.1 + promotion_value.get(move.promotion, 0)

        if board.is_castling(move):
            score += CASTLING_BONUS

        # Keskus
        if move.to_square in CENTER_SQUARES:
            score += CENTER_SQUARE_BONUS
        elif move.to_square in EXTENDED_CENTER_SQUARES:
            score += EXTENDED_CENTER_SQUARE_BONUS
        elif move.to_square in C_FILE_CENTER_SQUARES:
            score += C_FILE_CENTER_SQUARE_BONUS
        elif move.to_square in F_FILE_CENTER_SQUARES:
            if board.piece_at(move.from_square) == chess.PAWN:
                score -= F_FILE_CENTER_SQUARE_BONUS
            else:
                score += F_FILE_CENTER_SQUARE_BONUS

        if move.from_square in CENTER_SQUARES:
            score += CENTER_SQUARE_ATTACK_BONUS
        elif move.from_square in EXTENDED_CENTER_SQUARES:
            score += EXTENDED_CENTER_SQUARE_ATTACK_BONUS

        # Kehitys
        starting_squares = {
            chess.WHITE: [chess.B1, chess.G1, chess.C1, chess.F1],
            chess.BLACK: [chess.B8, chess.G8, chess.C8, chess.F8],
        }
        piece = board.piece_at(move.from_square)
        if piece and move.from_square in starting_squares[board.turn]:
            if piece.piece_type == chess.KNIGHT:
                score += KNIGHT_DEV_BONUS
            elif piece.piece_type == chess.BISHOP:
                score += BISHOP_DEV_BONUS
        
        # MOVE-SCORE -DEBUG-TULOSTUS
        # print(move, score)

        return score

    sorted_moves = sorted(moves, key=move_score, reverse=True)

    if tt_move is not None:
        return [tt_move] + sorted_moves
    else:
        return sorted_moves


transposition_table = {}  # Tyhjennetään jokaisen haun alussa (find_best_move)


def alphabeta(board, remaining_depth, alpha, beta, maximizing, context, last_move=None):
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

    ordered_moves = order_moves(board, context, current_depth, last_move)

    # MOVE_ORDER DATA-/DEBUG-TULOSTUS
    # if current_depth <= 2:
    #     print(f"\n[Depth {current_depth}] Ordered moves:")
    #     for idx, move in enumerate(ordered_moves):
    #         print(f"{idx+1}. {move.uci()}")


    for move in ordered_moves:
        board.push(move)
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
            # CUTOFF DATA-/DEBUG-TULOSTUS
            # print(f"info cutoff at move {move.uci()} at depth {current_depth} (α={alpha}, β={beta})")
            # Killer move -päivitys: vain quiet moves
            if not board.is_capture(move) and not board.gives_check(move):
                    context.counter_moves[last_move] = move
                    killers = context.killer_moves.get(current_depth, [None, None])
                    if move != killers[0] and move != killers[1]:
                        context.killer_moves[current_depth] = [move, killers[0]]
                    
                    # ⬇️ Historiaheuristiikka-päivitys
                    key = chess.polyglot.zobrist_hash(board)
                    tt_move = None
                    if key in transposition_table:
                        tt_entry = transposition_table[key]
                        tt_move = tt_entry.get("best_move", None)
                    if move != tt_move and move not in killers:
                        key = (move.from_square, move.to_square)
                        context.history_heuristic[key] = context.history_heuristic.get(key, 0) + 1.7 ** remaining_depth
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
    context.killer_moves = {depth: [None, None] for depth in range(max_depth)}


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

        print(f"info depth {current_depth} score cp {int(score * 100)} nodes {context.node_count} nps {nps} max_history {context.max_history_score} pv {' '.join(pv_san)}")

        if context.time_exceeded():
            break
        if context.node_count >= max_nodes:
            break

    return score, pv_final
