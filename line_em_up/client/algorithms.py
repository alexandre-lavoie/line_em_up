from abc import ABC, abstractmethod
from ..datatypes import PlayPacket, Move
from .heuristics import Heuristic

class Algorithm(ABC):
    @abstractmethod
    def next_move(self, packet: PlayPacket) -> Move:
        return (0, 0)

class MiniMax(Algorithm):
    __heuristic: Heuristic

    def __init__(self, heuristic: Heuristic):
        self.__heuristic = heuristic

    def next_move(self, packet: PlayPacket) -> Move:
        # TODO: Implement.
        return (0, 0)

class AlphaBeta(Algorithm):
    __heuristic: Heuristic

    def __init__(self, heuristic: Heuristic):
        self.__heuristic = heuristic

    def next_move(self, packet: PlayPacket) -> Move:
        # TODO: Implement.
        return (0, 0)
