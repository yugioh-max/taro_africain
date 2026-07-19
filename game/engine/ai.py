from . import rules
from .enums import Suit


def get_legal_moves(player, game) -> list:
    pot_card = game.pot.top()
    legal = []
    for card in player.hand:
        if rules.can_play_virtual(
            card=card,
            pot_card=pot_card,
            declared_suit=game.declared_suit,
            takeit_penalty=game.takeit_penalty,
            options=game.options,
        ):
            legal.append(card)
    return legal


def _score_card(card, bot, game) -> int:
    score = 0
    if game.takeit_penalty > 0:
        score += rules.takeit_value(card) * 10
    if len(bot.hand) <= 3:
        if rules.is_takeit(card) or rules.is_jack(card) or rules.is_ace(card):
            score += 5
    if card.suit:
        score += sum(1 for c in bot.hand if c.suit == card.suit)
    return score


def choose_declared_suit(bot):
    counts = {suit: 0 for suit in Suit}
    for card in bot.hand:
        if card.suit in counts:
            counts[card.suit] += 1
    return min(counts, key=lambda s: counts[s])


def choose_move(game, bot):
    legal_moves = get_legal_moves(bot, game)
    if not legal_moves:
        return None
    return max(legal_moves, key=lambda card: _score_card(card, bot, game))


