from ..common.sql import Game
from ..common import PlayerType, AlgorithmType, Tile, HeuristicType
from .config import LogConfig

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import string
import itertools
import os.path

def board_str(tiles, blocks, size):
    board = [["." for _ in range(size)] for __ in range(size)]

    for x, y, tile in tiles:
        board[y][x] = str(tile.value)

    for x, y in blocks:
        board[y][x] = "*"

    board_lines = []

    board_lines.append(" " * 2 + string.ascii_uppercase[:size])
    board_lines.append(" " * 1 + "+" + "-" * size)
    for letter, row in zip(string.ascii_lowercase, board):
        board_lines.append(letter + '|' + ''.join(row))

    return '\n'.join(board_lines)

def make_game_traces(db_session: any, log_dir: str):
    games = [game for game in db_session.query(Game).all() if game.complete]

    for game in games:
        log = []

        log.append(f"id={game.id}")
        log.append(f"n={game.board_size} b={game.block_count} s={game.line_up_size} t={game.max_time}")
        log.append(f"blocks={game.blocks}")
        log.append("")
        for session in game.unique_sessions:
            if session.player_type == PlayerType.HUMAN:
                log.append(f"Player {session.player.name} ({session.tile.value}): {session.player_type.name}")
            else:
                log.append(f"Player {session.player.name} ({session.tile.value}): {session.player_type.name} d={session.depth} a={session.algorithm == AlgorithmType.ALPHABETA} e{session.heuristic}")
        log.append("")
        log.append(board_str(
            tiles=[],
            blocks=game.blocks,
            size=game.board_size
        ))
        log.append("")
        for i, move in enumerate(game.move_tiles):
            log.append(f"Player {move.type.value} plays: {string.ascii_uppercase[move.x]}{string.ascii_lowercase[move.y]} (move #{i + 1})")
            if move.statistics:
                log.append("")
                statistics = move.statistics[0]
                log.append(f"i   Evaluation time: {statistics.average_time}s")
                log.append(f"ii  Heuristic evaluations: {sum(statistics.depth_counts)}")
                log.append(f"iii Evaluations by depth: {statistics.depth_counts}")
                log.append(f"iv  Average evaluation depth: {statistics.average_depth}")
                log.append(f"v   Average recursion depth: {statistics.average_recursive_depth}")
            log.append("")
            moves = game.moves[:i + 1]
            log.append(board_str(
                tiles=moves,
                blocks=game.blocks,
                size=game.board_size
            ))
            log.append("")

        if game.tile_winner == Tile.EMPTY:
            log.append("Tie!") 
        else:
            log.append(f"The winner is {game.tile_winner.value}!")

        all_statistics = [move.statistics[0] for move in game.move_tiles if move.statistics]

        if len(all_statistics) > 0:
            log.append("")
            log.append(f"6(b)i   Average evaluation time: {sum(statistics.average_time for statistics in all_statistics) / len(all_statistics)}s")
            log.append(f"6(b)ii  Total heuristic evaluations: {sum(sum(statistics.depth_counts) for statistics in all_statistics)}")
            log.append(f"6(b)iii Evaluations by depths: {[sum(dv) for dv in itertools.zip_longest(*[statistics.depth_counts for statistics in all_statistics], fillvalue=0)]}")
            log.append(f"6(b)iv  Average evaluation depth: {sum(statistics.average_depth for statistics in all_statistics) / len(all_statistics)}")
            log.append(f"6(b)v   Average recursion depth: {sum(statistics.average_recursive_depth for statistics in all_statistics) / len(all_statistics)}")
            log.append(f"6(b)vi  Total moves: {len(game.moves)}")

        with open(os.path.join(log_dir, f"gameTrace-{game.board_size}-{game.block_count}-{game.line_up_size}-{game.max_time}.{game.id}.txt"), "w") as h:
            h.write('\n'.join(log))

    db_session.close()

def make_scoreboard(db_session: any, log_dir: str):
    games = [game for game in db_session.query(Game).all() if game.complete]

    log = []

    log.append(f"n={games[0].board_size} b={games[0].block_count} s={games[0].line_up_size} t={games[0].max_time}")
    log.append("")

    for session in games[0].unique_sessions:
        log.append(f"Player {session.player.name}: d={session.depth} a={session.algorithm == AlgorithmType.ALPHABETA} e{session.heuristic}")

    log.append("")
    log.append(f"{len(games)} games")
    log.append("")

    for heuristic in HeuristicType:
        win_count = sum(len([session for session in game.unique_sessions if session.win and session.heuristic == heuristic]) for game in games)
        log.append(f"Total wins for heuristic e{heuristic.value}: {win_count} ({(win_count / len(games)) * 100}%)")

    log.append("")

    average_times = 0
    evaluation_count = 0
    depth_counts = []
    average_depth = 0
    average_recursive_depth = 0
    average_moves = 0

    stats_count = 0
    for game in games:
        all_statistics = [move.statistics[0] for move in game.move_tiles if move.statistics]

        if len(all_statistics) == 0:
            continue

        stats_count += 1
        average_times += sum(statistics.average_time for statistics in all_statistics) / len(all_statistics)
        evaluation_count += sum(sum(statistics.depth_counts) for statistics in all_statistics)
        game_depth_counts = [sum(dv) for dv in itertools.zip_longest(*[statistics.depth_counts for statistics in all_statistics], fillvalue=0)]
        depth_counts = [sum(dv) for dv in itertools.zip_longest(depth_counts, game_depth_counts, fillvalue=0)]
        average_depth += sum(statistics.average_depth for statistics in all_statistics) / len(all_statistics)
        average_recursive_depth += sum(statistics.average_recursive_depth for statistics in all_statistics) / len(all_statistics)
        average_moves += len(game.moves)

    average_times /= stats_count
    average_depth /= stats_count
    average_recursive_depth /= stats_count
    average_moves /= stats_count

    log.append(f"i   Average evaluation time: {average_times}s")
    log.append(f"ii  Total heuristic evaluations: {evaluation_count}")
    log.append(f"iii Evaluations by depth: {depth_counts}")
    log.append(f"iv  Average evaluation depth: {average_depth}")
    log.append(f"v   Average recursion depth: {average_recursive_depth}")
    log.append(f"vi  Average moves per game: {average_moves}")

    with open(os.path.join(log_dir, f"scoreboard.txt"), "w") as h:
        h.write('\n'.join(log))

    db_session.close()

def log_main(config: LogConfig):
    engine = create_engine(
        f'sqlite:///{config.db}'
    )
    SessionMaker = sessionmaker(bind=engine)

    make_game_traces(
        db_session=SessionMaker(),
        log_dir="./logs/"
    )

    make_scoreboard(
        db_session=SessionMaker(),
        log_dir="./logs/"
    )
