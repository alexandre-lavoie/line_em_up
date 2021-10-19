from line_em_up import Config
from argparse import ArgumentParser
from dotenv import load_dotenv
import json
import os

if __name__ == "__main__":
    load_dotenv()

    parser = ArgumentParser(description="COMP 472 - Mini Project 2")

    type_parser = parser.add_subparsers(title="type", dest="type", description="Type of executable to run.")
    server_parser = type_parser.add_parser("server")

    server_parser.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    if args.type == "server":
        from line_em_up import server_main

        server_main(Config(
            is_human=False,
            url=None,
            player_id=None,
            game_uuid=None,
            debug=args.debug
        ))
