from dataclasses import dataclass, field
from .player import Player
from .bank import Bank
from .pot import Pot
from .game_options import GameOptions
from .enums import Suit

@dataclass
class Game:
    players:      dict[str, Player] = field(default_factory=dict)
    turn_order:   list[str]         = field(default_factory=list)
    current_index: int              = 0
    bank:         Bank              = field(default_factory=Bank)
    pot:          Pot               = field(default_factory=Pot)
    options:      GameOptions       = field(default_factory=GameOptions)

    # Effets temporaires
    takeit_penalty: int             = 0
    declared_suit:  Suit | None     = None

    # Fin de partie
    ranking:  list[str] = field(default_factory=list)
    started:  bool      = False
    finished: bool      = False
    waiting_for_game_response: str|None = None

    @property
    def active_players(self) -> list[str]:
        return [pid for pid in self.turn_order]

    @property
    def current_player_id(self) -> str:
        return self.turn_order[self.current_index]
