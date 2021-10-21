from ..common import Parameters, PlayPacket, MovePacket, ViewPacket, JoinPacket, JoinResponsePacket, AlgorithmType, WinPacket, PlayerType
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
    _player_index: int

    def __init__(self, config: ClientConfig):
        self._config = config
        self._parameters = None
        self._done = False
        self._player = None
        self._player_index = None

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
            index = self.player_index
            algorithm_name = self._parameters.algorithm
            heuristic_index = self._parameters.heuristic1 if index == 0 else self._parameters.heuristic2

            heuristic_types = {
                1: Heuristic1, 
                2: Heuristic2
            }
            if heuristic_index in heuristic_types:
                heuristic = heuristic_types[heuristic_index](
                    player_index=index, 
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
            player_id=self._config.player_id,
            move=self._player.next_move(packet)
        )

class NetworkClient(Client):
    def run(self):
        sio = socketio.Client()

        @sio.event
        def connect():
            packet = ViewPacket(
                game_uuid=self._config.game_uuid
            )

            sio.emit("parameters", {"game_uuid": self._config.game_uuid})

        @sio.event
        def parameters(data):
            if "error" in data:
                return self.__handle_error(data["error"])

            self._parameters = Parameters.from_dict(data)

            join_packet = JoinPacket(
                player_id=self._config.player_id,
                player_type=self._config.player_type,
                game_uuid=self._config.game_uuid
            )

            sio.emit("join", join_packet.to_dict())

        @sio.event
        def join(data):
            if "error" in data:
                return self.__handle_error(data["error"])

            packet = JoinResponsePacket.from_dict(data)

            if packet.player_id == self._config.player_id:
                print("I Joined")

                self._player_index = packet.player_index
                self.init_player()
            else:
                print("Opponent Joined")

        @sio.event
        def play(data):
            if "error" in data:
                return self.__handle_error(data["error"])

            packet = PlayPacket.from_dict(data)

            if packet.player_id == self._config.player_id:
                print("My Turn")
                sio.emit("play", self.next_move(packet).to_dict())
            else:
                print("Opponent's Turn")

        @sio.event
        def win(data):
            packet = WinPacket.from_dict(data)

            if packet.player_id == None:
                print("Tie")
            elif packet.player_id == self._config.player_id:
                print("I Win")
            else:
                print("I Lose")

            sio.disconnect()

        @sio.event
        def error(data):
            print(data["error"])
            sio.disconnect()

        sio.connect(self._config.url)
