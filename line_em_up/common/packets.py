from dataclasses import dataclass
from dataclasses_json import dataclass_json
from .types import AlgorithmType, PlayerUUID, GameUUID, PlayerType, Move, Tile, HeuristicType
from typing import List, Tuple, Union, Set, Dict
import itertools
import string

@dataclass
class Parameters:
    board_size: int
    line_up_size: int
    max_time: float
    algorithm: AlgorithmType
    depths: List[int]
    heuristics: List[HeuristicType]
    blocks: List[Tuple[int, int]] = None
    block_count: int = 0
    max_player_count: int = 2
    listed: bool = False

    def __post_init__(self):
        if self.max_player_count < 2 or self.max_player_count > len([tile for tile in Tile if tile.value >= 0]):
            raise TypeError("Invalid player count.")

        if self.board_size < 3:
            raise TypeError("Invalid board size.")

        if self.block_count < 0 or self.block_count > self.board_size * 2:
            raise TypeError("Invalid block count.")

        if self.line_up_size < 0 or self.line_up_size > self.board_size:
            raise TypeError("Invalid line up size.")

        for depth in self.depths:
            if depth < 0:
                raise TypeError("Invalid player depth.")

        if not len(self.depths) == self.max_player_count:
            raise TypeError("Depths count does match player count.") 

        if self.max_time < 0:
            raise TypeError("Invalid max time.")

        if not len(self.heuristics) == self.max_player_count:
            raise TypeError("Heuristic count does match player count.") 

    def to_dict(self):
        d = vars(self)
        nd = {}

        nd['max_player_count'] = d['max_player_count']
        nd['board_size'] = d['board_size']
        nd['line_up_size'] = d['line_up_size']
        nd['max_time'] = d['max_time']
        nd['algorithm'] = d['algorithm'].value
        nd['listed'] = d['listed']
        nd['depths'] = d['depths']
        nd['heuristics'] = [heuristic.value for heuristic in d['heuristics']]
        nd['block_count'] = d['block_count']
        nd['blocks'] = d['blocks']

        return nd

    @classmethod
    def from_dict(cls, d: any):
        nd = {}

        if 'max_player_count' in d:
            nd['max_player_count'] = int(d['max_player_count'])

        nd['board_size'] = int(d['board_size'])
        nd['line_up_size'] = int(d['line_up_size'])
        nd['max_time'] = float(d['max_time'])
        nd['algorithm'] = AlgorithmType(d['algorithm'])
        if 'listed' in d:
            nd['listed'] = d['listed'] == 'on'

        depths = []
        if 'depths' in d:
            depths = [int(depth) for depth in d['depths']]
        else:
            for i in range(1, nd['max_player_count'] + 1):
                tag = f'depth{i}'
                depths.append(int(d[tag]))
        nd['depths'] = depths

        heuristics = []
        if 'heuristics' in d:
            heuristics = [HeuristicType(heuristic) for heuristic in d['heuristics']]
        else:
            for i in range(1, nd['max_player_count'] + 1):
                tag = f'heuristic{i}'
                heuristics.append(HeuristicType(d[tag]))
        nd['heuristics'] = heuristics

        if 'blocks' in d and not d['blocks'] == None:
            if isinstance(d['blocks'], str):
                if len(d['blocks'].strip()) == 0:
                    nd['blocks'] = []
                    nd['block_count'] = 0
                elif d['blocks'].isnumeric():
                    nd['blocks'] = None
                    nd['block_count'] = int(d['blocks'])
                elif '(' in d['blocks']:
                    nd['blocks'] = []
                    for coordinate in d['blocks'].split(')'):
                        if len(coordinate.strip()) == 0:
                            continue

                        inner = coordinate[coordinate.index('(') + 1:]

                        if "," in inner:
                            x, y = inner.split(",")
                        elif " " in inner:
                            x, y = inner.split(" ")

                        if x.isnumeric():
                            x = int(x)
                        elif x in string.ascii_uppercase:
                            x = string.ascii_uppercase.index(x)
                        elif x in string.ascii_lowercase:
                            x = string.ascii_lowercase.index(x)

                        nd['blocks'].append((x, int(y)))
                    nd['block_count'] = len(nd['blocks'])
                else:
                    nd['blocks'] = []
                    for coordinate in d['blocks'].split(','):
                        if len(coordinate.strip()) == 0:
                            continue

                        sc = coordinate.strip().split(" ")

                        if len(sc) == 1:
                            x, y = sc[0]
                        else:
                            x, y = sc

                        if x.isnumeric():
                            x = int(x)
                        elif x in string.ascii_uppercase:
                            x = string.ascii_uppercase.index(x)
                        elif x in string.ascii_lowercase:
                            x = string.ascii_lowercase.index(x)

                        nd['blocks'].append((x, int(y)))
                    nd['block_count'] = len(nd['blocks'])
            elif isinstance(d['blocks'], list):
                nd['blocks'] = [tuple([int(v) for v in block]) for block in d['blocks']]
                nd['block_count'] = len(nd['blocks'])
            else:
                raise Exception("Cannot handle blocks type.")
        else:
            nd['blocks'] = None
            nd['block_count'] = int(d['block_count'])

        return Parameters(**nd)

@dataclass
class PlayPacket:
    tile: Tile
    emoji_board: List[List[str]]
    moves: List[Tuple[int, int, Tile]]
    blocks: List[Tuple[int, int]]
    order: List[Tile]

    def to_dict(self):
        d = vars(self)

        d['tile'] = d['tile'].value
        d['moves'] = [(x, y, tile.value) for x, y, tile in d['moves']]
        d['blocks'] = [(x, y) for x, y in d['blocks']]
        d['order'] = [tile.value for tile in d['order']]

        return d

    @classmethod
    def from_dict(cls, d: any):
        nd = {}

        nd['tile'] = Tile(d['tile'])
        nd['emoji_board'] = d['emoji_board']
        nd['moves'] = [(x, y, Tile(tile)) for x, y, tile in d['moves']]
        nd['blocks'] = [(x, y) for x, y in d['blocks']]
        nd['order'] = [Tile(tile) for tile in d['order']]

        return PlayPacket(**nd)

@dataclass_json
@dataclass
class ErrorPacket:
    error: str

@dataclass_json
@dataclass
class MoveStatistics:
    node_times: List[float]
    depth_counts: List[int]
    average_recursive_depth: float

@dataclass
class MovePacket:
    move: Move
    statistics: MoveStatistics = None

    def to_dict(self):
        d = vars(self)
        nd = {}

        (x, y) = d['move']
        nd['move'] = (x, y)

        if d['statistics']:
            nd['statistics'] = d['statistics'].to_dict()

        return nd

    @classmethod
    def from_dict(cls, d: any):
        nd = {}

        (x, y) = d['move']
        nd['move'] = (x, y)

        if 'statistics' in d:
            nd['statistics'] = MoveStatistics.from_dict(d['statistics'])

        return MovePacket(**nd)

@dataclass_json
@dataclass
class ParametersPacket:
    game_id: GameUUID

@dataclass_json
@dataclass
class WinPacket:
    ranks: Dict[int, int]

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
        nd = {}

        nd['game_id'] = d['game_id']
        nd['player_name'] = d['player_name']
        nd['player_type'] = PlayerType(d['player_type'])

        return JoinPacket(**nd)

@dataclass
class JoinResponsePacket:
    socket_id: str
    player_id: PlayerUUID
    player_name: str
    player_type: PlayerType
    tile: Tile
    tile_emoji: str

    def to_dict(self):
        d = vars(self)
        d['player_type'] = d['player_type'].value
        d['tile'] = d['tile'].value

        return d

    @classmethod
    def from_dict(cls, d: any):
        nd = {}

        nd['socket_id'] = d['socket_id']
        nd['player_id'] = d['player_id']
        nd['player_name'] = d['player_name']
        nd['player_type'] = PlayerType(d['player_type'])
        nd['tile'] = Tile(d['tile'])
        nd['tile_emoji'] = d['tile_emoji']

        return JoinResponsePacket(**nd)

@dataclass_json
@dataclass
class ViewPacket:
    game_id: GameUUID
