from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO, emit, join_room
import uuid
import os.path
from ..datatypes import Parameters, MovePacket, tile_to_emoji, ErrorPacket, WinPacket, JoinResponsePacket, JoinPacket, Config, ParametersPacket, ViewPacket
from .game import Game, PlayState, InvalidException, M2Exception
from typing import Dict, List
import json
import random

class Server:
    _config: Config

    def __init__(self, config: Config):
        self._config=config

    def run(self):
        app = Flask(
            __name__,
            static_url_path="",
            static_folder=os.path.join(os.path.dirname(__file__), "./static"),
            template_folder=os.path.join(os.path.dirname(__file__), "./templates")
        )
        socketio = SocketIO(app)

        games: Dict[str, Game] = {}
        player_games: Dict[str, str] = {}

        @app.route('/')
        def index():
            board_size = 10

            return render_template('index.html', board=[[tile_to_emoji(random.randint(0, 3)) for __ in range(board_size)] for _ in range(board_size)])

        @app.route('/view/<game_uuid>')
        def view_game(game_uuid: str):
            if not game_uuid in games:
                return redirect('/')
                
            game = games[game_uuid]

            return render_template('view.html', 
                game_uuid=game_uuid, 
                board=game.pretty_board, 
                players_types=game.players_types, 
                playing=game.all_players(),
                winner=game.winner,
                is_complete=game.is_complete()
            )

        @app.route('/play/<game_uuid>')
        def play_game(game_uuid: str):
            if not game_uuid in games:
                return redirect('/')

            game = games[game_uuid]

            if game.is_complete():
                return redirect(f"/view/{game_uuid}")

            return render_template('play.html', 
                game_uuid=game_uuid, 
                board=game.pretty_board, 
                playing=game.all_players(),
                winner=game.winner
            )

        def __get_param(label: str, vals: List[any], is_range: bool=False):
            val = request.form[label]
            target_type = type(vals[0])

            try:
                if target_type in [int, float, str]:
                    val = target_type(val)
                else:
                    raise Exception("Invalid type.")
            except Exception as err:
                raise M2Exception(f"{label} should be type {str(target_type)}.")

            if is_range:
                if val < vals[0] or val > vals[1]:
                    raise M2Exception(f"{label} should be in {str(vals)}.")
            else:
                if not val in vals:
                    raise M2Exception(f"{label} should be in {str(vals)}.")

            return val

        @app.route('/new', methods=['GET', 'POST'])
        def new_game():
            if request.method == "GET":
                return render_template('new.html')
            else:
                try:
                    board_size = __get_param("board_size", [3, 10], is_range=True)
                    block_count = __get_param("block_count", [0, board_size * 2], is_range=True)
                    line_up_size = __get_param("line_up_size", [3, board_size], is_range=True)
                    
                    player_depths = []
                    for i in range(1, 3):
                        player_depths.append(__get_param(f"player_depth{i}", [1, float('inf')], is_range=True))

                    max_time = __get_param("max_time", [0, float('inf')], is_range=True)
                    algorithm = __get_param("algorithm", ["minimax", "alphabeta"])

                    heuristics = []
                    for i in range(1, 3):
                        heuristics.append(__get_param(f"heuristic{i}", [1, 2]))

                    parameters = Parameters(
                        board_size=board_size,
                        block_count=block_count,
                        line_up_size=line_up_size,
                        player_depths=player_depths,
                        max_time=max_time,
                        algorithm=algorithm,
                        heuristics=heuristics
                    )

                    game_uuid = str(uuid.uuid4()).split("-")[0]
                    game = Game(
                        uuid=game_uuid,
                        parameters=parameters
                    )

                    games[game_uuid] = game

                    return redirect(f"/view/{game_uuid}")
                except M2Exception as err:
                    return render_template('new.html', error=str(err))

        def __win(game: Game):
            packet = WinPacket(
                player_id=game.winner
            )

            emit("win", packet.to_dict(), to=game.uuid)

            for player in game.players:
                del player_games[player]

        def __play(game: Game):
            packet = game.next_packet()
            game.reset_time()
            emit("play", packet.to_dict(), to=game.uuid)

        def __handle_error(endpoint: str, data: any):
            packet = ErrorPacket(
                error=str(data)
            )

            emit(endpoint, packet.to_dict())

        def __get_packet(packet_type: any, data: any):
            try:
                return packet_type.from_dict(data)
            except Exception as err:
                raise M2Exception(str(err))

        @socketio.event
        def view(data):
            try:
                packet = __get_packet(ViewPacket, data)
                join_room(packet.game_uuid)
            except M2Exception as err:
                __handle_error("view", err)

        @socketio.event
        def join(data):
            try:
                packet = __get_packet(JoinPacket, data)

                if not type(packet.player_id) == str or len(packet.player_id) == 0:
                    raise M2Exception("player_id not valid string.")

                if not packet.game_uuid in games:
                    raise M2Exception("No game with game_uuid.")

                game = games[packet.game_uuid]

                if game.is_complete():
                    raise M2Exception("Game complete.")

                is_new = False
                if not packet.player_id in game.players:
                    if not game.join(
                        player_id=packet.player_id,
                        player_type=packet.player_type
                    ):
                        raise M2Exception("Could not join.")

                    is_new = True
                
                player_games[packet.player_id] = packet.game_uuid
                join_room(packet.game_uuid)

                player_index=game.players.index(packet.player_id)

                join_packet = JoinResponsePacket(
                    player_id=packet.player_id,
                    player_index=player_index,
                    player_type=packet.player_type
                )

                if is_new:
                    emit("join", join_packet.to_dict(), to=packet.game_uuid)
                else:
                    emit("join", join_packet.to_dict())

                if game.all_players():
                    if is_new:
                        __play(
                            game=game
                        )
                    else:
                        play_packet = game.next_packet()
                        emit("play", play_packet.to_dict())
            except M2Exception as err:
                __handle_error("join", err)

        @socketio.event
        def play(data):
            try:
                packet = __get_packet(MovePacket, data)

                if not packet.player_id in player_games:
                    raise M2Exception("Player not in game.")

                game_uuid = player_games[packet.player_id]
                game = games[game_uuid]

                if game.is_complete():
                    raise M2Exception("Game complete.")

                game.play(packet)

                if game.is_complete():
                    __win(
                        game=game
                    )

                __play(
                    game=game
                )
            except InvalidException as err:
                __handle_error("play", err)
                __win(
                    game=game
                )
                __play(
                    game=game
                )
            except M2Exception as err:
                __handle_error("play", err)

        @socketio.event
        def parameters(data):
            try:
                packet = __get_packet(ParametersPacket, data)

                if not packet.game_uuid in games:
                    raise M2Exception("No game with game_uuid.")

                game = games[packet.game_uuid]

                emit("parameters", game.parameters.to_dict())
            except M2Exception as err:
                __handle_error("parameters", err)

        socketio.run(app, debug=self._config.debug)
