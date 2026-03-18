#   LipisEngine
#   simple UCI compatible chess engine with added alpha-beta pruning
#   main.py
from uci import uci_loop
import sys


def main():
    try:
        uci_loop()
    except Exception as e:
        print(f"uci_loop crashed with error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
