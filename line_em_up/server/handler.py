from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update
from typing import Tuple, List
import random
import time

from ..common.exceptions import LEMException
from ..common.types import Tile, PlayerType
from ..common.packets import Parameters, PlayPacket, MovePacket
from .sql import GameSession, Game, Player, GameTile, Statistics

class ServerHandler:
    session: Session

    def __init__(self, session: Session):
        self.session = session

    def _commit(self):
        self.session.commit()

    def _flush(self):
        self.session.flush()

    def get_session(self, socket_id: str) -> GameSession:
        return self.session.query(GameSession).filter(GameSession.socket_id == socket_id).first()

    def get_game(self, game_id: str) -> Game:
        return self.session.query(Game).filter(Game.id == game_id).first()

    def get_games(self) -> List[Game]:
        return self.session.query(Game).all()

    def get_active_games(self) -> List[Game]:
        return self.session.query(Game).filter(Game.listed == True, Game.complete == False).all()

    def get_open_games(self, player_name: str = None) -> List[Game]:
        open_games = list(filter(lambda game: not game.started, self.session.query(Game).filter(Game.listed == True, Game.complete == False).all()))

        if player_name:
            open_games = list(filter(lambda game: not any(session.player.name == player_name for session in game.sessions), open_games))

        return open_games

    def get_completed_games(self) -> List[Game]:
        return self.session.query(Game).filter(Game.complete == True).all()

    def get_player(self, player_id: str = None, player_name: str = None) -> Player:
        if player_id:
            return self.session.query(Player).filter(Player.id == player_id).first()
        elif player_name:
            return self.session.query(Player).filter(Player.name == player_name).first()
        else:
            raise HandlerException("Cannot get player without any filter.")

    def get_players(self) -> List[Player]:
        return self.session.query(Player).all()

    def _get_random_block_positions(self, block_count: int, board_size: int):
        blocks = []
        block_indicies = random.sample(list(range(board_size ** 2)), k=block_count)
        for block_index in block_indicies:
            x, y = block_index % board_size, block_index // board_size
            blocks.append((x, y))
        
        return blocks

    def _create_blocks(self, game_id: str, block_count: int, board_size: int):
        blocks = self._get_random_block_positions(
            block_count=block_count,
            board_size=board_size
        )

        tiles = []
        for x, y in blocks:
            tile = GameTile(
                game_id=game_id,
                x=x,
                y=y,
                type=Tile.BLOCK
            )
            tiles.append(tile)

        self.session.add_all(tiles)

    def create_game(self, parameters: Parameters) -> Game:
        block_count = parameters.block_count

        pdict = parameters.to_dict()
        del pdict['block_count']

        game = Game(**pdict)

        self.session.add(game)
        self._flush()

        self._create_blocks(
            game_id=game.id,
            block_count=block_count,
            board_size=parameters.board_size
        )
        self._commit()

        return game

    def has_player(self, player_name: str) -> bool:
        return len(self.session.query(Player).filter(Player.name == player_name).all()) > 0
    
    def create_player(self, player_name: str) -> Player:
        player = Player(
            name=player_name
        )

        self.session.add(player)
        self._commit()

        return player

    def create_session(self, socket_id: str, player_type: PlayerType, game_id: str, player_id: str) -> GameSession:
        game = self.get_game(game_id=game_id)

        session = GameSession(
            game_id=game_id,
            player_id=player_id,
            socket_id=socket_id,
            player_type=player_type,
            tile=game.get_player_tile(player_id=player_id)
        )

        self.session.add(session)
        self._commit()

        return session

    def get_play_packet(self, socket_id: str) -> PlayPacket:
        session = self.get_session(socket_id=socket_id)

        return PlayPacket(
            tile=session.game.tile_turn,
            emoji_board=session.game.pretty_board,
            moves=session.game.moves,
            blocks=session.game.blocks,
            order=session.game.tile_order
        )

    def _handle_win(self, session: GameSession):
        if not session.game.check_complete(): 
            return False

        self.session.execute(
            update(Game)
            .where(Game.id == session.game.id)
            .values(
                tile_turn=Tile.EMPTY,
                tile_winner=session.game.tile_winner,
                complete=True
            )
        )
        self._commit()

        return True

    def _handle_next_move(self, session: GameSession):
        self.session.execute(
            update(Game)
            .where(Game.id == session.game.id)
            .values(
                tile_turn=session.game.next_tile,
                last_time=time.time()
            )
        )
        self._commit()

    def _handle_invalid_play(self, session: GameSession, message: str):
        if session.player_type == PlayerType.AI:
            session.game.add_loser(session.tile)
            self.session.execute(
                update(Game)
                .where(Game.id == session.game.id)
                .values(
                    _tile_losers=','.join(str(tile.value) for tile in session.game.tile_losers)
                )
            )
            self._commit()

            if not self._handle_win(session=session):
                self._handle_next_move(session=session)

        raise LEMException(message)

    def _is_tile_empty(self, game_id: str, coordinate: Tuple[int, int]) -> bool:
        return len(self.session.query(GameTile).filter(GameTile.game_id == game_id, GameTile.x == coordinate[0], GameTile.y == coordinate[1]).all()) == 0

    def play(self, socket_id: str, packet: MovePacket) -> GameSession:
        play_time = time.time()

        session = self.get_session(socket_id=socket_id)

        if not session.game.started:
            raise LEMException("Game not started.")

        if session.game.complete:
            raise LEMException("Game complete.")
    
        if not session.game.tile_turn == session.tile:
            raise LEMException("Not player turn.")

        if not session.game.last_time == None:
            if session.player_type == PlayerType.AI and play_time - session.game.last_time > session.game.max_time:
                self._handle_invalid_play(
                    session=session,
                    message="Too slow."
                )

        coordinate = packet.move

        for p in coordinate:
            if p < 0 or p >= session.game.board_size:
                self._handle_invalid_play(
                    session=session,
                    message="Invalid move."
                )

        if not self._is_tile_empty(game_id=session.game.id, coordinate=coordinate):
            self._handle_invalid_play(
                session=session,
                message="Tile not empty."
            )

        move = GameTile(
            game_id=session.game.id,
            x=coordinate[0],
            y=coordinate[1],
            type=session.tile
        )

        self.session.add(move)
        self._commit()

        if packet.statistics:
            statistics = Statistics(
                tile_id=move.id,
                **packet.statistics.to_dict()
            )

            self.session.add(statistics)
            self._commit()

        if not self._handle_win(session=session):
            self._handle_next_move(session=session)

        return session
