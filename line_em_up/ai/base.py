from ..client.algorithm import Algorithm, Heuristic
from ..common import PlayPacket, Move, Board

# TODO: Implement these classes.

class MiniMax(Algorithm):
    def next_move(self, packet: PlayPacket) -> Move:
        print(packet)
        return (0, 0)

class AlphaBeta(Algorithm):
    def next_move(self, packet: PlayPacket) -> Move:
        print(packet)
        return (0, 0)

class Heuristic1(Heuristic):
    def get_score(self, data: any) -> float:
        return 0

class Heuristic2(Heuristic):
    def get_score(self, data: any) -> float:
        return 0
