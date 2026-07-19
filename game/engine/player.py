from dataclasses import dataclass, field
from .card import Card


@dataclass                          # ← FIX : @dataclass manquait
class Player:
    id:         str
    username:   str
    hand:       list[Card] = field(default_factory=list)
    connected:  bool = True
    abandoned:  bool = False
    is_bot: bool = False

    def add_card(self, card: Card):
        self.hand.append(card)

    def add_cards(self, cards: list[Card]):
        self.hand.extend(cards)

    def remove_card(self, card: Card):
        self.hand.remove(card)

    def has_card(self, card: Card) -> bool:
        return card in self.hand

    def card_count(self) -> int:
        return len(self.hand)

    def is_check(self) -> bool:
        """Le joueur n'a plus qu'une carte (Check !)"""
        return len(self.hand) == 1

    def has_finished(self) -> bool:
        return len(self.hand) == 0

    def disconnect(self):
        self.connected = False

    def abandon(self):
        self.abandoned = True

    def __str__(self):
        return self.username
