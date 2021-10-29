from argparse import ArgumentParser
from dotenv import load_dotenv
import json
import os

def parse_args():
    parser = ArgumentParser(description="Line 'Em Up")

    type_parser = parser.add_subparsers(title="type", dest="type", description="Type of executable to run.")
    client_parser = type_parser.add_parser("client")

    client_parser.add_argument("client_type", choices=("ai", "human"), help="Client type to run as.")
    client_parser.add_argument("--game", help="Game UUID to connect to.", required=True)
    client_parser.add_argument("--name", help="Player name to connect with.")

    server_parser = type_parser.add_parser("server")

    server_parser.add_argument("--debug", action="store_true")

    return parser.parse_args()

def main():
    load_dotenv()
    args = parse_args()

    if args.type == "server":
        from line_em_up.server import server_main, ServerConfig

        server_main(ServerConfig(
            debug=args.debug
        ))
    elif args.type == "client":
        from line_em_up.client import client_main, ClientConfig
        from line_em_up.common import PlayerType
        import uuid

        client_main(ClientConfig(
            url=os.environ["URL"],
            player_name=args.name if args.name else str(uuid.uuid4()),
            player_type=PlayerType.HUMAN if args.client_type == "human" else PlayerType.AI,
            game_id=args.game
        ))

if __name__ == "__main__":
    main()
