// types.h
/*
 * Common types and helpers for a bitboard-based chess engine.
 * - Squares indexed 0..63 (a1 = 0, h8 = 63) in little-endian rank-file order.
 * - U64 = 64-bit unsigned integer for bitboards.
 * - Portable bit operations using C++20 <bit> utilities.
 */

#pragma once

#include <cstdint>  // std::uint64_t
#include <bit>      // std::popcount, std::countr_zero

// Short alias for 64-bit unsigned integer used as a bitboard.
// Keeps code concise and semantically clear.
using U64 = std::uint64_t;
static_assert(sizeof(U64) == 8, "U64 must be exactly 64 bits");

// Side to move / piece color.
enum Color { WHITE = 0, BLACK = 1 };

// Flip side: ~WHITE == BLACK, ~BLACK == WHITE.
inline Color operator~(Color color) {
    return Color(color ^ 1);
}

// Board squares in little-endian rank-file order.
// a1 = 0, b1 = 1, ..., h8 = 63.
// SQ_NONE is a sentinel for "no square".
enum Square : int {
  A1=0,B1,C1,D1,E1,F1,G1,H1,
  A2,B2,C2,D2,E2,F2,G2,H2,
  A3,B3,C3,D3,E3,F3,G3,H3,
  A4,B4,C4,D4,E4,F4,G4,H4,
  A5,B5,C5,D5,E5,F5,G5,H5,
  A6,B6,C6,D6,E6,F6,G6,H6,
  A7,B7,C7,D7,E7,F7,G7,H7,
  A8,B8,C8,D8,E8,F8,G8,H8,
  SQ_NONE = 64
};

// Extract file (0..7 for a..h) from a Square index.
inline int file_of(Square square) {
    return static_cast<int>(square) & 7;
}

// Extract rank (0..7 for ranks 1..8) from a Square index.
inline int rank_of(Square square) {
    return static_cast<int>(square) >> 3;
}

// Return a bitboard with a single bit set at the given square.
// If SQ_NONE, returns 0 to avoid undefined shift behavior.
inline U64 BB(Square square) {
    if (square == SQ_NONE) {
        return 0;
    }
    return U64(1) << static_cast<int>(square);
}

// Population count: number of 1-bits in the bitboard.
// Portable and fast with C++20 std::popcount.
inline int popcnt(U64 bitboard) {
    return std::popcount(bitboard);
}

// Index of least significant 1-bit (LSB).
// Returns -1 if bitboard == 0 (no bits set).
inline int lsb_index(U64 bitboard) {
    if (bitboard == 0)
        return -1;
    return static_cast<int>(std::countr_zero(bitboard));
}

// LSB as a Square (SQ_NONE if bitboard == 0).
inline Square lsb_square(U64 bitboard) {
    if (bitboard == 0) {
        return SQ_NONE;
    }
    return static_cast<Square>(static_cast<int>(std::countr_zero(bitboard)));
}

// Pop (clear) the least significant 1-bit and return its Square.
// Returns SQ_NONE if bitboard was 0.
inline Square pop_lsb(U64& bitboard) {
    const Square sq = lsb_square(bitboard);
    if (sq != SQ_NONE) {
        bitboard &= (bitboard - 1);
    }
    return sq;
}
