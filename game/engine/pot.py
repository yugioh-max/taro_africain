from .card import Card
from .exceptions import EmptyBankError

class Pot:

    def __init__(self):
        self._cards: list[Card] = []

    def push(self, card: Card):
        self._cards.append(card)

    def top(self) -> Card:
        if self.is_empty():
            raise EmptyBankError("Le pot est vide.")
        return self._cards[-1]

    def pop(self) -> Card:
        if self.is_empty():
            raise EmptyBankError("Le pot est vide.")
        return self._cards.pop()

    def is_empty(self) -> bool:
        return len(self._cards) == 0

    def count(self) -> int:
        return len(self._cards)

    def keep_top_and_take_rest(self) -> list[Card]:
        """Conserve la carte visible et retourne les autres (pour reconstruire la banque)."""
        if len(self._cards) <= 1:
            return []
        cards = self._cards[:-1]
        self._cards = [self._cards[-1]]
        return cards

    def clear(self):
        self._cards.clear()

    def __str__(self):
        if self.is_empty():
            return "Pot vide"
        return f"Pot({self.top()})"
