from argparse import ArgumentParser
from dotenv import load_dotenv
import json
import os
import uuid

def parse_args():
    parser = ArgumentParser(description="Line 'Em Up")

    type_parser = parser.add_subparsers(title="type", dest="type", description="Type of executable to run.")
    client_parser = type_parser.add_parser("client")

    client_parser.add_argument("client_type", choices=("ai", "human"), help="Client type to run as.")
    client_parser.add_argument("--game", help="Game UUID to connect to.", required=True)
    client_parser.add_argument("--name", help="Player name to connect with.", default=str(uuid.uuid4()))

    server_parser = type_parser.add_parser("server")

    server_parser.add_argument("--debug", help="Set server in debug mode.", action="store_true")
    server_parser.add_argument("--port", help="Specify port to run on.", type=int, default=5000)
    server_parser.add_argument("--db", help="SQLite database file.", default="./data.db")

    pool_parser = type_parser.add_parser("pool")

    pool_parser.add_argument("--name", help="AI name to connect with.", default=str(uuid.uuid4()))
    pool_parser.add_argument("--size", help="AI pool size.", type=int, default=1)

    copy_parser = type_parser.add_parser("copy")

    log_parser = type_parser.add_parser("log")

    log_parser.add_argument("--db", help="SQLite database file.", default="./data.db")
    log_parser.add_argument("--ltype", help="Type of log(s) to generate.", choices=("all", "game", "score"), default="all")

    experiment_parser = type_parser.add_parser("experiment")

    experiment_parser.add_argument("--port", help="Port for local server.", type=int, default=5000)
    experiment_parser.add_argument("--etype", help="Type of experiments to perform.", choices=("all", "game", "score"), default="all")

    return parser.parse_args()

def main():
    import os

    load_dotenv()
    args = parse_args()

    if args.type == "server":
        from line_em_up.server import server_main, ServerConfig
        import os.path

        server_main(ServerConfig(
            debug=args.debug,
            port=args.port,
            db=os.path.abspath(args.db)
        ))
    elif args.type == "client":
        from line_em_up.client import client_main, ClientConfig
        from line_em_up.common import PlayerType

        client_main(ClientConfig(
            url=os.environ["URL"],
            player_name=args.name,
            player_type=PlayerType(args.client_type),
            game_id=args.game
        ))
    elif args.type == "pool":
        from line_em_up.client import pool_main, PoolConfig

        pool_main(PoolConfig(
            url=os.environ["URL"],
            player_name=args.name,
            pool_count=args.size
        ))
    elif args.type == "copy":
        import shutil
        import os.path

        target = os.path.join(os.path.dirname(__file__), "./line_em_up/ai/")
        if os.path.exists(target):
            shutil.rmtree(target)

        shutil.copytree(os.environ["AI_PATH"], target)
    elif args.type == "log":
        from line_em_up.log import log_main, LogConfig
        import os.path

        log_main(LogConfig(
            db=os.path.abspath(args.db),
            type=args.ltype
        ))
    elif args.type == "experiment":
        from line_em_up.experiment import experiment_main, ExperimentConfig

        experiment_main(ExperimentConfig(
            port=args.port,
            type=args.etype
        ))

if __name__ == "__main__":
    main()
