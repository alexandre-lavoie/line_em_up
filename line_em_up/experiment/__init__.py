import requests
import time
import threading

from ..client import client_main
from ..client.config import ClientConfig
from ..common.packets import Parameters
from ..common.types import AlgorithmType, HeuristicType, PlayerType

class ClientThread(threading.Thread):
    __config: ClientConfig

    def __init__(self, config: ClientConfig):
        threading.Thread.__init__(self)
        self.__config = config

    def run(self):
        client_main(self.__config)

def experiment_main():
    PARAMETERS = [
        Parameters(
            board_size=4,
            blocks=[(0, 0), (0, 3), (3, 0), (3, 3)],
            line_up_size=3,
            max_time=5,
            algorithm=AlgorithmType.MINIMAX,
            depths=[6, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.ONE]
        ),
        Parameters(
            board_size=4,
            blocks=[(0, 0), (0, 3), (3, 0), (3, 3)],
            line_up_size=3,
            max_time=1,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[6, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.ONE]
        ),
        Parameters(
            board_size=5,
            block_count=4,
            line_up_size=4,
            max_time=1,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[2, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.ONE]
        ),
        Parameters(
            board_size=5,
            block_count=4,
            line_up_size=4,
            max_time=5,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[6, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.ONE]
        ),
        Parameters(
            board_size=8,
            block_count=5,
            line_up_size=5,
            max_time=1,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[2, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.ONE]
        ),
        Parameters(
            board_size=8,
            block_count=5,
            line_up_size=5,
            max_time=5,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[2, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.ONE]
        ),
        Parameters(
            board_size=8,
            block_count=6,
            line_up_size=5,
            max_time=1,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[6, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.ONE]
        ),
        Parameters(
            board_size=8,
            block_count=6,
            line_up_size=5,
            max_time=5,
            algorithm=AlgorithmType.ALPHABETA,
            depths=[6, 6],
            heuristics=[HeuristicType.ONE, HeuristicType.ONE]
        )
    ]

    AI_NAMES = ["AI1", "AI2"]
    url = "http://localhost:5000/"

    game_ids = []
    for parameters in PARAMETERS[:1]:
        res = requests.post(url + "api/new", json=parameters.to_dict())
        data = res.json()

        if 'error' in data:
            raise Exception(f"Error while creating game: {j['error']}")
        else:
            game_ids.append(data['game_id'])

    for game_id in game_ids:
        threads = []

        for name in AI_NAMES:
            thread = ClientThread(ClientConfig(
                url=url,
                player_name=name,
                player_type=PlayerType.AI,
                game_id=game_id
            ))
            thread.start()
            threads.append(thread)
            time.sleep(0.5)

        for thread in threads:
            thread.join()
