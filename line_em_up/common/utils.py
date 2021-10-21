from .types import Tile
from typing import Tuple, Union, List

def tile_to_emoji(tile: Tile) -> str:
    if tile == Tile.EMPTY:
        return "&#x2b1c;"
    elif tile == Tile.WHITE:
        return "&#x1f3c0;"
    elif tile == Tile.BLACK:
        return "&#x1f3b1;"
    elif tile == Tile.BLOCK:
        return "&#x26d4;"
    else:
        return "&#x2754;"

def make_line(point: Tuple[int, int], direction: Tuple[int, int], length: int, board_size: int) -> Union[List[Tuple[int, int]], None]:
    points = []

    for _ in range(length):
        for v in point:
            if v < 0 or v >= board_size:
                return None

        points.append(point)
        point = tuple([p + d for p, d in zip(point, direction)])

    print(points)

    return points
