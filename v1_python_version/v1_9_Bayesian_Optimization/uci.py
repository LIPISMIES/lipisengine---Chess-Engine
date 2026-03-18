# uci.py
# LipisEngine 1.7 - UCI-kommunikaatio
import chess
import sys
from engine import find_best_move, DEFAULT_DEPTH, MAX_DEPTH, MATE_SCORE

board = chess.Board()


def uci_loop():
    while True:
        line = sys.stdin.readline()
        if not line:
            break  # EOF
        line = line.strip()
        # kertoo moottorin tiedot ja uci-yhteensopivuuden
        if line == "uci":
            print("id name LipisEngine 1.7 StatsCollector", flush=True)
            print("id author Jaakko Simonen 'LIPISMIES'", flush=True)
            print("uciok", flush=True)  # 👈 varmista ettei jää puskurissa roikkumaan
        # tarkistaa onko moottori valmis ottamaan uci-komnetoja vastaan
        elif line == "isready":
            print("readyok")
        # position-komento asettaa tutkittavan aseman
        elif line.startswith("position"):
            set_position(line)
        # go-komento etsii parhaan siirron
        elif line.startswith("go"):
            tokens = line.strip().split()
            if "depth" in tokens:
                depth_index = tokens.index("depth") + 1
                try:
                    requested_depth = int(tokens[depth_index])
                    depth = min(requested_depth, MAX_DEPTH)
                    if requested_depth > MAX_DEPTH:
                        print(f"info string Depth {requested_depth} exceeds MAX_DEPTH={MAX_DEPTH}, using {depth}")
                except (IndexError, ValueError):
                    print(f"info string Invalid depth value, using default depth={DEFAULT_DEPTH}")
                    depth = DEFAULT_DEPTH
            else:
                print(f"info string No depth specified, using default depth={DEFAULT_DEPTH}")
                depth = DEFAULT_DEPTH


            eval_score, pv = find_best_move(board, max_depth=depth)

            # Score-stringin generointi
            if abs(eval_score) >= MATE_SCORE - depth:
                mate_in = MATE_SCORE - abs(eval_score)
                mate_sign = -1 if eval_score < 0 else 1
                print(f"info depth {depth} score mate {mate_sign * mate_in} pv {' '.join(move.uci() for move in pv)}")
            else:
                cp = int(eval_score * 100)
                pv_string = ' '.join(move.uci() for move in pv) if pv else ''
                print(f"info depth {depth} score cp {cp} pv {pv_string}")

            bestmove = pv[0].uci() if pv else "0000"
            print(f"bestmove {bestmove}")

        # quit-komento lopettaa moottorin toiminnan
        elif line == "quit":
            break


def set_position(line):
    global board
    tokens = line.strip().split()

    # Aseman alustus
    if "startpos" in tokens:
        board.set_fen(chess.STARTING_FEN)
    elif "fen" in tokens:
        fen_index = tokens.index("fen") + 1
        fen = " ".join(tokens[fen_index:fen_index + 6])
        board.set_fen(fen)
    else:
        # Ei aloitusasemaa annettu – tämä ei ole UCI:n mukaista
        print("info string Warning: no startpos or fen in position command")
        return

    move_index = tokens.index("moves") + 1 if "moves" in tokens else len(tokens)

    # Siirrä jäljellä olevat siirrot
    for move_str in tokens[move_index:]:
        try:
            move = chess.Move.from_uci(move_str)
            if move in board.legal_moves:
                board.push(move)
            else:
                print(f"info string Illegal move in position: {move_str}")
        except ValueError:
            print(f"info string Invalid UCI move string: {move_str}")

