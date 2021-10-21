from abc import ABC, abstractmethod
from ..common import PlayPacket, Move, Parameters, Board

class Heuristic(ABC):
    _player_index: int
    _parameters: Parameters

    def __init__(self, player_index: int, parameters: Parameters):
        self._player_index = player_index
        self._parameters = parameters

    @property
    def player_index(self) -> int:
        return self._player_index

    @property
    def parameters(self) -> Parameters:
        return self._parameters

    def get_score(self, data: any) -> float:
        return 0

class Algorithm(ABC):
    __heuristic: Heuristic

    def __init__(self, heuristic: Heuristic):
        self.__heuristic = heuristic

    @property
    def player_index(self) -> int:
        return self.__heuristic.player_index

    def get_score(self, data: any) -> float:
        return self.__heuristic.get_score(data)

    @property
    def max_depth(self) -> int:
        return self.__heuristic.parameters.player_depth1 if self.player_index == 0 else self.__heuristic.parameters.player_depth2

    @property
    def max_time(self) -> float:
        return self.__heuristic.parameters.max_time

    @property
    def line_up_size(self) -> int:
        return self.__heuristic.parameters.line_up_size

    @property
    def board_size(self) -> int:
        return self.__heuristic.parameters.board_size

    @abstractmethod
    def next_move(self, packet: PlayPacket) -> Move:
        return (0, 0)
