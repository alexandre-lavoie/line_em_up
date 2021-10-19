from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import List, Tuple, Union
from enum import Enum

class M2Exception(Exception):
    pass

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

def tile_to_emoji(tile: Union[Tile, int]) -> str:
    if tile == Tile.EMPTY or tile == Tile.EMPTY.value:
        return "&#x2b1c;"
    elif tile == Tile.WHITE or tile == Tile.WHITE.value:
        return "&#x1f3c0;"
    elif tile == Tile.BLACK or tile == Tile.BLACK.value:
        return "&#x1f3b1;"
    elif tile == Tile.BLOCK or tile == Tile.BLOCK.value:
        return "&#x26d4;"
    else:
        return "&#x2754;"

Board = List[List[Tile]]
Move = Tuple[int, int]
GameUUID = str
PlayerID = str

@dataclass_json
@dataclass
class Config:
    url: str
    player_id: PlayerID
    player_type: PlayerType
    game_uuid: GameUUID
    debug: bool

@dataclass_json
@dataclass
class Parameters:
    board_size: int
    block_count: int
    line_up_size: int
    player_depths: Tuple[int, int]
    max_time: float
    algorithm: Union[AlgorithmType]
    heuristics: Tuple[int, int]

@dataclass_json
@dataclass
class PlayPacket:
    player_id: Union[PlayerID, None]
    board: Board
    pretty_board: List[List[str]]

@dataclass_json
@dataclass
class ErrorPacket:
    error: str

@dataclass_json
@dataclass
class MovePacket:
    player_id: PlayerID
    move: Move

@dataclass_json
@dataclass
class ParametersPacket:
    game_uuid: GameUUID

@dataclass_json
@dataclass
class WinPacket:
    player_id: Union[PlayerID, None]

@dataclass_json
@dataclass
class JoinPacket:
    game_uuid: GameUUID
    player_id: PlayerID
    player_type: PlayerType

@dataclass_json
@dataclass
class JoinResponsePacket:
    player_id: PlayerID
    player_index: int
    player_type: PlayerType

@dataclass_json
@dataclass
class ViewPacket:
    game_uuid: GameUUID

class Vector2:
    x: float
    y: float
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __add__(self, other: Union[int, float, "Vector2"]) -> "Vector2":
        if type(other) in [int, float]:
            return Vector2(self.x + other, self.y + other)
        elif type(other) == Vector2:
            return Vector2(self.x + other.x, self.y + other.y)
        else:
            raise TypeError(f"Cannot add {other} to Vector2.")

    def __sub__(self, other: Union[int, float, "Vector2"]) -> "Vector2":
        if type(other) in [int, float]:
            return Vector2(self.x - other, self.y - other)
        elif type(other) == Vector2:
            return Vector2(self.x - other.x, self.y - other.y)
        else:
            raise TypeError(f"Cannot subtract {other} to Vector2.")

    def __mul__(self, other: Union[int, float]) -> "Vector2":
        if type(other) in [int, float]:
            return Vector2(self.x * other, self.y * other)
        else:
            raise TypeError(f"Cannot multiply {other} to Vector2.")
