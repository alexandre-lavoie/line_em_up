from .algorithm import Algorithm
from typing import Tuple, List
from abc import ABC, abstractmethod
from ..common import PlayPacket, MovePacket

class Player(ABC):
    @abstractmethod
    def next_move(self, packet: PlayPacket) -> MovePacket:
        return MovePacket(
            move=(0, 0)
        )

class AIPlayer(Player):
    __algorithm: Algorithm
    
    def __init__(self, algorithm: Algorithm):
        self.__algorithm = algorithm

    def next_move(self, packet: PlayPacket) -> MovePacket:
        return self.__algorithm.next_move(packet)

class HumanPlayer(Player):
    def next_move(self, packet: PlayPacket) -> MovePacket:
        try:
            move = input("Next Move (x y): ")
            x, y = [int(x) for x in move.split()]
        except:
            return self.next_move(packet)

        return MovePacket(
            move=(x, y)
        )
