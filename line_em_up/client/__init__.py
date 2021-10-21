from .client import NetworkClient
from .config import ClientConfig
from typing import Union

def client_main(config: ClientConfig):
    client = NetworkClient(config)

    client.run()
