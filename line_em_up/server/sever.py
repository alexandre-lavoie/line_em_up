from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO, emit, join_room
import os.path
from ..common import Parameters, MovePacket, tile_to_emoji, ErrorPacket, WinPacket, JoinResponsePacket, JoinPacket, ParametersPacket, ViewPacket, LEMException, Tile, GameUUID, PlayerUUID, PlayerType
from .game import Game, InvalidException
from .config import ServerConfig
from .player import Player, PlayerSession
from typing import Dict, List
import random

class Server:
    _config: ServerConfig
    __games: Dict[GameUUID, Game]
    __players: Dict[PlayerUUID, Player]

    def __init__(self, config: ServerConfig):
        self._config=config
        self.__games={}
        self.__players={}

    def __start_game(self, game: Game):
        self.__games[game.uuid]=game

    def __end_game(self, game: Game):
        for player in game.players:
            player.close_session(
                game_uuid=game.uuid
            )

    def __get_player(self, player_uuid: str) -> Player:
        if not player_uuid in self.__players:
            raise LEMException("No player with id.")

        return self.__players[player_uuid]

    def __join_game(self, player: Player, game: Game):
        joined = game.join(
            player=player
        )

        if not joined:
            raise LEMException("Could not join game.")

    def __get_game(self, uuid: GameUUID) -> Game:
        if not uuid in self.__games:
            raise LEMException("No game with game_uuid.")

        return self.__games[uuid]

    def __get_games(self) -> List[Game]:
        return self.__games.values()

    def __get_open_games(self) -> List[Game]:
        return [game for game in self.__get_games() if not game.is_private and not game.is_complete]

    def __get_completed_games(self) -> List[Game]:
        return [game for game in self.__get_games() if game.is_complete]

    def __make_player(self, uuid: PlayerUUID, type: PlayerType) -> Player:
        if uuid in self.__players:
            player = self.__players[uuid] 

            if not player.type == type:
                raise LEMException("Player types do not match.") 

            return player

        player = Player(
            uuid=uuid,
            type=type
        )
        self.__players[uuid] = player

        return player

    def __get_player(self, uuid: PlayerUUID) -> Player:
        if not uuid in self.__players:
            raise LEMException("No player with uuid.")

        return self.__players[uuid]

    def __random_board(self, board_size: int) -> List[List[str]]:
        return [[tile_to_emoji(tile) for tile in random.choices(list(Tile), k=board_size)] for _ in range(board_size)]

    def __get_dataclass(self, dataclass: any, data: any):
        try:
            return dataclass.from_dict(data)
        except Exception as err:
            raise LEMException(str(err))

    def __handle_win(self, game: Game):
        packet = WinPacket(
            player_uuid=game.winner
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
            return render_template('index.html', 
                board=self.__random_board(10)
            )

        @app.route('/view/<game_uuid>')
        def view_game(game_uuid: str):
            try:
                game = self.__get_game(game_uuid)

                return render_template('view.html', 
                    game_uuid=game_uuid, 
                    board=game.pretty_board, 
                    players=game.players,
                    playing=game.all_players,
                    winner=game.winner,
                    is_complete=game.is_complete
                )
            except LEMException:
                return redirect('/')

        @app.route('/play/<game_uuid>')
        def play_game(game_uuid: str):
            try:
                game = self.__get_game(game_uuid)

                if game.is_complete:
                    return redirect(f"/view/{game_uuid}")

                return render_template('play.html', 
                    game_uuid=game_uuid, 
                    board=game.pretty_board, 
                    playing=game.all_players,
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

        @app.route('/games', methods=['GET'])
        def games_list():
            return render_template("games.html", 
                open_games=self.__get_open_games(), 
                completed_games=self.__get_completed_games()
            )

        @app.route('/player/<player_uuid>', methods=['GET'])
        def player_profile(player_uuid: str):
            try:
                player = self.__get_player(uuid=player_uuid)

                return render_template("player.html",
                    player=player,
                    games=[self.__games[game_uuid] for game_uuid in player.games]
                )
            except:
                return redirect("/")

        @app.route('/leaderboard', methods=['GET'])
        def leaderboard():
            return render_template("leaderboard.html",
                players=self.__players.values()
            )

        @socketio.on("view")
        def view(data):
            packet = self.__get_dataclass(ViewPacket, data)
            join_room(packet.game_uuid)

        @socketio.on("join")
        def join(data):
            packet = self.__get_dataclass(JoinPacket, data)
            game = self.__get_game(uuid=packet.game_uuid)

            if game.is_complete:
                raise LEMException("Game complete.")

            player = self.__make_player(uuid=packet.player_uuid, type=packet.player_type)

            if player.has_session(game_uuid=game.uuid):
                raise LEMException("Already a session with this player in this game.")

            if not game.join(player=player, player_type=packet.player_type):
                raise LEMException("Could not join game.")

            session = PlayerSession(
                game_uuid=game.uuid,
                index=game.player_count - 1,
                socket=request.sid
            )

            player.begin_session(session=session)

            join_room(game.uuid)

            join_packet = JoinResponsePacket(
                player_uuid=player.uuid,
                player_index=session.index,
                player_type=packet.player_type
            )

            emit("join", join_packet.to_dict(), to=game.uuid)

            if game.all_players:
                self.__handle_play(game=game)

        @socketio.on("play")
        def play(data):
            packet = self.__get_dataclass(MovePacket, data)
            player = self.__get_player(uuid=packet.player_uuid)
            session = player.get_session(socket=request.sid)
            game = self.__get_game(uuid=session.game_uuid)

            try:
                game.play(packet)
            finally:
                if game.check_complete():
                    self.__handle_win(game=game)

                self.__handle_play(game=game)

        @socketio.on("parameters")
        def parameters(data):
            packet = self.__get_dataclass(ParametersPacket, data)
            game = self.__get_game(uuid=packet.game_uuid)

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
