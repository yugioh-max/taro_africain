from dataclasses import dataclass, field
from abc import ABC
from .card import Card
from .enums import Suit

@dataclass
class Action(ABC):
    player_id: str

@dataclass
class PlayCardAction(Action):
    cards: list[Card]                   # toujours une liste
    declared_suit: Suit | None = None   # obligatoire si on joue un valet

@dataclass
class DrawCardAction(Action):
    pass

@dataclass
class LeaveGameAction(Action):
    pass

@dataclass
class ReconnectAction(Action):
    pass
