from ..common import Parameters, MovePacket, Board, Tile, PlayPacket, LEMException, tile_to_emoji, PlayerType, PlayerUUID, GameUUID, make_line
from .player import Player
import random
from typing import List, Union, Tuple, Union, Set
import time
import uuid

class InvalidException(LEMException):
    pass

class Game:
    _uuid: GameUUID
    _parameters: Parameters
    _players: List[Player]
    _player_turn: int
    _tiles: Set[Tuple[int, int, Tile]]
    _moves: List[Tuple[int, int]]
    _blocks: Set[Tuple[int, int]]
    _winner: Union[PlayerUUID, None]
    _complete: bool
    _time: float

    def __init__(self, parameters: Parameters):
        self._uuid = str(uuid.uuid4()).split("-")[0]
        self._parameters = parameters
        self._players = []
        self._player_types = []
        self._player_turn = 0
        self._winner = None
        self._complete = False
        self._time = None
        self._winner = None

        self.__generate_board()

    def __generate_board(self):
        self._tiles = set()
        self._moves = []
        self._blocks = set()

        block_indicies = random.sample(list(range(self.board_size ** 2)), k=self._parameters.block_count)
        for block_index in block_indicies:
            x, y = block_index % self.board_size, block_index // self.board_size
            self._blocks.add((x, y))

    @property
    def board_size(self) -> int:
        return self._parameters.board_size

    @property
    def uuid(self) -> GameUUID:
        return self._uuid

    @property
    def players(self) -> List[Player]:
        return self._players

    @property
    def player_count(self) -> int:
        return len(self.players)

    @property
    def board(self) -> Board:
        board = [[Tile.EMPTY for __ in range(self.board_size)] for _ in range(self.board_size)]

        for x, y, tile in self._tiles:
            board[y][x] = tile

        for x, y in self._blocks:
            board[y][x] = Tile.BLOCK

        return board

    @property
    def pretty_board(self) -> Board:
        return [[tile_to_emoji(v) for v in row] for row in self.board]

    @property
    def parameters(self) -> Parameters:
        return self._parameters

    @property
    def winner(self) -> Union[PlayerUUID, None]:
        return self._winner

    @property
    def is_private(self) -> bool:
        return self._parameters.is_private

    @property
    def is_complete(self) -> bool:
        return self._complete

    @property
    def all_players(self) -> bool:
        return len(self._players) == 2

    def reset_time(self):
        self._time = time.time()

    def join(self, player: Player, player_type: PlayerType) -> bool:
        if self.all_players: 
            return False

        self._players.append(player)
        self._player_types.append(player_type)

        return True

    def get_other_player(self, player: Player) -> str:
        return self._players[0] if player == self._players[1] else self._players[1]

    def __end_game(self, winner: Union[PlayerUUID, None]):
        if winner:
            self._winner = winner.uuid
        self._complete = True

        return True

    def is_invalid_move(self, position: Tuple[int, int]) -> bool:
        return position in self._moves or position in self._blocks

    def __get_player_index(self, player: Player) -> int:
        return self._players.index(player)

    def play(self, packet: MovePacket):
        play_time = time.time()

        player = None
        for iplayer in self._players:
            if iplayer.uuid == packet.player_uuid:
                player = iplayer
                break
        else:
            raise LEMException("Player not in game")

        if not self.all_players:
            raise LEMException("Game not started")

        if player.type == PlayerType.AI and play_time - self._time > self._parameters.max_time:
            self.__end_game(self.get_other_player(player=player))
            raise InvalidException("Too slow")

        player_index = self.__get_player_index(player)

        if not player_index == self._player_turn:
            raise LEMException("Not player turn")

        (x, y) = packet.move

        if self.is_invalid_move((x, y)):
            if player.type == PlayerType.AI:
                self.__end_game(self.get_other_player(player=player))
                raise InvalidException("Invalid move")
            elif player.type == PlayerType.HUMAN:
                raise LEMException("Invalid move")

        self._moves.append((x, y))
        self._tiles.add((x, y, Tile.WHITE if player_index == 0 else Tile.BLACK))
        self._player_turn = (self._player_turn + 1) % len(self._players)

    def next_packet(self) -> PlayPacket:
        return PlayPacket(
            board=[[tile.value for tile in row] for row in self.board],
            emoji_board=self.pretty_board,
            player_uuid=self._players[self._player_turn].uuid if not self._complete else None,
            moves=self._moves,
            tiles=list((x, y, tile.value) for x, y, tile in self._tiles),
            blocks=list(self._blocks)
        )

    def check_complete(self) -> bool:
        if self._complete:
            return True

        for x, y, tile in self._tiles:
            for direction in [(1, 0), (1, 1), (0, 1), (1, -1)]:
                line = make_line(
                    point=(x, y), 
                    direction=direction, 
                    length=self._parameters.line_up_size,
                    board_size=self.board_size
                )

                if not line: continue

                if all((lx, ly, tile) in self._tiles for lx, ly in line):
                    player_index = 0 if tile == Tile.WHITE else 1
                    return self.__end_game(winner=self.players[player_index])

        if len(self._moves) + len(self._blocks) == self.board_size ** 2:
            return self.__end_game(winner=None)

        return False
