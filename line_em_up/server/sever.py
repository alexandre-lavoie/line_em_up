from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO, emit, join_room
import uuid
import os.path
from ..datatypes import Parameters, MovePacket, tile_to_emoji, ErrorPacket, WinPacket, JoinResponsePacket, Config
from .game import Game, PlayState, InvalidException, M2Exception
from typing import Dict
import json
import random

class Server:
    _config: Config

    def __init__(self, config: Config):
        self._config=config

    def run(self):
        app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "./templates"))
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
                board=game.board, 
                players=game.players, 
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
                board=game.board, 
                players=game.players, 
                playing=game.all_players(),
                winner=game.winner
            )

        @app.route('/new', methods=['GET', 'POST'])
        def new_game():
            if request.method == "GET":
                return render_template('new.html')
            else:
                try:
                    board_size = int(request.form['board_size'])

                    if board_size < 3 or board_size > 10:
                        raise M2Exception("Board size should be in [3, 10].")

                    block_count = int(request.form['block_count'])

                    if block_count < 0 or block_count > board_size * 2:
                        raise M2Exception("Block count should be in [0, 2 * board size].")

                    line_up_size = int(request.form['line_up_size'])

                    if line_up_size < 3 or line_up_size > board_size:
                        raise M2Exception("Line up size should be in [3, board size].")

                    p1_depth = int(request.form['player_depth1'])
                    p2_depth = int(request.form['player_depth2'])
                    player_depths = (p1_depth, p2_depth)

                    for pd in player_depths:
                        if pd < 1:
                            raise M2Exception("Player depth should be at least 1.")

                    max_time = float(request.form['max_time'])

                    if max_time < 0:
                        raise M2Exception("Max time should be positive.")

                    algorithm = request.form['algorithm']

                    if not algorithm in ["minimax", "alphabeta"]:
                        raise M2Exception("Algorithm should be in [minimax, alphabeta].")

                    heurstic1 = int(request.form['heuristic1'])
                    heurstic2 = int(request.form['heuristic2'])
                    heurstics = (heurstic1, heurstic2)

                    for h in heurstics:
                        if h < 1 or h > 2:
                            raise M2Exception("Heuristic should be in [1, 2].")

                    parameters = Parameters(
                        board_size=board_size,
                        block_count=block_count,
                        line_up_size=line_up_size,
                        player_depths=player_depths,
                        max_time=max_time,
                        algorithm=algorithm,
                        heuristics=heurstics
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
                player_id=str(game.winner)
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

        @socketio.event
        def view(data):
            try:
                if not "game_uuid" in data:
                    raise M2Exception("No game_uuid.")

                join_room(data["game_uuid"])
            except M2Exception as err:
                __handle_error("view", err)

        @socketio.event
        def join(data):
            try:
                if not "player_id" in data:
                    raise M2Exception("No player_id.")

                if not type(data["player_id"]) == str:
                    raise M2Exception("player_id not string.")

                if not "game_uuid" in data:
                    raise M2Exception("No game_uuid.")

                if not data["game_uuid"] in games:
                    raise M2Exception("No game with game_uuid.")

                game_uuid = data["game_uuid"]
                game = games[game_uuid]
                player_id = data["player_id"]

                if game.is_complete():
                    raise M2Exception("Game complete.")

                if player_id in game.players:
                    join_room(game_uuid)

                    packet = JoinResponsePacket(
                        player_id=player_id,
                        player_index=game.players.index(player_id)
                    )

                    emit("join", packet.to_dict())

                    if game.all_players():
                        packet = game.next_packet()
                        emit("play", packet.to_dict())
                    return
                
                joined = game.join(player_id)

                if not joined:
                    raise M2Exception("Could not join.")

                player_games[player_id] = game_uuid
                join_room(game_uuid)

                packet = JoinResponsePacket(
                    player_id=player_id,
                    player_index=game.players.index(player_id)
                )

                emit("join", packet.to_dict(), to=game_uuid)

                if game.all_players():
                    __play(
                        game=game
                    )
            except M2Exception as err:
                __handle_error("join", err)

        @socketio.event
        def play(data):
            game_uuid = None
            game = None
            packet = None
            try:
                if not "player_id" in data:
                    raise M2Exception("No player_id.")

                if not "move" in data:
                    raise M2Exception("No move.")
                
                packet = MovePacket.from_dict(data)

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
            except M2Exception as err:
                __handle_error("play", err)

        @socketio.event
        def parameters(data):
            try:
                if not "game_uuid" in data:
                    raise M2Exception("No game_uuid.")

                if not data["game_uuid"] in games:
                    raise M2Exception("No game with game_uuid.")

                game_uuid = data["game_uuid"]
                game = games[game_uuid]

                emit("parameters", game.parameters.to_dict())
            except M2Exception as err:
                __handle_error("parameters", err)

        socketio.run(app, debug=self._config.debug)
