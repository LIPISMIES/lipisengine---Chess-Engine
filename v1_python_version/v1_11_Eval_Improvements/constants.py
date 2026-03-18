# constants.py
# LipisEngine 1.11 - Kaikki globaalit vakiot

import chess

# ----- YLEISET -----

DEFAULT_DEPTH = 6
MAX_DEPTH = 10
MAX_QUIESCENCE_DEPTH = 2  # maksimisyvyys quiescence-hakulle
DEFAULT_MAX_NODES = 1_000_000
DEFAULT_TIME = 120 # Maksimiaika, jos ei määritelty
MATE_SCORE = 10_000 # Matin arvio, jotta mate N toimii järkevästi


# ----- NAPPULOIDEN ARVOT -----

PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3.1,
        chess.BISHOP: 3.2,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0  # Estää KeyErrorin move_score-funktiossa
    }
PROMOTION_VALUES = {chess.QUEEN: 8, chess.ROOK: 4, chess.BISHOP: 2.2, chess.KNIGHT: 2.2}


# ----- PHASE-SCORE -----

PHASE_SCORE_PAWN = 0.4
PHASE_SCORE_MINOR = 1.0
PHASE_SCORE_ROOK = 1.1
PHASE_SCORE_QUEEN = 1.8

PHASE_PAWN_DEV = 0.4
PHASE_MINOR_DEV = 1.5

PHASE_CASTLING = 2.0


# ----- RUUTUJEN LUOKITTELU -----

MINOR_PIECE_STARTING_SQUARES = {
            chess.WHITE: [chess.B1, chess.G1, chess.C1, chess.F1],
            chess.BLACK: [chess.B8, chess.G8, chess.C8, chess.F8],
}
PAWN_STARTING_SQUARES = [
                        chess.A2, chess.B2, chess.C2, chess.D2,
                        chess.E2, chess.F2, chess.G2, chess.H2,
                        chess.A7, chess.B7, chess.C7, chess.D7,
                        chess.E7, chess.F7, chess.G7, chess.H7
]
CENTER_SQUARES = [chess.D4, chess.D5, chess.E4, chess.E5]
EXTENDED_CENTER_SQUARES = [chess.D3, chess.E3, chess.D6, chess.E6]
C_FILE_CENTER_SQUARES = [chess.C3, chess.C4, chess.C5, chess.C6]
F_FILE_CENTER_SQUARES = [chess.F3, chess.F4, chess.F5, chess.F6]


# ----- MOVE SCORE BONUKSET -----

# KUNINGASAKTIIVISUUS
KING_CENTER_BONUS = 0.3
KING_EXTENDED_BONUS = 0.2
KING_F_C_FILE = 0.15
KING_NEAR_PAWN_OWN = 0.06
KING_NEAR_PAWN_ENEMY = 0.09
KING_PASSED_DIST_SCALING = 0.06
# KESKUSTAN HALLINTA
CENTER_SQUARE_BONUS = 0.20
EXTENDED_CENTER_SQUARE_BONUS = 0.06
C_FILE_CENTER_SQUARE_BONUS = 0.07
F_FILE_CENTER_SQUARE_BONUS = 0.07
# KONTROLLOI RUUTUA
CENTER_SQUARE_ATTACK_BONUS = 0.12
EXTENDED_CENTER_SQUARE_ATTACK_BONUS = 0.03
C_FILE_CENTER_SQUARE_ATTACK_BONUS = 0.02
F_FILE_CENTER_SQUARE_ATTACK_BONUS = 0.02
# SHAKKI, KOROTUS JA TORNITUS
CHECK_BONUS = 0.09
PROMOTION_BONUS = 0.1
CASTLING_BONUS = 0.5
CASTLING_RIGHTS_BONUS = 0.25
# NAPPULOIDEN KEHITYS
MOBILITY_BONUS = 0.02
KNIGHT_DEV_BONUS = 0.23
BISHOP_DEV_BONUS = 0.21
QUEEN_MOVE_PENALTY = 0.15


# ----- LMR-vakiot -----

LMR_REDUCTION = 3        # kuinka paljon syvyyttä vähennetään
LMR_DEPTH_THRESHOLD = 3  # kuinka syvällä pitää olla, ennen kuin aletaan vähentämään
LMR_MOVE_THRESHOLD = 3   # kuinka myöhäinen siirto saa LMR:n (esim. neljännestä siirrosta alkaen)
