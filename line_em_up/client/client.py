from ..datatypes import Parameters, PlayPacket, MovePacket, ViewPacket, JoinPacket, JoinResponsePacket, AlgorithmType, WinPacket
from ..datatypes import Config
from .players import Player, HumanPlayer, AIPlayer
from .heuristics import Heuristic1, Heuristic2
from .algorithms import MiniMax, AlphaBeta
from abc import ABC, abstractmethod
from typing import Union
import socketio

class Client(ABC):
    _parameters: Parameters
    _config: Config
    _done: bool
    _player: Player
    _player_index: int

    def __init__(self, config: Config):
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
        if self._config.is_human:
            self._player = HumanPlayer()
        else:
            index = self.player_index
            algorithm_name = self._parameters.algorithm
            heuristic_index = self._parameters.heuristics[index]

            if heuristic_index == 1:
                heuristic = Heuristic1(self._parameters)
            elif heuristic_index == 2:
                heuristic = Heuristic2(self._parameters)
            else:
                raise Exception(f"Unknown heuristic {heuristic_index}.")

            if algorithm_name == AlgorithmType.MINIMAX:
                algorithm = MiniMax(
                    heuristic=heuristic
                )
            elif algorithm_name == AlgorithmType.ALPHABETA:
                algorithm = AlphaBeta(
                    heuristic=heuristic
                )
            else:
                raise Exception(f"Unknown algorithm {algorithm_name}.")
            
            self._player = AIPlayer(
                algorithm=algorithm
            )

    @abstractmethod
    def run(self):
        pass

    def next_move(self, packet: PlayPacket) -> MovePacket:
        return MovePacket(
            player_id=self._config.player_id,
            move=self._player.next_move(packet)
        )

class NetworkClient(Client):
    def __init__(self, config: Config):
        super().__init__(config)

    def run(self):
        sio = socketio.Client()

        def __handle_error(error: str):
            print(error)
            sio.disconnect()

        @sio.event
        def connect():
            packet = ViewPacket(
                game_uuid=self._config.game_uuid
            )

            sio.emit("parameters", {"game_uuid": self._config.game_uuid})

        @sio.event
        def parameters(data):
            if "error" in data:
                return __handle_error(data["error"])

            self._parameters = Parameters.from_dict(data)

            join_packet = JoinPacket(
                player_id=self._config.player_id,
                game_uuid=self._config.game_uuid
            )

            sio.emit("join", join_packet.to_dict())

        @sio.event
        def join(data):
            if "error" in data:
                return __handle_error(data["error"])

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
                return __handle_error(data["error"])

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

        sio.connect(self._config.url)
