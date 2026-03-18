# evaluate.py
# LipisEngine 1.10
# arviointifunktiot

import chess
from constants import *


def game_phase_score(board):
    # Painokertoimet
    phase = 0
    max_phase = (
        16 * PHASE_SCORE_PAWN +
        8 * PHASE_SCORE_MINOR +
        4 * PHASE_SCORE_ROOK +
        2 * PHASE_SCORE_QUEEN +
        16 * PHASE_PAWN_DEV +
        8 * PHASE_MINOR_DEV +
        2 * PHASE_CASTLING
    ) # skaalaamisen yläraja (tällä hetkellä 31.4)
    # Materiaalipohja: 0.4–1.8 pistettä
    phase += PHASE_SCORE_PAWN * len(board.pieces(chess.PAWN, chess.WHITE))
    phase += PHASE_SCORE_PAWN * len(board.pieces(chess.PAWN, chess.BLACK))
    phase += PHASE_SCORE_MINOR * len(board.pieces(chess.KNIGHT, chess.WHITE))
    phase += PHASE_SCORE_MINOR * len(board.pieces(chess.KNIGHT, chess.BLACK))
    phase += PHASE_SCORE_MINOR * len(board.pieces(chess.BISHOP, chess.WHITE))
    phase += PHASE_SCORE_MINOR * len(board.pieces(chess.BISHOP, chess.BLACK))
    phase += PHASE_SCORE_ROOK * len(board.pieces(chess.ROOK, chess.WHITE))
    phase += PHASE_SCORE_ROOK * len(board.pieces(chess.ROOK, chess.BLACK))
    phase += PHASE_SCORE_QUEEN * len(board.pieces(chess.QUEEN, chess.WHITE))
    phase += PHASE_SCORE_QUEEN * len(board.pieces(chess.QUEEN, chess.BLACK))

    # Kehitys: enemmän kehittämättömiä → avaus

    for color in [chess.WHITE, chess.BLACK]:
        for sq in MINOR_PIECE_STARTING_SQUARES[color]:
            piece = board.piece_at(sq)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                phase += PHASE_MINOR_DEV # kehittämättömästä upseerista +0.5

    for sq in (PAWN_STARTING_SQUARES):
        piece = board.piece_at(sq)
        if piece and piece.piece_type == chess.PAWN:
            phase += PHASE_PAWN_DEV  # kehittämättömästä upseerista +0.5

    # Linnoittautuminen: kumpikaan ei linnoittautunut → avaus
    if board.has_castling_rights(chess.WHITE):
        phase += PHASE_CASTLING
    if board.has_castling_rights(chess.BLACK):
        phase += PHASE_CASTLING

    # Skaalaus
    normalized = phase / max_phase
    return max(0.0, min(1.0, normalized))


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

    # linnoitusoikeus
    if board.has_castling_rights(chess.WHITE):
        bonus += CASTLING_RIGHTS_BONUS
    if board.has_castling_rights(chess.BLACK):
        bonus -= CASTLING_RIGHTS_BONUS

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


def queen_move_penalty(board):
    bonus = 0
    queen_starting_squares = {
            chess.WHITE: chess.D1,
            chess.BLACK: chess.D8
        }
    for color in [chess.WHITE, chess.BLACK]:
        for square in board.pieces(chess.QUEEN, color):
            if square == queen_starting_squares[color]:
                bonus += -QUEEN_MOVE_PENALTY if color == chess.WHITE else QUEEN_MOVE_PENALTY
    return bonus


def mobility_bonus(board):
    white_board = board.copy()
    white_board.turn = chess.WHITE
    white_mobility = len(list(white_board.legal_moves))

    black_board = board.copy()
    black_board.turn = chess.BLACK
    black_mobility = len(list(black_board.legal_moves))

    return MOBILITY_BONUS * (white_mobility - black_mobility)


def is_passed(pawn_sq, board, color):
    pawn_file = chess.square_file(pawn_sq)
    pawn_rank = chess.square_rank(pawn_sq)
    for dx in [-1, 0, 1]:
        adj_file = pawn_file + dx
        if 0 <= adj_file <= 7:
            forward_ranks = range(pawn_rank + 1, 8) if color == chess.WHITE else range(pawn_rank - 1, -1, -1)
            for rank in forward_ranks:
                sq = chess.square(adj_file, rank)
                if board.piece_at(sq) == chess.Piece(chess.PAWN, not color):
                    return False
    return True


def passed_pawn_bonus(board):
    bonus = 0
    for color in [chess.WHITE, chess.BLACK]:
        pawns = board.pieces(chess.PAWN, color)
        for pawn_square in pawns:
            pawn_rank = chess.square_rank(pawn_square)
            if is_passed(pawn_square,board, color):
                # Lasketaan etäisyys korotusriville
                distance = max(0, 7 - pawn_rank) if color == chess.WHITE else max(0, pawn_rank)
                value = 0.2 * (6 - distance)  # 0.2 – 1.0 välillä
                bonus += value if color == chess.WHITE else -value
    return bonus


def king_activity(board):
    bonus = 0
    for color in [chess.WHITE, chess.BLACK]:
        king_sq = board.king(color)
        if king_sq is None:
            continue  # Kuningas puuttuu (teoriassa mahdollista epänormaalitilanteessa)

        # 1. Keskustan läheisyys
        if king_sq in CENTER_SQUARES:
            bonus += KING_CENTER_BONUS if color == chess.WHITE else -KING_CENTER_BONUS
        elif king_sq in EXTENDED_CENTER_SQUARES:
            bonus += KING_EXTENDED_BONUS if color == chess.WHITE else -KING_EXTENDED_BONUS
        elif king_sq in C_FILE_CENTER_SQUARES or king_sq in F_FILE_CENTER_SQUARES:
            bonus += KING_F_C_FILE if color == chess.WHITE else -KING_F_C_FILE

        # 2. Sotilaiden määrä viereisillä ruuduilla
        nearby_squares = [sq for sq in chess.SquareSet(chess.BB_KING_ATTACKS[king_sq])]
        own_pawns = 0
        enemy_pawns = 0
        for sq in nearby_squares:
            piece = board.piece_at(sq)
            if piece and piece.piece_type == chess.PAWN:
                if piece.color == color:
                    own_pawns += 1
                else:
                    enemy_pawns += 1

        activity_bonus = own_pawns * KING_NEAR_PAWN_OWN + enemy_pawns * KING_NEAR_PAWN_ENEMY  # uhkaus tärkeämpi kuin suoja
        bonus += activity_bonus if color == chess.WHITE else -activity_bonus

        # 3. Etäisyys vapaasotilaisiin
        passed_pawns = []
        # Voidaan yhdistää yhdellä for-loopilla
        for pawn_sq in board.pieces(chess.PAWN, chess.WHITE if color == chess.WHITE else chess.BLACK):
            if is_passed(pawn_sq, board, chess.WHITE if color == chess.WHITE else chess.BLACK):
                passed_pawns.append(pawn_sq)


        if passed_pawns:
            # Manhattan-etäisyys
            k_file, k_rank = chess.square_file(king_sq), chess.square_rank(king_sq)
            total_distance = sum(abs(chess.square_file(p) - k_file) + abs(chess.square_rank(p) - k_rank) for p in passed_pawns)
            avg_distance = total_distance / len(passed_pawns)
            distance_penalty = avg_distance * KING_PASSED_DIST_SCALING  # Skaalaa sopivasti
            bonus += (0.6 - distance_penalty) if color == chess.WHITE else -(0.6 - distance_penalty)

    return bonus


def evaluate(board):
    phase = game_phase_score(board)
    opening_weight = max(0.0, phase - 0.6) * 2.5
    middlegame_weight = max(0.0, 1.0 - phase) * 2.5 if phase > 0.6 else max(0.0, phase - 0.1) * 2
    endgame_weight = max(0.0, 0.5 - phase) * 2.5 if phase > 0.1 else 1.0
    score = 0
    # Materiaali
    score += material_score(board)
    # Avaus
    score += (opening_weight + 0.5 * middlegame_weight) * castling_bonus(board)
    score += (opening_weight + 0.5 * middlegame_weight) * development_bonus(board)
    score += opening_weight * queen_move_penalty(board)
    # Avaus-keskipeli
    score += (0.9 * opening_weight + middlegame_weight) * center_control_bonus(board)
    # Keskipeli
    score += (0.2 * opening_weight + middlegame_weight + 0.2 * endgame_weight) * mobility_bonus(board)
    # Keskipeli-loppupeli
    score += (0.8 * middlegame_weight + endgame_weight) * check_bonus(board)
    # Loppupeli
    score += endgame_weight * passed_pawn_bonus(board)
    # evaluate()-funktion loppuun
    score += endgame_weight * king_activity(board)

    return score