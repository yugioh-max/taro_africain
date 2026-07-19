from .actions import Action, PlayCardAction, DrawCardAction, LeaveGameAction, ReconnectAction
from .game import Game
from .player import Player
from . import rules as rules

# ==========================================================
# VALIDATION PRINCIPALE
# ==========================================================

def validate_action(game: Game, action: Action) -> bool:
    validate_game_state(game)
    validate_player_exists(game, action.player_id)
    validate_player_turn(game, action.player_id)

    if isinstance(action, PlayCardAction):
        return validate_play_action(game, action)
    if isinstance(action, DrawCardAction):
        return validate_draw_action(game, action)
    if isinstance(action, LeaveGameAction):
        return validate_leave_action(game, action)
    if isinstance(action, ReconnectAction):
        return validate_reconnect_action(game, action)
    return False

# ==========================================================
# ÉTAT GÉNÉRAL
# ==========================================================

def validate_game_state(game: Game):
    if not game.started:
        raise Exception("La partie n'a pas commencé.")
    if game.finished:
        raise Exception("La partie est terminée.")

# ==========================================================
# EXISTENCE DU JOUEUR
# ==========================================================

def validate_player_exists(game: Game, player_id: str):
    if player_id not in game.players:
        raise Exception("Joueur inconnu.")

# ==========================================================
# TOUR DU JOUEUR
# ==========================================================

def validate_player_turn(game: Game, player_id: str):
    current = game.turn_order[game.current_index]
    if current != player_id:
        raise Exception("Ce n'est pas votre tour.")

# ==========================================================
# VALIDATION PLAY
# ==========================================================

def validate_play_action(game: Game, action: PlayCardAction) -> bool:
    player = game.players[action.player_id]
    validate_cards_owned(player, action)
    validate_number_of_cards(action)

    card = action.cards[0]              # FIX : action.cards[0] et non action.card

    # Priorité 1 : pénalité take-it
    if game.takeit_penalty > 0:
        if not rules.valid_takeit_response(card, game.options):
            raise Exception("Vous devez répondre au take-it ou piocher.")
        return True

    # Priorité 2 : couleur imposée
    if game.declared_suit is not None:
        if rules.two_breaks_declared_suit(card, game.options):
            return True
        if not rules.respects_declared_suit(card, game.declared_suit):
            raise Exception("La couleur imposée n'est pas respectée.")
        return True

    # Valet passe-partout
    if rules.is_jack(card):
        return True

    # Joker posé sur carte
    if rules.can_put_joker_on(card, game.pot.top()):
        return True

    # Carte posée sur joker
    if rules.can_play_on_joker(card, game.pot.top()):
        return True

    # Règle normale
    if rules.matches_pot(card, game.pot.top()):
        return True

    # Option two_wildcard
    if game.options.two_wildcard and rules.is_two(card):
        return True

    raise Exception("Carte illégale.")

# ==========================================================
# POSSESSION DES CARTES
# ==========================================================

def validate_cards_owned(player: Player, action: PlayCardAction):
    for card in action.cards:
        if not player.has_card(card):
            raise Exception("Le joueur ne possède pas cette carte.")

# ==========================================================
# NOMBRE DE CARTES
# ==========================================================

def validate_number_of_cards(action: PlayCardAction):
    if len(action.cards) != 1:
        raise Exception("Une seule carte peut être jouée.")

# ==========================================================
# PIOCHE — toujours autorisée
# ==========================================================

def validate_draw_action(game: Game, action: DrawCardAction):
    return True

# ==========================================================
# QUITTER
# ==========================================================

def validate_leave_action(game: Game, action: LeaveGameAction):
    return True

# ==========================================================
# RECONNEXION
# ==========================================================

def validate_reconnect_action(game: Game, action: ReconnectAction):
    if not game.options.allow_reconnect:
        raise Exception("Reconnexion désactivée.")
    return True
