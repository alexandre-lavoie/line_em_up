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
    EMPTY = -2
    BLOCK = -1
    P1 = 0
    P2 = 1
    P3 = 2
    P4 = 3

Board = List[List[Tile]]
Move = Tuple[int, int]
GameUUID = str
PlayerUUID = str

Emojis = {
    "P1": "&#x1f7e9;",
    "P2": "&#x1f537;",
    "P3": "&#x2b50;",
    "P4": "&#x1f49c;",
    "EMPTY": "&#x2b1c;",
    "BLOCK": "&#x26d4;",
    "HUMAN": "&#x1f466;",
    "AI": "&#129302;",
    "TIE": "&#x1f454;",
    "UNKNOWN": "&#x2753;",
    "WIN": "&#x1f451;",
    "LOSE": "&#x1f948;"
}
