from abc import ABC
from ..datatypes import Board, Parameters

class Heuristic(ABC):
    _parameters: Parameters

    def __init__(self, parameters: Parameters):
        self._parameters = parameters

    def get_score(self, board: Board) -> float:
        return 0

class Heuristic1(Heuristic):
    def get_score(self, board: Board) -> float:
        # TODO: Implement.
        return 0

class Heuristic2(Heuristic):
    def get_score(self, board: Board) -> float:
        # TODO: Implement.
        return 0
