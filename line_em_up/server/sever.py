from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO, emit, join_room
import uuid
import os.path
from ..common import Parameters, MovePacket, tile_to_emoji, ErrorPacket, WinPacket, JoinResponsePacket, JoinPacket, ParametersPacket, ViewPacket, LEMException, Tile, GameUUID, PlayerID
from .game import Game, InvalidException
from .config import ServerConfig
from typing import Dict, List
import json
import random

class Server:
    _config: ServerConfig
    __games: Dict[GameUUID, Game]
    __player_games: Dict[PlayerID, GameUUID]

    def __init__(self, config: ServerConfig):
        self._config=config
        self.__games={}
        self.__player_games={}

    def __start_game(self, game: Game):
        self.__games[game.uuid]=game

    def __end_game(self, game: Game):
        for player in game.players:
            del self.__player_games[player]

    def __join_game(self, player_id: PlayerID, player_type: str, game: Game):
        joined = game.join(
            player_id=player_id,
            player_type=player_type
        )

        if not joined:
            raise LEMException("Could not join game.")

        self.__player_games[player_id] = game.uuid

    def __get_game(self, game_uuid: GameUUID) -> Game:
        if not game_uuid in self.__games:
            raise LEMException("No game with game_uuid.")

        return self.__games[game_uuid]

    def __get_player_game(self, player_id: PlayerID) -> Game:
        if not player_id in self.__player_games:
            raise LEMException("Player not in game.")

        return self.__get_game(self.__player_games[player_id])

    def __random_board(self, board_size: int) -> List[List[str]]:
        return [[tile_to_emoji(tile) for tile in random.choices(list(Tile), k=board_size)] for _ in range(board_size)]

    def __get_dataclass(self, dataclass: any, data: any):
        try:
            return dataclass.from_dict(data)
        except Exception as err:
            raise LEMException(str(err))

    def __handle_win(self, game: Game):
        packet = WinPacket(
            player_id=game.winner
        )
        emit("win", packet.to_dict(), to=game.uuid)

        self.__end_game(game)

    def __handle_play(self, game: Game):
        packet = game.next_packet()
        game.reset_time()
        emit("play", packet.to_dict(), to=game.uuid)

    def run(self):
        app = Flask(
            __name__,
            static_url_path="",
            static_folder=os.path.join(os.path.dirname(__file__), "../web/static"),
            template_folder=os.path.join(os.path.dirname(__file__), "../web/templates")
        )
        socketio = SocketIO(app)

        @app.route('/')
        def index():
            return render_template('index.html', board=self.__random_board(10))

        @app.route('/view/<game_uuid>')
        def view_game(game_uuid: str):
            try:
                game = self.__get_game(game_uuid)

                return render_template('view.html', 
                    game_uuid=game_uuid, 
                    board=game.pretty_board, 
                    players_types=game.players_types, 
                    playing=game.all_players(),
                    winner=game.winner,
                    is_complete=game.is_complete()
                )
            except LEMException:
                return redirect('/')

        @app.route('/play/<game_uuid>')
        def play_game(game_uuid: str):
            try:
                game = self.__get_game(game_uuid)

                if game.is_complete():
                    return redirect(f"/view/{game_uuid}")

                return render_template('play.html', 
                    game_uuid=game_uuid, 
                    board=game.pretty_board, 
                    playing=game.all_players(),
                    winner=game.winner
                )
            except LEMException:
                return redirect('/')

        @app.route('/new', methods=['GET'])
        def new_game_get():
            return render_template('new.html')

        @app.route('/new', methods=['POST'])
        def new_game_post():
            try:
                parameters = self.__get_dataclass(Parameters, request.form)
                game = Game(
                    parameters=parameters
                )

                self.__start_game(game)

                return redirect(f"/view/{game.uuid}")
            except LEMException as err:
                return render_template('new.html', error=str(err))

        @socketio.on("view")
        def view(data):
            packet = self.__get_dataclass(ViewPacket, data)
            join_room(packet.game_uuid)

        @socketio.on("join")
        def join(data):
            packet = self.__get_dataclass(JoinPacket, data)
            game = self.__get_game(packet.game_uuid)

            if game.is_complete():
                raise LEMException("Game complete.")

            is_new = False
            if not packet.player_id in game.players:
                self.__join_game(
                    player_id=packet.player_id,
                    player_type=packet.player_type,
                    game=game
                )

                is_new = True

            join_room(game.uuid)

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
                    self.__handle_play(
                        game=game
                    )
                else:
                    play_packet = game.next_packet()
                    emit("play", play_packet.to_dict())

        @socketio.on("play")
        def play(data):
            packet = self.__get_dataclass(MovePacket, data)
            game = self.__get_player_game(packet.player_id)

            if game.is_complete():
                raise LEMException("Game complete.")

            ie = None
            try:
                game.play(packet)
            except InvalidException as err:
                ie = err

            if game.is_complete():
                self.__handle_win(
                    game=game
                )

            self.__handle_play(
                game=game
            )

            if ie: raise ie

        @socketio.on("parameters")
        def parameters(data):
            packet = self.__get_dataclass(ParametersPacket, data)
            game = self.__get_game(packet.game_uuid)

            emit("parameters", game.parameters.to_dict())

        @socketio.on_error()
        def error_handler(err):
            try:
                raise err
            except LEMException as lerr:
                packet = ErrorPacket(
                    error=str(lerr)
                )
                emit("error", packet.to_dict())

        socketio.run(app, debug=self._config.debug)
