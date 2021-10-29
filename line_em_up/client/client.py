from ..common import Parameters, PlayPacket, MovePacket, ViewPacket, JoinPacket, JoinResponsePacket, AlgorithmType, WinPacket, PlayerType, Tile, HeuristicType
from .config import ClientConfig
from .players import Player, HumanPlayer, AIPlayer
from ..ai import MiniMax, AlphaBeta, Heuristic1, Heuristic2
from abc import ABC, abstractmethod
from typing import Union
import socketio

class Client(ABC):
    _parameters: Parameters
    _config: ClientConfig
    _done: bool
    _player: Player
    _tile: Tile

    def __init__(self, config: ClientConfig):
        self._config = config
        self._parameters = None
        self._done = False
        self._player = None
        self._tile = Tile.EMPTY

    @property
    def player_index(self) -> int:
        return self._player_index

    @property
    def done(self) -> bool:
        return self._done

    def init_player(self):
        if self._config.player_type == PlayerType.HUMAN:
            self._player = HumanPlayer()
        elif self._config.player_type == PlayerType.AI:
            tile = self._tile
            algorithm_name = self._parameters.algorithm
            heuristic_index = self._parameters.heuristic1 if tile == Tile.WHITE else self._parameters.heuristic2

            heuristic_types = {
                HeuristicType.ONE: Heuristic1, 
                HeuristicType.TWO: Heuristic2
            }
            if heuristic_index in heuristic_types:
                heuristic = heuristic_types[heuristic_index](
                    tile=tile, 
                    parameters=self._parameters
                )
            else:
                raise Exception(f"Unknown heuristic {heuristic_index}.")

            algorithm_types = {
                AlgorithmType.MINIMAX: MiniMax,
                AlgorithmType.ALPHABETA: AlphaBeta
            }
            if algorithm_name in algorithm_types:
                algorithm = algorithm_types[algorithm_name](
                    heuristic=heuristic
                )
            else:
                raise Exception(f"Unknown algorithm {algorithm_name}.")

            self._player = AIPlayer(
                algorithm=algorithm
            )
        else:
            raise Exception("Unimplemented PlayerType.")

    @abstractmethod
    def run(self):
        pass

    def next_move(self, packet: PlayPacket) -> MovePacket:
        return MovePacket(
            move=self._player.next_move(packet)
        )

class NetworkClient(Client):
    def run(self):
        sio = socketio.Client()

        @sio.event
        def connect():
            print("Connected")

            packet = ViewPacket(
                game_id=self._config.game_id
            )

            sio.emit("parameters", packet.to_dict())

        @sio.event
        def parameters(data):
            print("Parameters")

            self._parameters = Parameters.from_dict(data)

            join_packet = JoinPacket(
                player_name=self._config.player_name,
                player_type=self._config.player_type,
                game_id=self._config.game_id
            )

            sio.emit("join", join_packet.to_dict())

        @sio.event
        def join(data):
            packet = JoinResponsePacket.from_dict(data)

            if packet.player_name == self._config.player_name:
                print("I Joined")

                self._tile = packet.tile
                self.init_player()
            else:
                print("Opponent Joined")

        @sio.event
        def play(data):
            packet = PlayPacket.from_dict(data)

            if packet.tile == self._tile:
                print("My Turn")
                sio.emit("play", self.next_move(packet).to_dict())
            else:
                print("Opponent's Turn")

        @sio.event
        def win(data):
            packet = WinPacket.from_dict(data)

            if packet.player_name == None:
                print("Tie")
            elif packet.player_name == self._config.player_name:
                print("I Win")
            else:
                print("I Lose")

            sio.disconnect()

        @sio.event
        def error(data):
            print(data["error"])
            sio.disconnect()

        sio.connect(self._config.url)
