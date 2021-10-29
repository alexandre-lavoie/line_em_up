from dataclasses import dataclass
from dataclasses_json import dataclass_json
from .types import AlgorithmType, PlayerUUID, GameUUID, PlayerType, Move, Tile, HeuristicType
from typing import List, Tuple, Union, Set

@dataclass_json
@dataclass
class Parameters:
    board_size: int
    block_count: int
    line_up_size: int
    depth1: int
    depth2: int
    max_time: float
    algorithm: AlgorithmType
    heuristic1: HeuristicType
    heuristic2: HeuristicType
    listed: bool = False

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

        self.depth1 = int(self.depth1)
        if self.depth1 < 0:
            raise TypeError("Invalid player1 depth.")

        self.depth2 = int(self.depth2)
        if self.depth2 < 0:
            raise TypeError("Invalid player2 depth.")

        self.max_time = float(self.max_time)
        if self.max_time < 0:
            raise TypeError("Invalid max time.")

        self.algorithm = AlgorithmType(self.algorithm)
        self.heuristic1 = HeuristicType(self.heuristic1)
        self.heuristic2 = HeuristicType(self.heuristic2)

        self.listed = self.listed == "on"

@dataclass
class PlayPacket:
    tile: Tile
    board: List[List[Tile]]
    emoji_board: List[List[str]]
    moves: List[Tuple[int, int, Tile]]
    blocks: List[Tuple[int, int]]

    def to_dict(self):
        d = vars(self)
        d['tile'] = d['tile'].value
        d['board'] = [[tile.value for tile in row] for row in d['board']]
        d['moves'] = [(x, y, tile.value) for x, y, tile in d['moves']]

        return d

    @classmethod
    def from_dict(cls, d: any):
        d['tile'] = Tile(d['tile'])
        d['board'] = [[Tile(tile) for tile in row] for row in d['board']]
        d['moves'] = [(x, y, Tile(tile)) for x, y, tile in d['moves']]

        return PlayPacket(**d)

@dataclass_json
@dataclass
class ErrorPacket:
    error: str

@dataclass_json
@dataclass
class MovePacket:
    move: Move

@dataclass_json
@dataclass
class ParametersPacket:
    game_id: GameUUID

@dataclass
class WinPacket:
    tile: Tile
    player_id: PlayerUUID
    player_name: str

    def to_dict(self):
        d = vars(self)
        d['tile'] = d['tile'].value

        return d

    @classmethod
    def from_dict(cls, d: any):
        d['tile'] = Tile(d['tile'])

        return WinPacket(**d)

@dataclass
class JoinPacket:
    game_id: GameUUID
    player_name: str
    player_type: PlayerType

    def to_dict(self):
        d = vars(self)
        d['player_type'] = d['player_type'].value

        return d

    @classmethod
    def from_dict(cls, d: any):
        d['player_type'] = PlayerType(d['player_type'])

        return JoinPacket(**d)

@dataclass
class JoinResponsePacket:
    socket_id: str
    player_id: PlayerUUID
    player_name: str
    player_type: PlayerType
    tile: Tile

    def to_dict(self):
        d = vars(self)
        d['player_type'] = d['player_type'].value
        d['tile'] = d['tile'].value

        return d

    @classmethod
    def from_dict(cls, d: any):
        d['player_type'] = PlayerType(d['player_type'])
        d['tile'] = Tile(d['tile'])

        return JoinResponsePacket(**d)

@dataclass_json
@dataclass
class ViewPacket:
    game_id: GameUUID
