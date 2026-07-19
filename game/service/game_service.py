
from uuid import uuid4
from game.engine.game_options import GameOptions
from lobby.models import Room, RoomPlayer
from accounts.models import User
from game.engine.player import Player
from game.engine.game import Game
from game.engine.deck import Deck
from game.engine.actions import PlayCardAction, DrawCardAction
from game.engine.engine import Engine
from game.engine.card import Card
from game.engine import ai
from game.engine import rules
from game.engine.card_image import card_to_image

class GameService:
    _instance = None
    _games = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GameService, cls).__new__(cls)
        return cls._instance

    def create_game(self, host, name, max_players=5, 
                    is_private=False, password=None, is_vs_ai=False,
                    jack_blocks_takeit=False, two_wildcard=False):
        while True:
            code = str(uuid4())[:6].upper()
            if Room.objects.filter(room_code=code).exists() == False:
                room = Room.objects.create(
                        room_code=code,
                        is_vs_ai=is_vs_ai, 
                        host=host, 
                        name=name, 
                        is_private=is_private, 
                        password=password, 
                        max_players=max_players,
                        options_json={
                            "jack_blocks_takeit": jack_blocks_takeit,
                            "two_wildcard": two_wildcard,
                        },
                        current_index=0,
                        takeit_penalty=0,
                        bank_json=[],
                        pot_json=[],
                        ranking_json=[],
                )
                RoomPlayer.objects.create(
                    user=host, 
                    room=room, 
                    position=0,
                    connected=True,
                    hand_json=[]
                )
                return code

    def join_game(self, room_code, user, password=None):
        room = Room.objects.get(room_code=room_code)
        if room.started == True:
            raise Exception("game has already started")
    
        if room.is_private:
            if password != room.password:
                raise Exception("incorrect password")
        
        nb_players = RoomPlayer.objects.filter(room=room).count()
        if nb_players >= room.max_players:
            raise Exception("room is full")
        else:
            room_player = RoomPlayer.objects.create(user=user, room=room, position=nb_players, connected=True)
            return room_player

    def start_game(self, room_code, host):
        room = Room.objects.get(room_code=room_code)
        if room.host != host:
            raise Exception("Only host can start game")
        
        if room.started:
            raise Exception("game has already started")
        
        nb_players = RoomPlayer.objects.filter(room=room).count()
        if not room.is_vs_ai and nb_players < 2:
            raise Exception("a game must have more than 02 players")
        
        room_players = RoomPlayer.objects.filter(room=room).order_by('position')
        players = {}
        turn_order = []

        for rp in room_players:
            player = Player(id= str(rp.user.id), username=rp.user.username)
            players[str(rp.user.id)] = player
            turn_order.append(str(rp.user.id))

        if room.is_vs_ai:
            nb_bots = room.max_players - len(turn_order)
            for i in range(1, nb_bots + 1):
                bot_id = f"BOT_{i}"
                players[bot_id] = Player(id=bot_id, username=f"IA {i}", is_bot=True)
                turn_order.append(bot_id)
            
            nb_players = room.max_players
        else:
            nb_players = len(turn_order)
            if nb_players < 2:
                raise Exception("A game must have more than 02 players")
        
        options = GameOptions(
            jack_blocks_takeit=room.options_json.get('jack_blocks_takeit', False),
            two_wildcard=room.options_json.get('two_wildcard', False),
        )
        game = Game(players=players, turn_order=turn_order, options=options, started=True)
        deck = Deck()
        deck.create_deck()
        deck.shuffle()
        deck.distribute(game=game, nb_players=nb_players)
        self._games[room_code] = game
        room.started = True
        room.save()
        return game


    def play(self, room_code, player:Player, card:Card, declared_suit=None):
        game = self._games.get(room_code)
        if game is None:
            raise Exception("game not found")
        
        engine = Engine(game=game)
        engine.execute(action=PlayCardAction(cards=[card], declared_suit=declared_suit, player_id=str(player.id)))

        while True:
            current = game.players[game.current_player_id]
            if not getattr(current, "is_bot", False):
                break

            bot_card = ai.choose_move(game, current)
            if bot_card is None:
                engine.execute(action=DrawCardAction(player_id=current.id))
                continue

            if rules.is_jack(bot_card):
                suit = ai.choose_declared_suit(current)
                engine.execute(action=PlayCardAction(cards=[bot_card], declared_suit=suit, player_id=current.id))
            else:
                engine.execute(action=PlayCardAction(cards=[bot_card], player_id=current.id))

        self._save_state(room_code=room_code, game=game)
        return game

    def draw(self, room_code, player:Player):
        game = self._games.get(room_code)
        if game is None:
            raise Exception("game not found")
        
        engine = Engine(game=game)
        engine.execute(action=DrawCardAction(player_id=str(player.id)))
        
        while True:
            current = game.players[game.current_player_id]
            if not getattr(current, "is_bot", False):
                break

            bot_card = ai.choose_move(game, current)
            if bot_card is None:
                engine.execute(action=DrawCardAction(player_id=current.id))
                continue

            if rules.is_jack(bot_card):
                suit = ai.choose_declared_suit(current)
                engine.execute(action=PlayCardAction(cards=[bot_card], declared_suit=suit, player_id=current.id))
            else:
                engine.execute(action=PlayCardAction(cards=[bot_card], player_id=current.id))

        self._save_state(room_code=room_code, game=game)
        return game

    
    def get_state(self, room_code, player_id=None):
        game = self._games.get(room_code)
        if game is None:
            raise Exception("game not found")
        
        player = game.players[game.current_player_id]
        top_card = game.pot.top()
        room = Room.objects.get(room_code=room_code)

        state = {
            'current_player': game.current_player_id,
            'current_player_username': game.players[game.current_player_id].username,
            'takeit_penalty': game.takeit_penalty,
            'declared_suit': game.declared_suit.value if game.declared_suit else None,
            'pot': {'rank': top_card.rank.value, 'suit': top_card.suit.value, "image":card_to_image(top_card)},
            'finished': game.finished,
            'ranking': game.ranking,
            'is_tournament_match': room.is_tournament_match,
            'bank_count': game.bank.count(),
            'players': [
                {
                    'id': pid,
                    'username': game.players[pid].username,
                    'nb_cards': game.players[pid].card_count(),
                }
                for pid in game.turn_order
            ],
        }

        #AAjouter la main du joueur
        if player_id and player_id in game.players:
            
            player = game.players[player_id]
            state['my_hand'] = [
                {
                    'rank': card.rank.value,
                    'suit': card.suit.value,
                    'image': card_to_image(card),
                }
                for card in player.hand
            ]
        
        return state

    def end_game(self, room_code):
        game = self._games.get(room_code)
        room = Room.objects.get(room_code=room_code)
        if game is None:
            raise Exception("game not found")
        
        del self._games[room_code]
        room.finished = True
        room.save()
        
        for position, player_id in enumerate(game.ranking):
            if player_id.startswith("BOT_"):
                continue

            user = User.objects.get(id=player_id)
            user.games_played += 1
            if position == 0:
                user.games_won += 1
            
            user.save()



    def _save_state(self, room_code, game:Game):
        room = Room.objects.get(room_code=room_code)

        room.current_index = game.current_index
        room.takeit_penalty = game.takeit_penalty
        room.finished = game.finished
        room.declared_suit = game.declared_suit.value if game.declared_suit else None

        room.bank_json = self.convert_state_game_to_JSON(cards=game.bank._cards)
        room.pot_json = self.convert_state_game_to_JSON(cards=game.pot._cards)
        room.ranking_json = game.ranking
        room.save()

        for player_id, player in game.players.items():
            if player_id.startswith("BOT_"):
                continue

            rp = RoomPlayer.objects.get(room=room, user__id=player_id)
            rp.hand_json = self.convert_state_game_to_JSON(cards=player.hand)
            rp.save()


    def convert_state_game_to_JSON(self, cards:list[Card]):
        cards_json = []
        
        for card in cards:
            cards_json.append({
                "rank": card.rank.value,
                "suit": card.suit.value
            })

        return cards_json