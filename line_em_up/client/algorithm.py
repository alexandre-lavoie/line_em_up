from abc import ABC, abstractmethod
from ..common import PlayPacket, Move, Parameters, Board, Tile

class Heuristic(ABC):
    __tile: Tile
    __parameters: Parameters

    def __init__(self, tile: Tile, parameters: Parameters):
        self.__tile = tile
        self.__parameters = parameters

    @abstractmethod
    def get_score(self, data: any) -> float:
        return 0

    @property
    def max_depth(self) -> int:
        return self.__parameters.depth1 if self.__tile == Tile.WHITE else self.__parameters.depth2

    @property
    def block_count(self) -> int:
        return self.__parameters.block_count

    @property
    def max_time(self) -> int:
        return self.__parameters.max_time

    @property
    def line_up_size(self) -> int:
        return self.__parameters.line_up_size

    @property
    def board_size(self) -> int:
        return self.__parameters.board_size

class Algorithm(ABC):
    __heuristic: Heuristic

    def __init__(self, heuristic: Heuristic):
        self.__heuristic = heuristic

    @abstractmethod
    def next_move(self, packet: PlayPacket) -> Move:
        return (0, 0)

    def get_score(self, data: any) -> float:
        return self.__heuristic.get_score(data)

    @property
    def max_depth(self) -> int:
        return self.__heuristic.max_depth

    @property
    def block_count(self) -> int:
        return self.__heuristic.block_count

    @property
    def max_time(self) -> float:
        return self.__heuristic.max_time

    @property
    def line_up_size(self) -> int:
        return self.__heuristic.line_up_size

    @property
    def board_size(self) -> int:
        return self.__heuristic.board_size
