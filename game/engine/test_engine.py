"""
test_engine.py
Batterie de tests du moteur Taro Africain.
"""

from PYTHON.ARC_V_PROJECT.game.engine.enums import Rank, Suit
from PYTHON.ARC_V_PROJECT.game.engine.card import Card
from PYTHON.ARC_V_PROJECT.game.engine.player import Player
from PYTHON.ARC_V_PROJECT.game.engine.game import Game
from PYTHON.ARC_V_PROJECT.game.engine.engine import Engine
from PYTHON.ARC_V_PROJECT.game.engine.actions import PlayCardAction, DrawCardAction
from PYTHON.ARC_V_PROJECT.game.engine.game_options import GameOptions

# =====================================================
# OUTILS
# =====================================================

tests   = 0
success = 0

def check(condition, message):
    global tests, success
    tests += 1
    if condition:
        success += 1
        print("✅", message)
    else:
        print("❌", message)

def resume():
    print()
    print("==============================")
    print(f"{success} / {tests} tests réussis")
    print("==============================")

# =====================================================
# FABRIQUE UNE PARTIE
# =====================================================

def create_game(nb_players=2):
    players = {}
    order   = []
    for i in range(nb_players):
        pid = f"J{i+1}"
        players[pid] = Player(id=pid, username=pid)   # FIX : Player est un dataclass
        order.append(pid)

    game = Game(
        players=players,
        turn_order=order,
        options=GameOptions(),
        started=True,
    )
    game.current_index = 0
    return game



game = create_game()
engine = Engine(game)
game.players["J1"].hand = [Card(Rank.JACK, Suit.SPADE), Card(Rank.SEVEN, Suit.HEART)]
game.pot.push(Card(Rank.THREE, Suit.HEART)) 
game.options.jack_blocks_takeit = False
game.bank.add(Card(Rank.EIGHT, Suit.DIAMOND))

engine.execute(DrawCardAction(player_id="J1"))
for i in game.players["J1"].hand:
    print(  i)


print(game.pot)



