from .client import NetworkClient
from ..datatypes import Config
from typing import Union

def client_main(config: Config):
    client = NetworkClient(config)

    client.run()
