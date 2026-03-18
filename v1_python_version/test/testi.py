import chess

test_board = chess.Board()
test_board.set_fen(chess.STARTING_FEN)

luku = 10_000

print(luku)

for move in test_board.legal_moves:
    print(move)