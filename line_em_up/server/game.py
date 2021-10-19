from ..datatypes import Parameters, MovePacket, Board, Tile, PlayPacket, M2Exception, tile_to_emoji, Vector2, PlayerType
import random
from typing import List, Union, Tuple, Union
from enum import Enum, auto
import time

class PlayState(Enum):
    NOT_STARTED=auto()
    INVALID_TIME=auto()
    INVALID_PLAYER=auto()
    INVALID_TURN=auto()
    INVALID_MOVE=auto()
    SUCCESS=auto()

class InvalidException(M2Exception):
    pass

class Game:
    _uuid: str
    _parameters: Parameters
    _players: List[str]
    _player_types: List[PlayerType]
    _player_turn: int
    _board: Board
    _winner: str
    _complete: bool
    _time: float

    def __init__(self, uuid: str, parameters: Parameters):
        self._uuid = uuid
        self._parameters = parameters
        self._players = []
        self._player_types = []
        self._player_turn = 0
        self._winner = None
        self._complete = False
        self.__generate_board()
        self._time = None

    def __generate_board(self):
        board_size = self._parameters.board_size

        self._board = [[Tile.EMPTY.value for _ in range(board_size)] for _ in range(board_size)]

        block_indicies = random.sample(list(range(board_size ** 2)), k=self._parameters.block_count)

        for block_index in block_indicies:
            i, j = block_index // board_size, block_index % board_size
            self._board[i][j] = Tile.BLOCK.value

    def __map_value(self, value: str) -> str:
        if value == 0:
            return "&#x2b1c;"
        elif value == 1:
            return "&#x1f3c0;"
        elif value == 2:
            return "&#x1f3b1;"
        elif value == 3:
            return "&#x26d4;"
        else:
            return "&#x2754;"

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def players(self) -> List[str]:
        return self._players

    @property
    def player_types(self) -> List[PlayerType]:
        return self._player_types

    @property
    def players_types(self) -> List[Tuple[str, PlayerType]]:
        return list(zip(self.players, self.player_types))

    @property
    def board(self) -> Board:
        return [[v for v in row] for row in self._board]
    
    @property
    def pretty_board(self) -> Board:
        return [[tile_to_emoji(v) for v in row] for row in self._board]

    @property
    def parameters(self) -> Parameters:
        return self._parameters

    @property
    def winner(self) -> str:
        return self._winner

    def reset_time(self):
        self._time = time.time()

    def join(self, player_id: str, player_type: PlayerType) -> bool:
        if self.all_players(): return False

        self._players.append(player_id)
        self._player_types.append(player_type)

        return True

    def all_players(self) -> bool:
        return len(self._players) == 2

    def get_other_player(self, player_id: str) -> str:
        return self._players[0] if player_id == self._players[1] else self._players[1]

    def __end_game(self, winner: Union[str, None]):
        self._winner = winner
        self._complete = True

        return True

    def play(self, packet: MovePacket):
        play_time = time.time()

        player_id = packet.player_id

        if not player_id in self._players:
            raise M2Exception("Player not in game.")

        if not self.all_players():
            raise M2Exception("Game not started.")

        player_index = self._players.index(player_id)
        player_type = self._player_types[player_index]

        if player_type == PlayerType.AI and play_time - self._time > self._parameters.max_time:
            self.__end_game(self.get_other_player(player_id))
            raise InvalidException("Too slow.")

        if not player_index == self._player_turn:
            raise M2Exception("Not player turn.")

        (x, y) = packet.move

        if not self._board[y][x] == Tile.EMPTY.value:
            if player_type == PlayerType.AI:
                self.__end_game(self.get_other_player(player_id))
                raise InvalidException("Invalid move.")
            elif player_type == PlayerType.HUMAN:
                raise M2Exception("Invalid move.")

        tile = [Tile.WHITE.value, Tile.BLACK.value][player_index]

        self._board[y][x] = tile
        self._player_turn = (self._player_turn + 1) % 2

    def next_packet(self) -> PlayPacket:
        return PlayPacket(
            board=self.board,
            pretty_board=self.pretty_board,
            player_id=self._players[self._player_turn] if not self._complete else None
        )

    def __get_line_indicies(self, start: Vector2, direction: Vector2, length: int) -> Union[List[Vector2], None]:
        points = []
        point = start
        board_size = self._parameters.board_size

        for _ in range(length):
            if point.x < 0 or point.x >= board_size or point.y < 0 or point.y >= board_size:
                return None

            points.append(point)
            point += direction

        return points

    def __get_line_values(self, indicies: List[Vector2]) -> List[int]:
        values = []
        
        for index in indicies:
            values.append(self._board[index.x][index.y])

        return values

    def is_complete(self) -> bool:
        if self._complete:
            return True

        board_size = self._parameters.board_size

        for i in range(board_size):
            for j in range(board_size):
                point = Vector2(i, j)

                for direction in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, -1)]:
                    direction = Vector2(direction[0], direction[1])

                    line = self.__get_line_indicies(point, direction, self._parameters.line_up_size)

                    if not line: continue

                    values = self.__get_line_values(line)

                    if all(value == Tile.WHITE.value for value in values):
                        return self.__end_game(self.players[0])
                    elif all(value == Tile.BLACK.value for value in values):
                        return self.__end_game(self.players[1])

        if not any(any(tile == Tile.EMPTY.value for tile in row) for row in self._board):
            return self.__end_game(None)

        return False
