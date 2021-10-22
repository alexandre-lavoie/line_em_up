from dataclasses import dataclass
from typing import Dict, List

from line_em_up.common.exceptions import LEMException
from ..common import PlayerUUID, PlayerType, GameUUID

@dataclass
class PlayerSession:
    game_uuid: GameUUID
    index: int
    socket: str

class Player:
    __uuid: PlayerUUID
    __type: PlayerType
    __sessions: List[PlayerSession]
    __games: List[GameUUID]

    def __init__(self, uuid: PlayerUUID, type: PlayerType):
        self.__uuid = uuid
        self.__type = type
        self.__sessions = []
        self.__games = []

    @property
    def uuid(self) -> PlayerUUID:
        return self.__uuid

    @property
    def type(self) -> PlayerType:
        return self.__type

    @property
    def games(self) -> List[GameUUID]:
        return self.__games

    def begin_session(self, session: PlayerSession):
        self.__games.append(session.game_uuid)
        self.__sessions.append(session)

    def close_session(self, session: PlayerSession):
        self.__sessions.remove(session)

    def has_session(self, game_uuid: GameUUID=None, socket: any=None) -> bool:
        if game_uuid:
            return any(session.game_uuid == game_uuid for session in self.__sessions)
        elif socket:
            return any(session.socket == socket for session in self.__sessions)

    def get_session(self, game_uuid: GameUUID=None, socket: any=None) -> PlayerSession:
        if game_uuid:
            for session in self.__sessions:
                if session.game_uuid == game_uuid:
                    return session
        elif socket:
            for session in self.__sessions:
                if session.socket == socket:
                    return session

        raise LEMException("Could not find session")
