from ..datatypes import Config
from .sever import Server

def server_main(config: Config):
    server = Server(config)

    server.run()
