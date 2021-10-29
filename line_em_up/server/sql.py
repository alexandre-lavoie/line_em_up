from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, String, Integer, Boolean, DateTime, CheckConstraint, UniqueConstraint, ForeignKey, Enum
from typing import Tuple, List

from ..common.packets import Parameters
from ..common.types import Tile, PlayerType, AlgorithmType, HeuristicType
from ..common.utils import tile_to_emoji, make_line

Base = declarative_base()

class Game(Base):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    sessions = relationship("GameSession", back_populates="game")
    tiles = relationship("GameTile")

    board_size = Column(Integer, nullable=False)
    block_count = Column(Integer, nullable=False)
    line_up_size = Column(Integer, nullable=False)
    depth1 = Column(Integer, nullable=False)
    depth2 = Column(Integer, nullable=False)
    max_time = Column(Integer, nullable=False)
    algorithm = Column(Enum(AlgorithmType), nullable=False)
    heuristic1 = Column(Enum(HeuristicType), nullable=False)
    heuristic2 = Column(Enum(HeuristicType), nullable=False)
    listed = Column(Boolean, default=False)

    last_time = Column(Integer)
    tile_turn = Column(Enum(Tile), default=Tile.WHITE)
    complete = Column("complete", Boolean, default=False)
    tile_winner = Column(Enum(Tile), default=Tile.EMPTY)

    @property
    def parameters(self):
        return Parameters.from_dict(vars(self))

    @property
    def started(self):
        return self.player_count == 2

    @property
    def player_count(self):
        return len(set([session.player.id for session in self.sessions]))

    @property
    def winner(self):
        if self.tile_winner == Tile.EMPTY:
            return None

        for session in self.sessions:
            if session.tile == self.tile_winner:
                return session.player

    def get_player_tile(self, player_id: str) -> Tile:
        for session in self.sessions:
            if session.player.id == player_id:
                return session.tile

        player_count = self.player_count
        if player_count == 0:
            return Tile.WHITE
        elif player_count == 1:
            return Tile.BLACK
        else:
            raise Exception("Cannot get tile type.")

    @property
    def blocks(self):
        return [(tile.x, tile.y) for tile in filter(lambda tile: tile.type == Tile.BLOCK, self.tiles)]

    @property
    def moves(self):
        return [(tile.x, tile.y, tile.type) for tile in filter(lambda tile: not tile.type == Tile.BLOCK and not tile.type == Tile.EMPTY, self.tiles)]

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

    def check_complete(self) -> bool:
        if self.complete: 
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
        if self.tile == Tile.WHITE:
            return self.game.heuristic1
        else:
            return self.game.heuristic2

    @property
    def depth(self) -> int:
        if self.tile == Tile.WHITE:
            return self.game.depth1
        else:
            return self.game.depth2

    @property
    def is_turn(self) -> bool:
        return self.game.tile_turn == self.tile

    @property
    def winner(self) -> bool:
        return self.game.tile_winner == self.tile

    def __repr__(self):
        return f"GameSession(game_id={self.game_id}, player_id={self.player_id}, socket_id={self.socket_id})"

class GameTile(Base):
    __tablename__ = 'tiles'

    id = Column(Integer, primary_key=True)

    game_id = Column(Integer, ForeignKey('games.id'), nullable=False)

    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False) 
    type = Column(Enum(Tile), nullable=False)

    def __repr__(self):
        return f"Tile(x={self.x}, y={self.y}, type={self.type})"

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
            if session.game.winner:
                score += 2 if session.winner else -1
        
        return score

    def __repr__(self):
        return f"Player(id={self.id}, name={self.name}, type={self.type})"
