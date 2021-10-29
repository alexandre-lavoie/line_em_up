from .client import NetworkClient
from .config import ClientConfig, PoolConfig
from typing import Union, Set
import requests
import urllib.parse
import time
import threading

def client_main(config: ClientConfig):
    client = NetworkClient(config)
    client.run()

    return client

class PoolThread(threading.Thread):
    __config: PoolConfig
    __lock: threading.Lock
    __ids: Set[int]

    def __init__(self, config: PoolConfig, lock: threading.Lock, ids: Set[int]):
        threading.Thread.__init__(self)
        self.__config = config
        self.__lock = lock
        self.__ids = ids

    def run(self):
        from ..common import PlayerType
        
        while True:
            print("Finding match")

            game_id = None
            while True:
                self.__lock.acquire()
                res = requests.get(urllib.parse.urljoin(self.__config.url, f"api/games/{self.__config.player_name}"))
                open_games = res.json()["open_games"]

                for open_game in open_games:
                    if not open_game in self.__ids:
                        self.__ids.add(open_game)
                        game_id = open_game
                        break
                
                self.__lock.release()

                if game_id:
                    break

                time.sleep(5)

            try:
                client = client_main(ClientConfig(
                    url=self.__config.url,
                    player_name=self.__config.player_name,
                    player_type=PlayerType.AI,
                    game_id=game_id
                ))

                while not client.done:
                    time.sleep(1)
            except Exception as err:
                print(err)

def pool_main(config: PoolConfig):
    threads = []
    lock = threading.Lock()
    ids = set()

    for _ in range(config.pool_count):
        thread = PoolThread(config=config, lock=lock, ids=ids)
        thread.start()
        threads.append(thread)
        time.sleep(1)

    for thread in threads:
        thread.join()