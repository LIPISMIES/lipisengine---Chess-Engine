// main.cpp
/*
 * LipisEngine 2.0
 * Structure skeleton for C++-based chess engine
 * Entry point of the program: initializes the UCI loop.
 * All communication happens via UCI (Universal Chess Interface).
 */

#include "uci.h"

int main() {
    // Create a temporary UCI object and start the main loop.
    // The loop reads commands from standard input and writes responses to standard output.
    UCI{}.loop();
}
