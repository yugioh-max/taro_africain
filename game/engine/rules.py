from .card import Card
from .enums import Rank, Suit

# ==========================================================
# TESTS ÉLÉMENTAIRES
# ==========================================================

def is_ace(card: Card) -> bool:
    return card.rank == Rank.ACE

def is_jack(card: Card) -> bool:
    return card.rank == Rank.JACK

def is_seven(card: Card) -> bool:
    return card.rank == Rank.SEVEN

def is_joker(card: Card) -> bool:
    return card.rank == Rank.JOKER

def is_two(card: Card) -> bool:       # ← FIX : manquait, utilisé dans game_solver
    return card.rank == Rank.TWO

def is_takeit(card: Card) -> bool:
    return is_seven(card) or is_joker(card)

# ==========================================================
# COULEUR
# ==========================================================

def is_red(card: Card) -> bool:
    return card.suit in (Suit.HEART, Suit.DIAMOND)

def is_black(card: Card) -> bool:
    return card.suit in (Suit.SPADE, Suit.CLUB)

# ==========================================================
# VALEUR DE LA PÉNALITÉ
# ==========================================================

def takeit_value(card: Card) -> int:
    if is_seven(card): return 2
    if is_joker(card): return 4
    return 0

# ==========================================================
# RÈGLE NORMALE
# ==========================================================

def matches_pot(card: Card, pot_card: Card) -> bool:
    return card.rank == pot_card.rank or card.suit == pot_card.suit

# ==========================================================
# JOKER
# ==========================================================

def can_play_on_joker(card: Card, joker: Card) -> bool:
    """Une carte normale peut-elle se poser sur un joker au pot ? (R11)"""
    if not is_joker(joker):
        return False
    return is_red(card) if is_red(joker) else is_black(card)

def can_put_joker_on(card: Card, pot_card: Card) -> bool:
    """Un joker peut-il se poser sur la carte au pot ? (R11)"""
    if not is_joker(card):
        return False
    return is_red(pot_card) if is_red(card) else is_black(pot_card)

# ==========================================================
# COULEUR IMPOSÉE
# ==========================================================

def respects_declared_suit(card: Card, declared_suit: Suit) -> bool:
    if is_jack(card):
        return True
    if is_joker(card):
        return is_red(card) if declared_suit in (Suit.HEART, Suit.DIAMOND) else is_black(card)
    return card.suit == declared_suit

def two_breaks_declared_suit(card: Card, options) -> bool:
    """R32.2 — Le 2 casse une couleur imposée par un valet."""
    return options.two_wildcard and is_two(card)

def clears_declared_suit(card: Card, options) -> bool:
    return options.two_wildcard and is_two(card)

# ==========================================================
# RÉPONSE À UNE PÉNALITÉ
# ==========================================================

def valid_takeit_response(card: Card, options) -> bool:
    if is_takeit(card):
        return True
    if options.jack_blocks_takeit and is_jack(card):
        return True
    return False

# ==========================================================
# EFFET DE L'AS
# ==========================================================

def ace_keeps_turn(active_players: int) -> bool:
    return active_players == 2

def ace_skips_next(active_players: int) -> bool:
    return active_players >= 3

def grants_extra_turn(card: Card, player_count: int) -> bool:
    return is_ace(card) and player_count == 2

# ==========================================================
# FIN SUR UN AS
# ==========================================================

def can_finish_with_last_card(card: Card, active_players: int) -> bool:
    """R27/R28 — Peut-on terminer la partie avec cette carte ?"""
    if not is_ace(card):
        return True
    return active_players >= 3

# ==========================================================
# PIOCHE
# ==========================================================

def draw_amount(takeit_penalty: int) -> int:
    return takeit_penalty if takeit_penalty > 0 else 1

# ==========================================================
# CAN_PLAY_VIRTUAL — version sans état pour game_solver
# ==========================================================

def can_play_virtual(
    card: Card,
    pot_card: Card,
    declared_suit,
    takeit_penalty: int,
    options,
) -> bool:
    """
    FIX : fonction manquante utilisée par game_solver.
    Même logique que validator mais sans lever d'exception.
    """
    # Priorité 1 : pénalité en cours
    if takeit_penalty > 0:
        return valid_takeit_response(card, options)

    # Priorité 2 : couleur imposée
    if declared_suit is not None:
        if is_jack(card):
            return True
        if two_breaks_declared_suit(card, options):
            return True
        return respects_declared_suit(card, declared_suit)

    # Règle normale
    if is_jack(card):
        return True
    if is_joker(card):
        return can_put_joker_on(card, pot_card)
    if options.two_wildcard and is_two(card):
        return True
    if matches_pot(card, pot_card):
        return True
    if can_play_on_joker(card, pot_card):
        return True

    return False
