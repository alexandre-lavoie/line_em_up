from ..client.algorithm import Algorithm, Heuristic
from ..common import PlayPacket, MovePacket, MoveStatistics
import random

# TODO: Implement these classes.

class MiniMax(Algorithm):
    def next_move(self, packet: PlayPacket) -> MovePacket:
        print(packet)
        return MovePacket(
            move=(random.randint(0, self.board_size - 1), random.randint(0, self.board_size - 1)),
            statistics=MoveStatistics(
                node_times=[0.1] * 3,
                depth_counts=[1] * self.max_depth,
                average_recursive_depth=1
            )
        )

class AlphaBeta(Algorithm):
    def next_move(self, packet: PlayPacket) -> MovePacket:
        print(packet)
        return MovePacket(
            move=(random.randint(0, self.board_size - 1), random.randint(0, self.board_size - 1)),
            statistics=MoveStatistics(
                node_times=[0.1] * 3,
                depth_counts=[1] * self.max_depth,
                average_recursive_depth=1
            )
        )

class Heuristic1(Heuristic):
    def get_score(self, data: any) -> float:
        return 0

class Heuristic2(Heuristic):
    def get_score(self, data: any) -> float:
        return 0
