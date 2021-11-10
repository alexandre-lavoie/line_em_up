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
    _done: bool
    _id: int

    def __init__(self, config: ClientConfig):
        self._config = config
        self._parameters = None
        self._done = False
        self._player = None
        self._tile = Tile.EMPTY
        self._id = 0

    @property
    def done(self) -> bool:
        return self._done

    def init_player(self):
        if self._config.player_type == PlayerType.HUMAN:
            self._player = HumanPlayer()
        elif self._config.player_type == PlayerType.AI:
            heuristic_types = {
                HeuristicType.ONE: Heuristic1,
                HeuristicType.TWO: Heuristic2
            }
            if self._parameters.heuristics[self._tile.value] in heuristic_types:
                heuristic = heuristic_types[self._parameters.heuristics[self._tile.value]](
                    tile=self._tile,
                    parameters=self._parameters
                )
            else:
                raise Exception(f"Unknown heuristic.")

            algorithm_types = {
                AlgorithmType.MINIMAX: MiniMax,
                AlgorithmType.ALPHABETA: AlphaBeta
            }
            if self._parameters.algorithm in algorithm_types:
                algorithm = algorithm_types[self._parameters.algorithm](
                    heuristic=heuristic
                )
            else:
                raise Exception(f"Unknown algorithm.")

            self._player = AIPlayer(
                algorithm=algorithm
            )
        else:
            raise Exception("Unimplemented PlayerType.")

    @property
    def done(self):
        return self._done

    @abstractmethod
    def run(self):
        pass

    def next_move(self, packet: PlayPacket) -> MovePacket:
        return self._player.next_move(packet)

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

                self._id = packet.player_id
                self._tile = packet.tile
                self.init_player()
            else:
                print("Opponent Joined")

        @sio.event
        def play(data):
            packet = PlayPacket.from_dict(data)

            if packet.tile == self._tile:
                print("My Turn")
                next_packet = self.next_move(packet)
                sio.emit("play", next_packet.to_dict())
            else:
                print("Opponent's Turn")

        @sio.event
        def win(data):
            packet = WinPacket.from_dict(data)

            print(f"I Ranked {packet.ranks[self._id]}")

            self._done = True
            sio.disconnect()

        @sio.event
        def error(data):
            print(data["error"])
            self._done = True
            sio.disconnect()

        sio.connect(self._config.url)
