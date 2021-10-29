from enum import Enum
from typing import List, Tuple
from dataclasses import dataclass
from dataclasses_json import dataclass_json

class AlgorithmType(str, Enum):
    MINIMAX = "minimax"
    ALPHABETA = "alphabeta"

class HeuristicType(str, Enum):
    ONE = 1
    TWO = 2

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

Emojis = {
    "WHITE": "&#x1f7e9;",
    "EMPTY": "&#x2b1c;",
    "BLACK": "&#x1f537;",
    "BLOCK": "&#x26d4;",
    "HUMAN": "&#x1f466;",
    "AI": "&#129302;",
    "TIE": "&#x1f454;",
    "UNKNOWN": "&#x2753;",
    "WIN": "&#x1f451;",
    "LOSE": "&#x1f948;"
}
