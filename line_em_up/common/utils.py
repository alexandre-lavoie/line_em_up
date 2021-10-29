from .types import Tile, Emojis
from typing import Tuple, Union, List

def tile_to_emoji(tile: Tile) -> str:
    if tile == Tile.EMPTY:
        return Emojis["EMPTY"]
    elif tile == Tile.WHITE:
        return Emojis["WHITE"]
    elif tile == Tile.BLACK:
        return Emojis["BLACK"]
    elif tile == Tile.BLOCK:
        return Emojis["BLOCK"]
    else:
        return Emojis["UNKNOWN"]

def make_line(point: Tuple[int, int], direction: Tuple[int, int], length: int, board_size: int) -> Union[List[Tuple[int, int]], None]:
    points = []

    for _ in range(length):
        for v in point:
            if v < 0 or v >= board_size:
                return None

        points.append(point)
        point = tuple([p + d for p, d in zip(point, direction)])

    return points
