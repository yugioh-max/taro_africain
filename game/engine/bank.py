from .card import Card
from random import shuffle
from .exceptions import EmptyBankError

class Bank:
    """Représente la banque de pioche."""

    def __init__(self):
        self._cards: list[Card] = []

    def add(self, card: Card):
        self._cards.append(card)

    def add_many(self, cards: list[Card]):
        self._cards.extend(cards)

    def shuffle(self):
        shuffle(self._cards)

    def draw(self) -> Card:
        if self.is_empty():
            raise EmptyBankError("La banque est vide.")
        return self._cards.pop()

    def count(self) -> int:
        return len(self._cards)

    def is_empty(self) -> bool:
        return len(self._cards) == 0

    def clear(self):
        self._cards.clear()

    def __str__(self):
        return f"Bank({self.count()} cartes)"
