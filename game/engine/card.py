from dataclasses import dataclass
from .enums import Suit, Rank

@dataclass(frozen=True)
class Card:
    rank: Rank          # ← rank TOUJOURS en premier
    suit: Suit | None   # None interdit en pratique mais garde la flexibilité

    def __str__(self):
        if self.rank == Rank.JOKER:
            color = "Rouge" if self.suit in (Suit.HEART, Suit.DIAMOND) else "Noir"
            return f"JOKER {color}"
        return f"{self.rank.value} of {self.suit.value}"
