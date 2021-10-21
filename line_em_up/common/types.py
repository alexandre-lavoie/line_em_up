from enum import Enum
from typing import List, Tuple

class AlgorithmType(str, Enum):
    MINIMAX = "minimax"
    ALPHABETA = "alphabeta"

class PlayerType(str, Enum):
    HUMAN = "human"
    AI = "ai"

class Tile(Enum):
    EMPTY = 0
    WHITE = 1
    BLACK = 2
    BLOCK = 3

def tile_to_emoji(tile: Tile) -> str:
    if tile == Tile.EMPTY:
        return "&#x2b1c;"
    elif tile == Tile.WHITE:
        return "&#x1f3c0;"
    elif tile == Tile.BLACK:
        return "&#x1f3b1;"
    elif tile == Tile.BLOCK:
        return "&#x26d4;"
    else:
        return "&#x2754;"

Board = List[List[Tile]]
Move = Tuple[int, int]
GameUUID = str
PlayerID = str
