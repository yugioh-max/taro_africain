

from .enums import Rank, Suit
from .card import Card
from random import shuffle as random_shuffle
from .game import Game



class Deck:
    def __init__(self):
        self._cards = []

    def create_deck(self):
        for suit in Suit:
            for rank in Rank:
                if rank == Rank.JOKER: continue
                card = Card(rank=rank, suit=suit)
                self._cards.append(card)
        
        self._cards.append(Card(rank=Rank.JOKER, suit=Suit.HEART))
        self._cards.append(Card(rank=Rank.JOKER, suit=Suit.SPADE))
        return self._cards
    
    def shuffle(self):
        random_shuffle(self._cards)

    def distribute(self, game:Game, nb_players:int):
        nb_cards = 5 if nb_players == 2 else 4
        for player_id in game.turn_order:
            player = game.players[player_id]
            for _ in range(nb_cards):
                card = self._cards.pop()
                player.add_card(card)
        
        skipped = []
        pot_card = None
        while True:
            card = self._cards.pop()
            if card.rank in (Rank.ACE, Rank.JACK, Rank.SEVEN, Rank.JOKER):
                skipped.append(card)
            else:
                pot_card = card
                break
        
        for c in reversed(skipped):
            self._cards.insert(0, c)
        
        game.pot.push(pot_card)
        game.bank.add_many(self._cards)