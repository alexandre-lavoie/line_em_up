from .config import ServerConfig
from .sever import Server

def server_main(config: ServerConfig):
    server = Server(config)

    server.run()
