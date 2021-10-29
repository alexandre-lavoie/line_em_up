from dataclasses import dataclass
from dataclasses_json import dataclass_json
from ..common import PlayerUUID, PlayerType, GameUUID

@dataclass_json
@dataclass
class ClientConfig:
    url: str
    player_name: PlayerUUID
    player_type: PlayerType
    game_id: GameUUID

@dataclass_json
@dataclass
class PoolConfig:
    url: str
    player_name: PlayerUUID
    pool_count: int
