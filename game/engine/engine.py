"""
engine.py
Moteur principal du Taro Africain.
"""

from . import validator as validator
from . import rules as rules
from . import game_solver as game_solver
from .actions import PlayCardAction, DrawCardAction

class Engine:

    def __init__(self, game):
        self.game = game

    # ===================================================
    # API PRINCIPALE
    # ===================================================

    def execute(self, action):
        if self.game.waiting_for_game_response is not None:
            if action.player_id != self.game.waiting_for_game_response:
                raise Exception("En attente de la reponse au game")
            
            if isinstance(action, PlayCardAction):
                self._play(action)
            elif isinstance(action, DrawCardAction):
                self._draw(action)

            return
        
        validator.validate_action(self.game, action)
        if isinstance(action, PlayCardAction):
            self._play(action)
        elif isinstance(action, DrawCardAction):
            self._draw(action)

    # ===================================================
    # JOUE UNE CARTE
    # ===================================================

    def _play(self, action):
        player = self._current_player()
        card   = action.cards[0]            # FIX : .cards[0] et non .card

        player.remove_card(card)
        self.game.pot.push(card)

        # Couleur imposée (valet)
        if rules.is_jack(card):
            self.game.takeit_penalty = 0
            # Si le joueur finit avec le valet, aucune couleur imposée
            self.game.declared_suit = None if player.has_finished() else action.declared_suit
        else:
            self.game.declared_suit = None

        # Take-it
        if rules.is_seven(card):
            self.game.takeit_penalty += 2
        elif rules.is_joker(card):
            self.game.takeit_penalty += 4

        # GAME
        if player.has_finished():
            self._game(player, card)
            return

        self._advance_turn(card)

    # ===================================================
    # PIOCHE
    # ===================================================

    def _draw(self, action):
        player = self._current_player()

        if self.game.takeit_penalty > 0:
            for _ in range(self.game.takeit_penalty):
                player.add_card(self._safe_draw())
            self.game.takeit_penalty = 0
        else:
            player.add_card(self._safe_draw())

        
        self._advance_turn(None)

    # ===================================================
    # GAME
    # ===================================================

    def _game(self, player, last_card):
        # 3 joueurs ou plus
        if len(self.game.turn_order) > 2:
            self.game.ranking.append(player.id)
            self.game.turn_order.remove(player.id)

            if len(self.game.turn_order) == 1:
                self.game.ranking.append(self.game.turn_order[0])
                self.game.finished = True
                return

            self.game.current_index %= len(self.game.turn_order)
            return

        # 2 joueurs
        responder_index = (self.game.current_index + 1) % 2
        responder = self.game.players[self.game.turn_order[responder_index]]

        success = game_solver.can_finish_entire_hand(
            hand=responder.hand,
            pot_card=last_card,
            declared_suit=self.game.declared_suit,
            takeit_penalty=self.game.takeit_penalty,
            options=self.game.options,
        )
        if success:
            for _ in range(3):
                player.add_card(self._safe_draw())

            for _ in range(3):
                responder.add_card(self._safe_draw())
            
            self.game.declared_suit = None
            self.game.takeit_penalty = 0
            self.game.current_index = responder_index
            return
        
        self.game.ranking.append(player.id)
        self.game.ranking.append(responder.id)
        self.game.finished = True

    # ===================================================
    # JOUEUR COURANT
    # ===================================================

    def _current_player(self):
        pid = self.game.turn_order[self.game.current_index]
        return self.game.players[pid]

    # ===================================================
    # AVANCER LE TOUR
    # ===================================================

    def _advance_turn(self, last_card):
        # As à 2 joueurs → le même joueur rejoue
        if last_card is not None and rules.is_ace(last_card):
            if len(self.game.turn_order) == 2:
                return              # current_index inchangé
            step = 2                # As à 3+ → saute un joueur
        else:
            step = 1

        self.game.current_index = (
            self.game.current_index + step
        ) % len(self.game.turn_order)

    def _safe_draw(self):
        """Pioche une carte, recycle le pot automatiquement si la banque est vide"""
        if self.game.bank.is_empty():
            recycled = self.game.pot.keep_top_and_take_rest()
            if recycled:
                self.game.bank.add_many(recycled)
                self.game.bank.shuffle()
        return self.game.bank.draw()
