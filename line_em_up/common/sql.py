from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, String, Integer, Boolean, DateTime, CheckConstraint, UniqueConstraint, ForeignKey, Enum, Float
from typing import Tuple, List, Dict

from .packets import Parameters, MoveStatistics
from .types import Tile, PlayerType, AlgorithmType, HeuristicType
from .utils import tile_to_emoji, make_line

Base = declarative_base()

class Game(Base):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    sessions = relationship("GameSession", back_populates="game")
    tiles = relationship("GameTile")

    max_player_count = Column(Integer, nullable=False)
    board_size = Column(Integer, nullable=False)
    line_up_size = Column(Integer, nullable=False)
    _depths = Column("depths", String, nullable=False)
    max_time = Column(Integer, nullable=False)
    algorithm = Column(Enum(AlgorithmType), nullable=False)
    _heuristics = Column("heuristics", String, nullable=False)
    listed = Column(Boolean, default=False)

    last_time = Column(Integer)
    tile_turn = Column(Enum(Tile), default=Tile.P1)
    complete = Column("complete", Boolean, default=False)
    tile_winner = Column("winner", Enum(Tile), default=Tile.EMPTY)
    _tile_losers = Column("losers", String, default="")

    @property
    def player_tiles(self) -> List[Tile]:
        return [tile for tile in Tile if tile.value >= 0 and tile.value < self.max_player_count]

    @property
    def tile_losers(self) -> List[Tile]:
        tiles = self._tile_losers.split(',')

        if len(tiles) == 1 and tiles[0].strip() == "": return []

        tiles = [int(tile) for tile in tiles]

        return [Tile(tile) for tile in tiles]

    @tile_losers.setter
    def _set_tile_losers(self, losers: List[Tile]):
        self._tile_losers = ','.join(str(tile.value) for tile in losers)

    def add_loser(self, tile: Tile):
        if tile in self.tile_losers: return
        self._set_tile_losers = [tile] + self.tile_losers

    @property
    def depths(self) -> List[int]:
        return [int(depth) for depth in self._depths.split(',')]

    @depths.setter
    def depths(self, depths: List[int]):
        self._depths = ','.join(str(depth) for depth in depths)

    @property
    def heuristics(self) -> List[HeuristicType]:
        return [HeuristicType(heuristic) for heuristic in self._heuristics.split(',')]

    @heuristics.setter
    def heuristics(self, heuristics: List[HeuristicType]):
        strings = []

        for heuristic in heuristics:
            if isinstance(heuristic, str):
                strings.append(HeuristicType(heuristic).value)
            else:
                strings.append(heuristic.value)

        self._heuristics = ','.join(strings)

    @property
    def parameters(self):
        d = dict(vars(self))

        d['blocks'] = self.blocks
        d['block_count'] = self.block_count
        d['depths'] = self.depths
        d['heuristics'] = self.heuristics

        return Parameters.from_dict(d)

    @property
    def started(self):
        return self.player_count >= self.max_player_count

    @property
    def ranks(self) -> Dict[int, int]:
        ranks = {}

        for session in self.sessions:
            if not session.player.id in ranks:
                ranks[session.player.id] = session.rank

        return ranks

    @property
    def player_count(self):
        return len(set([session.player.id for session in self.sessions]))

    def get_player_tile(self, player_id: str) -> Tile:
        for session in self.sessions:
            if session.player.id == player_id:
                return session.tile

        return Tile(self.player_count)

    @property
    def blocks(self):
        return [(tile.x, tile.y) for tile in filter(lambda tile: tile.type == Tile.BLOCK, self.tiles)]

    @property
    def block_count(self) -> int:
        return len(self.blocks)

    @property
    def move_tiles(self):
        return list(filter(lambda tile: not tile.type in [Tile.BLOCK, Tile.EMPTY], self.tiles))

    @property
    def moves(self):
        return [(tile.x, tile.y, tile.type) for tile in self.move_tiles]

    @property
    def tile_board(self) -> List[List[Tile]]:
        board = [[Tile.EMPTY for __ in range(self.board_size)] for _ in range(self.board_size)]

        for tile in self.tiles:
            board[tile.y][tile.x] = tile.type

        return board

    @property
    def int_board(self) -> List[List[int]]:
        return [[type.value for type in row] for row in self.tile_board]

    @property
    def pretty_board(self) -> List[List[str]]:
        return [[tile_to_emoji(v) for v in row] for row in self.tile_board]

    @property
    def tile_order(self) -> List[Tile]:
        tiles = self.player_tiles

        for tile in self.tile_losers:
            tiles.remove(tile)

        return tiles

    @property
    def next_tile(self) -> Tile:
        tiles = self.player_tiles
        i = tiles.index(self.tile_turn)

        while True:
            i = (i + 1) % len(tiles)
            tile = tiles[i]

            if not tile in self.tile_losers:
                return tile

    def check_complete(self) -> bool:
        if self.complete: 
            return True

        if len(self.tile_losers) >= self.max_player_count - 1:
            for tile in self.player_tiles:
                if not tile in self.tile_losers:
                    self.tile_winner = tile
                    break
            return True 

        for tile in self.tiles:
            for direction in [(1, 0), (1, 1), (0, 1), (1, -1)]:
                line = make_line(
                    point=(tile.x, tile.y), 
                    direction=direction, 
                    length=self.line_up_size,
                    board_size=self.board_size
                )

                if not line: 
                    continue

                if all(any(lx == t.x and ly == t.y and t.type == tile.type for t in self.tiles) for lx, ly in line):
                    self.tile_winner = tile.type
                    return True

        if len(self.tiles) == self.board_size ** 2:
            return True

        return False

    @property
    def unique_sessions(self):
        seen_ids = set()
        sessions = []

        for session in self.sessions:
            if not session.player.id in seen_ids:
                seen_ids.add(session.player.id)
                sessions.append(session)

        return sessions

    def __repr__(self):
        return f"Game(id={self.id}, board_size={self.board_size}, started={self.started}, turn={self.tile_turn}, complete={self.complete}, listed={self.listed})"

class GameSession(Base):
    __tablename__ = 'sessions'
    __table_args__ = (
        UniqueConstraint('game_id', 'player_id', 'socket_id', name='_game_session_uc'),
    )

    id = Column(Integer, primary_key=True)

    game_id = Column(Integer, ForeignKey('games.id'), nullable=False)
    game = relationship("Game")

    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    player_type = Column(Enum(PlayerType), nullable=False)
    player = relationship("Player")

    socket_id = Column(String, nullable=False)

    tile = Column(Enum(Tile), default=Tile.BLOCK)

    @property
    def algorithm(self) -> AlgorithmType:
        return self.game.algorithm

    @property
    def heuristic(self) -> HeuristicType:
        return self.game.heuristics[self.tile.value]

    @property
    def depth(self) -> int:
        return self.game.depths[self.tile.value]

    @property
    def is_turn(self) -> bool:
        return self.game.tile_turn == self.tile

    @property
    def win(self) -> bool:
        return self.game.tile_winner == self.tile

    @property
    def tie(self) -> bool:
        return self.game.complete and self.game.tile_winner == Tile.EMPTY and not self.tile in self.game.tile_losers

    @property
    def rank(self) -> int:
        if not self.game.complete:
            return 0

        if not self.game.tile_winner == Tile.EMPTY:
            if self.tile == self.game.tile_winner:
                return 1

            if self.game.max_player_count == 2:
                return 2
            
            for i, tile in enumerate(self.game.tile_losers, 3):
                if tile == self.tile:
                    return i

            return 2
        else:
            for i, tile in enumerate(self.game.tile_losers, 2):
                if tile == self.tile:
                    return i

            return 1

    def __repr__(self):
        return f"GameSession(game_id={self.game_id}, player_id={self.player_id}, socket_id={self.socket_id})"

class GameTile(Base):
    __tablename__ = 'tiles'

    id = Column(Integer, primary_key=True)

    game_id = Column(Integer, ForeignKey('games.id'), nullable=False)
    statistics = relationship("Statistics")

    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False) 
    type = Column(Enum(Tile), nullable=False)

    def __repr__(self):
        return f"Tile(x={self.x}, y={self.y}, type={self.type})"

class Statistics(Base):
    __tablename__ = 'statistics'

    id = Column(Integer, primary_key=True)

    tile_id = Column(Integer, ForeignKey('tiles.id'), nullable=False)

    _node_times = Column("node_times", String, nullable=False)
    _depth_counts = Column("depth_counts", String, nullable=False)
    average_recursive_depth = Column(Float, nullable=False)

    @property
    def node_count(self) -> int:
        return len(self.node_times)

    @property
    def node_times(self) -> List[int]:
        if self._node_times.strip() == "":
            return []

        return [float(time) for time in self._node_times.split(",")]

    @node_times.setter
    def node_times(self, times: List[int]):
        self._node_times = ','.join(str(time) for time in times)

    @property
    def depth_counts(self) -> List[int]:
        if self._depth_counts.strip() == "":
            return []

        return [int(count) for count in self._depth_counts.split(",")]

    @depth_counts.setter
    def depth_counts(self, counts: List[int]):
        self._depth_counts = ','.join(str(count) for count in counts)

    @property
    def average_time(self) -> float:
        if len(self.node_times) == 0:
            return 0

        return sum(self.node_times) / len(self.node_times)

    @property
    def average_depth(self) -> float:
        if sum(self.depth_counts) == 0: 
            return 0

        return sum(depth * count for depth, count in enumerate(self.depth_counts, 1)) / sum(self.depth_counts)

    def __repr__(self):
        return f"Statistics(tile={self.tile_id})"

class Player(Base):
    __tablename__ = 'players'
    __table_args__ = (
        UniqueConstraint('name', name='_name_uc'),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    sessions = relationship("GameSession", back_populates="player")

    @property
    def unique_sessions(self):
        seen_ids = set()
        sessions = []

        for session in self.sessions:
            if not session.game.id in seen_ids:
                seen_ids.add(session.game.id)
                sessions.append(session)

        return sessions

    @property
    def score(self) -> int:
        score = 0

        for session in self.unique_sessions:
            if session.game.complete:
                if session.game.tile_winner == Tile.EMPTY:
                    score += 0 if session.rank == 1 else -1
                else:
                    score += 2 if session.rank == 1 else -1
        
        return score

    def __repr__(self):
        return f"Player(id={self.id}, name={self.name}, type={self.type})"
