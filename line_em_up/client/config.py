from dataclasses import dataclass
from dataclasses_json import dataclass_json
from ..common import PlayerID, PlayerType, GameUUID

@dataclass_json
@dataclass
class ClientConfig:
    url: str
    player_id: PlayerID
    player_type: PlayerType
    game_uuid: GameUUID
