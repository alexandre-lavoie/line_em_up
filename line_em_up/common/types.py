from enum import Enum
from typing import List, Tuple
from dataclasses import dataclass
from dataclasses_json import dataclass_json

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

Board = List[List[Tile]]
Move = Tuple[int, int]
GameUUID = str
PlayerUUID = str
