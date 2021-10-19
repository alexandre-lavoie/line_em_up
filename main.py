from line_em_up import Config, PlayerType
from argparse import ArgumentParser
from dotenv import load_dotenv
import json
import os

if __name__ == "__main__":
    load_dotenv()

    parser = ArgumentParser(description="Line 'Em Up")

    type_parser = parser.add_subparsers(title="type", dest="type", description="Type of executable to run.")
    client_parser = type_parser.add_parser("client")

    client_parser.add_argument("client_type", choices=("ai", "human"), help="Client type to run as.")
    client_parser.add_argument("game_uuid", help="Game UUID to connect to.")
    client_parser.add_argument("player_id", help="Player id to connect with.")

    server_parser = type_parser.add_parser("server")

    server_parser.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    if args.type == "server":
        from line_em_up import server_main

        server_main(Config(
            url=None,
            player_id=None,
            player_type=PlayerType.AI,
            game_uuid=None,
            debug=args.debug
        ))
    elif args.type == "client":
        from line_em_up import client_main

        client_main(Config(
            url=os.environ["URL"],
            player_id=args.player_id,
            player_type=PlayerType.HUMAN if args.client_type == "human" else PlayerType.AI,
            game_uuid=args.game_uuid,
            debug=False
        ))
