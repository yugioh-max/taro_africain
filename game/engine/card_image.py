
from .enums import Suit, Rank


SUIT_NAMES = {
    Suit.HEART: 'heart',
    Suit.DIAMOND: 'diamond',
    Suit.SPADE: 'spade',
    Suit.CLUB: 'club',
}

RANK_NAMES = {
    Rank.ACE   : "1",
    Rank.TWO   : "2",
    Rank.THREE : "3",
    Rank.FOUR  : "4",
    Rank.FIVE  : "5",
    Rank.SIX   : "6",
    Rank.SEVEN : "7",
    Rank.EIGHT : "8",
    Rank.NINE  : "9",
    Rank.TEN   : "10",
    Rank.JACK  : "jack",
    Rank.QUEEN : "queen",
    Rank.KING  : "king",
}

def card_to_image(card):
    """Retourne le nom du PNG correspondant a une carte"""

    if card.rank == Rank.JOKER:
        if card.suit in (Suit.HEART, Suit.DIAMOND):
            return 'joker_red.png'
        return 'joker_black.png'

    suit = SUIT_NAMES[card.suit] 
    rank = RANK_NAMES[card.rank]

    return f"{suit}_{rank}.png"
