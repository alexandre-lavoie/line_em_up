from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO, emit, join_room
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine
import os.path
from typing import Dict, List
import random

from ..common import Parameters, MovePacket, tile_to_emoji, ErrorPacket, WinPacket, JoinResponsePacket, JoinPacket, ParametersPacket, ViewPacket, LEMException, Tile, GameUUID, PlayerUUID, PlayerType, Emojis
from .config import ServerConfig
from .sql import Base
from .handler import ServerHandler

class Server:
    _config: ServerConfig

    def __init__(self, config: ServerConfig):
        self._config=config

    def __random_board(self, board_size: int) -> List[List[str]]:
        return [[tile_to_emoji(tile) for tile in random.choices(list(Tile), k=board_size)] for _ in range(board_size)]

    def __get_dataclass(self, dataclass: any, data: any):
        try:
            return dataclass.from_dict(data)
        except Exception as err:
            raise LEMException(str(err))

    def run(self):
        if self._config.debug:
            engine = create_engine(
                'sqlite://',
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                # echo=True
            )
        else:
            engine = create_engine(
                f'sqlite:///{os.path.abspath("./data.db")}',
                connect_args={"check_same_thread": False},
            )
        Base.metadata.create_all(engine)
        SessionMaker = sessionmaker(bind=engine)

        app = Flask(
            __name__,
            static_url_path="",
            static_folder=os.path.join(os.path.dirname(__file__), "../web/static"),
            template_folder=os.path.join(os.path.dirname(__file__), "../web/templates")
        )
        socketio = SocketIO(app)

        @app.before_request
        def before_request():
            request.handler = ServerHandler(session=SessionMaker())

        @app.route('/')
        def index():
            return render_template('index.html', 
                board=self.__random_board(10)
            )

        @app.route('/view/<game_id>')
        def view_game(game_id: str):
            try:
                game = request.handler.get_game(game_id=game_id)

                if not game:
                    raise LEMException("Game not found.")

                return render_template('view.html',
                    game=game,
                    emojis=Emojis
                )
            except LEMException:
                return redirect('/')

        @app.route('/play/<game_id>')
        def play_game(game_id: str):
            try:
                game = request.handler.get_game(game_id=game_id)

                if not game:
                    raise LEMException("Game not found.")

                if game.complete:
                    return redirect(f"/view/{game.id}")

                return render_template('play.html',
                    game=game
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
                game = request.handler.create_game(parameters=parameters)

                return redirect(f"/view/{game.id}")
            except LEMException as err:
                return render_template('new.html', error=str(err))

        @app.route('/games', methods=['GET'])
        def games_list():
            return render_template("games.html", 
                active_games=request.handler.get_active_games(), 
                completed_games=request.handler.get_completed_games(),
                emojis=Emojis
            )

        @app.route('/player/<player_id>', methods=['GET'])
        def player_profile(player_id: str):
            try:
                player = request.handler.get_player(player_id=player_id)

                return render_template("player.html",
                    player=player,
                    emojis=Emojis
                )
            except:
                return redirect("/")

        @app.route('/leaderboard', methods=['GET'])
        def leaderboard():
            return render_template("leaderboard.html",
                players=list(sorted(request.handler.get_players(), key=lambda player: player.score, reverse=True))
            )

        @app.route('/api/games', methods=['GET'])
        def games_api_list_any():
            return {
                "open_games": [game.id for game in request.handler.get_open_games()]
            }

        @app.route('/api/games/<player_name>', methods=['GET'])
        def games_api_list(player_name: str):
            return {
                "open_games": [game.id for game in request.handler.get_open_games(player_name=player_name)]
            }

        @socketio.on("view")
        def view(data):
            request.handler = ServerHandler(session=SessionMaker())

            packet = self.__get_dataclass(ViewPacket, data)

            game = request.handler.get_game(game_id=packet.game_id)

            if not game:
                raise LEMException("No game with game_id.")

            join_room(game.id)

        @socketio.on("join")
        def join(data):
            request.handler = ServerHandler(session=SessionMaker())

            packet = self.__get_dataclass(JoinPacket, data)

            game = request.handler.get_game(game_id=packet.game_id)

            if not game:
                raise LEMException("No game with game_id.")

            if game.complete:
                raise LEMException("Game complete.")

            if request.handler.has_player(player_name=packet.player_name):
                player = request.handler.get_player(player_name=packet.player_name)
            else:
                player = request.handler.create_player(player_name=packet.player_name)

            session = request.handler.get_session(socket_id=request.sid)
            if not session:
                try:
                    session = request.handler.create_session(
                        socket_id=request.sid,
                        player_type=packet.player_type,
                        game_id=game.id,
                        player_id=player.id
                    )
                except:
                    raise LEMException("Unable to make new session.")

            join_room(game.id)

            join_packet = JoinResponsePacket(
                socket_id=request.sid,
                player_id=player.id,
                player_name=player.name,
                player_type=session.player_type,
                tile=session.tile
            )

            emit("join", join_packet.to_dict(), to=game.id)

            if game.started:
                emit("play", request.handler.get_play_packet(socket_id=request.sid).to_dict(), to=game.id)

        @socketio.on("play")
        def play(data):
            request.handler = ServerHandler(session=SessionMaker())

            packet = self.__get_dataclass(MovePacket, data)

            try:
                session = request.handler.play(socket_id=request.sid, packet=packet)
                emit("play", request.handler.get_play_packet(socket_id=request.sid).to_dict(), to=session.game.id)
            finally:
                session = request.handler.get_session(socket_id=request.sid)

                if not session:
                    return

                if session.game.complete:
                    winner = session.game.winner
                    player_name = winner.name if winner else None
                    player_id = winner.id if winner else None

                    emit("win", WinPacket(tile=session.game.tile_winner, player_name=player_name, player_id=player_id).to_dict(), to=session.game.id)

        @socketio.on("parameters")
        def parameters(data):
            request.handler = ServerHandler(session=SessionMaker())

            packet = self.__get_dataclass(ParametersPacket, data)
            game = request.handler.get_game(game_id=packet.game_id)

            if game == None:
                raise LEMException("No game with game_id.")

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

        socketio.run(app, host="0.0.0.0", debug=self._config.debug, port=self._config.port)
