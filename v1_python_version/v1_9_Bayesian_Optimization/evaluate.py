# LipisEngine 1.7 with StatsCollector
# Improved file structure
# evaluate.py

import chess
from constants import *

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