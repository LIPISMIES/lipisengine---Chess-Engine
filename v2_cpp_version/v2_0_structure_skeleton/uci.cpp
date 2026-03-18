// uci.cpp
/*
 * Implementation of the UCI command loop for Lipisengine.
 *
 * Goal of this file (current milestone):
 * - Be whitespace-robust (leading/trailing/multiple spaces, tabs).
 * - Dispatch commands based on tokens instead of exact string matches.
 * - Follow UCI "ignore unknown tokens and continue parsing" spirit by scanning
 *   the line for the first known command token.
 *
 * NOTE: Chess logic (board, movegen, search) is not implemented yet.
 *       "position" and "go" are parsed, but still behave as stubs.
 */

#include "uci.h"

#include <cctype>
#include <iostream>
#include <string>
#include <vector>

// Trim leading and trailing whitespace (spaces, tabs, etc.)
static inline std::string trim_copy(const std::string& s) {
    size_t b = 0;
    while (b < s.size() && std::isspace(static_cast<unsigned char>(s[b]))) {
        ++b;
    }
    size_t e = s.size();
    while (e > b && std::isspace(static_cast<unsigned char>(s[e - 1]))) {
        --e;
    }
    return s.substr(b, e - b);
}

// Split by whitespace into tokens.
static inline std::vector<std::string> split_ws(const std::string& s) {
    std::vector<std::string> out;
    out.reserve(16);

    size_t i = 0;
    while (i < s.size()) {
        while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i]))) {
            ++i;
        }
        if (i >= s.size()) {
            break;
        }
        const size_t start = i;
        while (i < s.size() && !std::isspace(static_cast<unsigned char>(s[i]))) {
            ++i;
        }
        out.emplace_back(s.substr(start, i - start));
    }

    return out;
}

// Join tokens into a single space-separated string (lossy but sufficient for stubs).
static inline std::string join_tokens(const std::vector<std::string>& t, size_t start_index) {
    std::string out;
    for (size_t i = start_index; i < t.size(); ++i) {
        if (!out.empty()) {
            out.push_back(' ');
        }
        out += t[i];
    }
    return out;
}

static inline bool is_known_command(const std::string& tok) {
    // Commands we currently recognize/handle (even if some are stubs).
    return tok == "uci" ||
           tok == "isready" ||
           tok == "ucinewgame" ||
           tok == "setoption" ||
           tok == "debug" ||
           tok == "position" ||
           tok == "go" ||
           tok == "stop" ||
           tok == "ponderhit" ||
           tok == "quit";
}

void UCI::loop() {
    // Slightly faster I/O. Keep std::endl usage where we want an immediate flush.
    std::ios::sync_with_stdio(false);

    bool debugEnabled = false;
    bool stopRequested = false; // placeholder for future search stop flag

    std::string rawLine;

    // Main loop: read line by line from standard input.
    while (std::getline(std::cin, rawLine)) {
        const std::string line = trim_copy(rawLine);
        if (line.empty()) {
            continue;
        }

        std::vector<std::string> tokens = split_ws(line);
        if (tokens.empty()) {
            continue;
        }

        // UCI spec: ignore unknown command/token and try to parse the rest of the line.
        // We implement this by scanning the line for the first known command token.
        size_t cmdIndex = 0;
        while (cmdIndex < tokens.size() && !is_known_command(tokens[cmdIndex])) {
            ++cmdIndex;
        }
        if (cmdIndex >= tokens.size()) {
            // Entire line contains no known command -> ignore.
            continue;
        }

        const std::string& cmd = tokens[cmdIndex];

        // Convenience: arguments start after the command token.
        const size_t argsIndex = cmdIndex + 1;

        if (cmd == "uci") {
            // Identify engine and list supported options, then acknowledge with uciok.
            std::cout << "id name LipisEngine v2 (C++)" << std::endl;
            std::cout << "id author Jaakko Simonen 'LIPISMIES'" << std::endl;

            // Minimal, commonly supported options (values are placeholders for now).
            std::cout << "option name Hash type spin default 16 min 1 max 1024" << std::endl;
            std::cout << "option name Ponder type check default false" << std::endl;
            std::cout << "option name MultiPV type spin default 1 min 1 max 8" << std::endl;

            std::cout << "uciok" << std::endl;
            continue;
        }

        if (cmd == "isready") {
            // Must always respond with readyok (even while searching in the future).
            std::cout << "readyok" << std::endl;
            continue;
        }

        if (cmd == "quit") {
            break;
        }

        if (cmd == "debug") {
            // "debug on|off"
            if (argsIndex < tokens.size()) {
                if (tokens[argsIndex] == "on") {
                    debugEnabled = true;
                } else if (tokens[argsIndex] == "off") {
                    debugEnabled = false;
                }
            }
            // No mandatory response for debug.
            continue;
        }

        if (cmd == "ucinewgame") {
            // TODO: reset internal game state (hash tables, repetition history, etc.)
            stopRequested = false;
            if (debugEnabled) {
                std::cout << "info string ucinewgame received (stub)" << std::endl;
            }
            continue;
        }

        if (cmd == "setoption") {
            // Format: setoption name <id> [value <x>]
            // NOTE: <id> and <x> may contain spaces; do not rely purely on tokens.
            // For now we only parse the basic markers and ignore content.
            if (debugEnabled) {
                std::cout << "info string setoption received (stub): " << join_tokens(tokens, cmdIndex) << std::endl;
            }
            continue;
        }

        if (cmd == "position") {
            // Format:
            // position [fen <fenstring> | startpos] moves <move1> ... <moveN>
            //
            // We only parse the structure at a token level for now.
            // Real FEN parsing and move application will come later.
            bool hasStartpos = false;
            bool hasFen = false;
            bool hasMoves = false;

            // Scan tokens after "position" to find "startpos"/"fen"/"moves".
            for (size_t i = argsIndex; i < tokens.size(); ++i) {
                if (tokens[i] == "startpos") {
                    hasStartpos = true;
                } else if (tokens[i] == "fen") {
                    hasFen = true;
                } else if (tokens[i] == "moves") {
                    hasMoves = true;
                    break;
                }
            }

            if (debugEnabled) {
                std::cout << "info string position received (stub):"
                          << " startpos=" << (hasStartpos ? "true" : "false")
                          << " fen=" << (hasFen ? "true" : "false")
                          << " moves=" << (hasMoves ? "true" : "false")
                          << std::endl;
            }

            // TODO: Store "current position" in a Board object and apply moves.
            continue;
        }

        if (cmd == "go") {
            // Format: go [wtime <x>] [btime <x>] [winc <x>] [binc <x>] [movestogo <x>]
            //            [depth <x>] [nodes <x>] [mate <x>] [movetime <x>] [infinite]
            //            [searchmoves <m1> ...]
            //
            // We do not search yet; we still return a nullmove.
            stopRequested = false;

            if (debugEnabled) {
                std::cout << "info string go received (stub): " << join_tokens(tokens, cmdIndex) << std::endl;
            }

            // TODO: Start search (likely in a separate thread) and eventually output bestmove.
            std::cout << "bestmove 0000" << std::endl;
            continue;
        }

        if (cmd == "stop") {
            // TODO: When search is implemented, set a stop flag checked by the search.
            stopRequested = true;
            if (debugEnabled) {
                std::cout << "info string stop received (stub)" << std::endl;
            }
            continue;
        }

        if (cmd == "ponderhit") {
            // TODO: Switch from pondering to normal search.
            if (debugEnabled) {
                std::cout << "info string ponderhit received (stub)" << std::endl;
            }
            continue;
        }

        // Any remaining lines/commands are ignored.
    }
}
