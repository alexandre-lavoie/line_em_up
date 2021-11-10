import requests
import time
import threading
import multiprocessing
import os.path
import logging

from line_em_up.server.config import ServerConfig

from .config import ExperimentConfig
from ..server import server_main, ServerConfig
from ..client import client_main, ClientConfig
from ..common.packets import Parameters
from ..common.types import AlgorithmType, HeuristicType, PlayerType

AI_NAMES = ["AI1", "AI2"]

class ClientThread(threading.Thread):
    __config: ClientConfig

    def __init__(self, config: ClientConfig):
        threading.Thread.__init__(self)
        self.__config = config

    def run(self):
        client_main(self.__config)

def play(url: str, parameters: Parameters):
    res = requests.post(url + "api/new", json=parameters.to_dict())
    data = res.json()

    if 'error' in data:
        raise Exception(f"Error while creating game: {data['error']}")

    game_id = data['game_id']

    client_threads = []

    for name in AI_NAMES:
        thread = ClientThread(ClientConfig(
            url=url,
            player_name=name,
            player_type=PlayerType.AI,
            game_id=game_id
        ))
        thread.start()
        client_threads.append(thread)
        time.sleep(0.5)

    for thread in client_threads:
        thread.join()

def experiment(config: ServerConfig, parameters: Parameters):
    logging.getLogger('werkzeug').setLevel(logging.CRITICAL)

    server_process = multiprocessing.Process(target=server_main, args=(config,))
    url = f"http://localhost:{config.port}/"
    server_process.start()

    time.sleep(2)

    for i, parameters in enumerate(parameters, 1):
        print("Experiment", i, "-", parameters.algorithm.name, "\n")
        play(url=url, parameters=parameters)

    server_process.terminate()

def experiment_main(config: ExperimentConfig):
    PARAMETERS = [
        Parameters(
            board_size=4,
            blocks=[(0, 0), (0, 3), (3, 0), (3, 3)],
            line_up_size=3,
            max_time=5,
            algorithm=AlgorithmType.MINIMAX,
            depths=[6, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.TWO]
        ),
        Parameters(
            board_size=4,
            blocks=[(0, 0), (0, 3), (3, 0), (3, 3)],
            line_up_size=3,
            max_time=1,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[6, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.TWO]
        ),
        Parameters(
            board_size=5,
            block_count=4,
            line_up_size=4,
            max_time=1,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[2, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.TWO]
        ),
        Parameters(
            board_size=5,
            block_count=4,
            line_up_size=4,
            max_time=5,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[6, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.TWO]
        ),
        Parameters(
            board_size=8,
            block_count=5,
            line_up_size=5,
            max_time=1,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[2, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.TWO]
        ),
        Parameters(
            board_size=8,
            block_count=5,
            line_up_size=5,
            max_time=5,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[2, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.TWO]
        ),
        Parameters(
            board_size=8,
            block_count=6,
            line_up_size=5,
            max_time=1,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[6, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.TWO]
        ),
        Parameters(
            board_size=8,
            block_count=6,
            line_up_size=5,
            max_time=5,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[6, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.TWO]
        )
    ]

    if not os.path.exists("./experiments/"):
        os.mkdir("./experiments")

    db_name = f"{int(time.time())}"

    if config.type in ["all", "game"]:
        experiment(ServerConfig(
            debug=False,
            port=config.port,
            db=f"./experiments/{db_name}.db"
        ), PARAMETERS)

    if config.type in ["all", "score"]:
        experiment(ServerConfig(
            debug=False,
            port=config.port + 1,
            db=f"./experiments/{db_name}s.db"
        ), PARAMETERS * 10)
