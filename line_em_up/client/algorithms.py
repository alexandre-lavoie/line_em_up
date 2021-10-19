from abc import ABC, abstractmethod
from ..datatypes import PlayPacket, Move
from .heuristics import Heuristic

class Algorithm(ABC):
    __heuristic: Heuristic

    def __init__(self, heuristic: Heuristic):
        self.__heuristic = heuristic

    @property
    def max_depth(self) -> int:
        return self.__heuristic.parameters.player_depths[self.__heuristic.player_index]

    @property
    def max_time(self) -> float:
        return self.__heuristic.parameters.max_time

    @property
    def line_up_size(self) -> int:
        return self.__heuristic.parameters.line_up_size

    @abstractmethod
    def next_move(self, packet: PlayPacket) -> Move:
        return (0, 0)

class MiniMax(Algorithm):
    def next_move(self, packet: PlayPacket) -> Move:
        # TODO: Implement.
        return (0, 0)

class AlphaBeta(Algorithm):
    def next_move(self, packet: PlayPacket) -> Move:
        # TODO: Implement.
        return (0, 0)
