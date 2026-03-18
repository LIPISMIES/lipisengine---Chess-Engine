# ttable.py
# LipisEngine 1.7 – Transpositiotaulun käsittely

from typing import Optional


class TranspositionTable:
    def __init__(self):
        self.table = {}

    def get(self, key) -> Optional[dict]:
        return self.table.get(key)
   
    def set(self, key, entry):
        self.table[key] = entry

    def store(self, key, depth, value, pv, best_move, flag):
        """Tallentaa tietueen transpositiotauluun."""
        entry = self.table.get(key)
        if not isinstance(entry, dict) or entry is None or depth >= entry["depth"]:
            self.table[key] = {
                "depth": depth,
                "value": value,
                "pv": pv,
                "best_move": best_move,
                "flag": flag
            }

    def __contains__(self, key):
        """Mahdollistaa 'if key in ttable' -tarkistuksen."""
        return key in self.table

    def __len__(self):
        """Mahdollistaa 'len(ttable)' -kutsun."""
        return len(self.table)

    def __str__(self):
        """Palauttaa lyhyen yhteenvedon transpositiotaulusta."""
        lines = [f"TranspositionTable: {len(self.table)} entries"]
        example_items = list(self.table.items())[:3]
        for key, entry in example_items:
            lines.append(f"  {key}: {entry}")
        return "\n".join(lines)


    def clear(self):
        """Tyhjentää transpositiotaulun."""
        self.table.clear()

    def size(self):
        return len(self.table)


# ttable.py
# Lisää loppuun:
ttable = TranspositionTable()
