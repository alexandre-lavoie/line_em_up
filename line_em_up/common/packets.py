from dataclasses import dataclass
from dataclasses_json import dataclass_json
from .types import AlgorithmType, PlayerUUID, GameUUID, PlayerType, Board, Move, Tile
from typing import List, Tuple, Union, Set

@dataclass_json
@dataclass
class Parameters:
    board_size: int
    block_count: int
    line_up_size: int
    player_depth1: int
    player_depth2: int
    max_time: float
    algorithm: AlgorithmType
    heuristic1: int
    heuristic2: int
    is_private: bool = False

    def __post_init__(self):
        self.board_size = int(self.board_size)
        if self.board_size < 3 or self.board_size > 10:
            raise TypeError("Invalid board size.")

        self.block_count = int(self.block_count)
        if self.block_count < 0 or self.block_count > self.board_size * 2:
            raise TypeError("Invalid block count.")

        self.line_up_size = int(self.line_up_size)
        if self.line_up_size < 0 or self.line_up_size > self.board_size:
            raise TypeError("Invalid line up size.")

        self.player_depth1 = int(self.player_depth1)
        if self.player_depth1 < 0:
            raise TypeError("Invalid player1 depth.")

        self.player_depth2 = int(self.player_depth2)
        if self.player_depth2 < 0:
            raise TypeError("Invalid player2 depth.")

        self.max_time = float(self.max_time)
        if self.max_time < 0:
            raise TypeError("Invalid max time.")

        self.heuristic1 = int(self.heuristic1)
        if not self.heuristic1 in [1, 2]:
            raise TypeError("Invalid heuristic1.")

        self.heuristic2 = int(self.heuristic2)
        if not self.heuristic2 in [1, 2]:
            raise TypeError("Invalid heuristic2.")

        self.is_private = self.is_private == "on"

@dataclass_json
@dataclass
class PlayPacket:
    player_uuid: Union[PlayerUUID, None]
    board: Board
    emoji_board: List[List[str]]
    moves: List[Tuple[int, int]]
    tiles: Set[Tuple[int, int, Tile]]
    blocks: Set[Tuple[int, int]]

@dataclass_json
@dataclass
class ErrorPacket:
    error: str

@dataclass_json
@dataclass
class MovePacket:
    player_uuid: PlayerUUID
    move: Move

@dataclass_json
@dataclass
class ParametersPacket:
    game_uuid: GameUUID

@dataclass_json
@dataclass
class WinPacket:
    player_uuid: Union[PlayerUUID, None]

@dataclass_json
@dataclass
class JoinPacket:
    game_uuid: GameUUID
    player_uuid: PlayerUUID
    player_type: PlayerType

@dataclass_json
@dataclass
class JoinResponsePacket:
    player_uuid: PlayerUUID
    player_index: int
    player_type: PlayerType

@dataclass_json
@dataclass
class ViewPacket:
    game_uuid: GameUUID
