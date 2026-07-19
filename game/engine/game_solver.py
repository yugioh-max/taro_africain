"""
game_solver.py

Solveur du Game à 2 joueurs.
Détermine si le joueur qui répond au Game peut vider
entièrement sa main avant de rendre le tour.
Ne modifie jamais l'état réel du jeu.
"""

from copy import deepcopy
from . import rules as rules

def can_finish_entire_hand(hand, pot_card, declared_suit, takeit_penalty, options):
    """Retourne True si le joueur peut vider entièrement sa main."""
    if rules.is_jack(pot_card):
        declared_suit = None
    return _search(deepcopy(hand), pot_card, declared_suit, takeit_penalty, options)


def _search(hand, pot_card, declared_suit, takeit_penalty, options):
    if len(hand) == 0:
        return True

    for index, card in enumerate(hand):
        if not rules.can_play_virtual(
            card=card,
            pot_card=pot_card,
            declared_suit=declared_suit,
            takeit_penalty=takeit_penalty,
            options=options,
        ):
            continue

        remaining     = hand.copy()
        remaining.pop(index)
        next_pot      = card
        next_declared = declared_suit
        next_penalty  = takeit_penalty

        # Effets de la carte jouée
        if rules.is_seven(card):
            next_penalty += 2
        elif rules.is_joker(card):
            next_penalty += 4
        elif rules.is_jack(card) and options.jack_blocks_takeit and takeit_penalty > 0:
            next_penalty = 0

        if options.two_wildcard and rules.is_two(card):
            next_declared = None

        # L'As à 2 joueurs permet de rejouer
        if rules.grants_extra_turn(card, player_count=2):
            if _search(remaining, next_pot, next_declared, next_penalty, options):
                return True
        else:
            if len(remaining) == 0:
                return True

    return False
