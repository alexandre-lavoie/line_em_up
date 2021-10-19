from abc import ABC
from ..datatypes import Board, Parameters

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
