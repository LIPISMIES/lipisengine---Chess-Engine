// board.cpp
/*
 * Chess board
 */

#include "board.h"

const Position STARTPOS{generate_startpos()};

Position generate_startpos() {
    Position pos{};
    // White pieces
    pos.pieces[static_cast<int>(Color::WHITE)][static_cast<int>(PieceType::KING)] =
        bitboard_of(Square::E1);
    pos.pieces[static_cast<int>(Color::WHITE)][static_cast<int>(PieceType::QUEEN)] =
        bitboard_of(Square::D1);
    pos.pieces[static_cast<int>(Color::WHITE)][static_cast<int>(PieceType::ROOK)] =
        bitboard_of(Square::A1) | bitboard_of(Square::H1);
    pos.pieces[static_cast<int>(Color::WHITE)][static_cast<int>(PieceType::BISHOP)] =
        bitboard_of(Square::C1) | bitboard_of(Square::F1);
    pos.pieces[static_cast<int>(Color::WHITE)][static_cast<int>(PieceType::KNIGHT)] =
        bitboard_of(Square::B1) | bitboard_of(Square::G1);
    pos.pieces[static_cast<int>(Color::WHITE)][static_cast<int>(PieceType::PAWN)] =
        bitboard_of(Square::A2) | bitboard_of(Square::B2) | bitboard_of(Square::C2) |
        bitboard_of(Square::D2) | bitboard_of(Square::E2) | bitboard_of(Square::F2) |
        bitboard_of(Square::G2) | bitboard_of(Square::H2);

    // Black pieces
    pos.pieces[static_cast<int>(Color::BLACK)][static_cast<int>(PieceType::KING)] =
        bitboard_of(Square::E8);
    pos.pieces[static_cast<int>(Color::BLACK)][static_cast<int>(PieceType::QUEEN)] =
        bitboard_of(Square::D8);
    pos.pieces[static_cast<int>(Color::BLACK)][static_cast<int>(PieceType::ROOK)] =
        bitboard_of(Square::A8) | bitboard_of(Square::H8);
    pos.pieces[static_cast<int>(Color::BLACK)][static_cast<int>(PieceType::BISHOP)] =
        bitboard_of(Square::C8) | bitboard_of(Square::F8);
    pos.pieces[static_cast<int>(Color::BLACK)][static_cast<int>(PieceType::KNIGHT)] =
        bitboard_of(Square::B8) | bitboard_of(Square::G8);
    pos.pieces[static_cast<int>(Color::BLACK)][static_cast<int>(PieceType::PAWN)] =
        bitboard_of(Square::A7) | bitboard_of(Square::B7) | bitboard_of(Square::C7) |
        bitboard_of(Square::D7) | bitboard_of(Square::E7) | bitboard_of(Square::F7) |
        bitboard_of(Square::G7) | bitboard_of(Square::H7);
    return pos;
}
