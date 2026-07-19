"""Il recoit les messages du navigateur
    Appelle GameService
    charger le nouvelle etat a tous les joueurs de la salle
"""
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from lobby.models import RoomPlayer
from game.engine.enums import Rank, Suit
from game.engine import rules, ai
from lobby.models import Room, Tournament

from game.engine.card import Card
from game.service.game_service import GameService
from game.service.tournament_service import TournamentService
import asyncio
import json

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
       #recuperer le room_code de la salle
       self.room_code = self.scope['url_route']['kwargs']['room_code']
       self.group_name = f"game_{self.room_code}"

       #Rejoindre le group
       await self.channel_layer.group_add(self.group_name, self.channel_name)

       #Accepter la connexion
       await self.accept()

       await self._set_player_connected()

    @database_sync_to_async
    def _set_player_connected(self):
        RoomPlayer.objects.filter(room__room_code=self.room_code, user=self.scope['user']).update(connected=True)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self._set_player_disconnected()

    @database_sync_to_async
    def _set_player_disconnected(self):
        RoomPlayer.objects.filter(room__room_code=self.room_code, user=self.scope['user']).update(connected=False)
    
    async def receive(self, text_data = None):
        data = json.loads(text_data)
        action = data.get('action')
        try:
            if action == 'play':
                game = await self._handle_play(data)
                await self._broadcast_state(game)
                if game.finished:
                    tournament_code = await self._resolve_tournament_if_needed(game)
                    if tournament_code:
                        await self._notify_tournament_players(game, tournament_code)
                    else:
                        await self._end_game()
                else:
                    await self._play_bot_turns_if_needed(game)

            elif action == 'draw':
                game = await self._handle_draw(data)
                await self._broadcast_state(game)
                if game.finished:
                    tournament_code = await self._resolve_tournament_if_needed(game)
                    if tournament_code:
                        await self._notify_tournament_players(game, tournament_code)
                    else:
                        await self._end_game()
                else:
                    await self._play_bot_turns_if_needed(game)

            elif action == 'get_state':
                await self._send_state_to_player()
                game = await self._get_game()
                if game and not game.finished:
                    await self._play_bot_turns_if_needed(game)

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e),
            }))
        
    @database_sync_to_async
    def _end_game(self):
        service = GameService()
        service.end_game(self.room_code)

    @database_sync_to_async
    def _handle_play(self, data):
        user = self.scope['user']
        rank = Rank(data['rank'])
        suit = Suit(data['suit'])
        card=Card(rank=rank, suit=suit)
        if data.get('declared_suit'):
            declared_suit = Suit(data['declared_suit'])
        else:
            declared_suit=None
        
        service = GameService()
        return service.play(
            room_code=self.room_code,
            player=user,
            card=card,
            declared_suit=declared_suit
        )
        

    @database_sync_to_async
    def _handle_draw(self, data):
        user = self.scope['user']
        service = GameService()
        return service.draw(
            room_code=self.room_code,
            player=user   
        )
        

    async def _broadcast_state(self, game):
        service = GameService()
        for pid in game.players.keys():
            personal_state =  await self._get_state_for(pid=pid)

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'game_update',
                    'data': personal_state,
                    'player_id': pid,
                }
            )

    @database_sync_to_async
    def _get_state_for(self, pid):
        service = GameService()
        return service.get_state(self.room_code, player_id=pid)

    async def game_update(self, event):
        #Envoiyer uniquement si c'est ce joueur
        current_user_id = str(self.scope['user'].id)

        if event.get('player_id') is None:
            await self.send(text_data=json.dumps(event['data']))
            return
        
        if event.get('player_id') == current_user_id:
            await self.send(text_data=json.dumps(event['data']))
            return
        
        #message de fin du tournoi
        msg_type = event['data'].get('type', '')
        if msg_type in ('tournament_match_finished', 'tournament_finished'):
            return
    
        #Envoi l'etat sans la main
        data = event['data'].copy()
        data.pop('my_hand', None)
        await self.send(text_data=json.dumps(data))

       

    async def _send_state_to_player(self):
        player_id = str(self.scope['user'].id)
        state = await self._get_personal_state(player_id)
        await self.send(text_data=json.dumps(state))

    @database_sync_to_async
    def _get_personal_state(self, player_id):
        service = GameService()
        return service.get_state(
            room_code=self.room_code,
            player_id=player_id,
        )
    
    async def _play_bot_turns_if_needed(self, game):
        while not game.finished and game.current_player_id.startswith("BOT_"):
            await asyncio.sleep(1)
            game = await self._handle_bot_turn(game)
            await self._broadcast_state(game)
            if game.finished:
                tournament_code = await self._resolve_tournament_if_needed(game)
                if tournament_code:
                    await self._notify_tournament_players(game=game, tournament_code=tournament_code)
                else:
                    await self._end_game()
        return game
    
    @database_sync_to_async
    def _handle_bot_turn(self, game):
        bot = game.players[game.current_player_id]
        service = GameService()
        card = ai.choose_move(game, bot)

        if card is None:
            return service.draw(room_code=self.room_code, player=bot)
        
        declared_suit = ai.choose_declared_suit(bot) if rules.is_jack(card) else None
        return service.play(room_code=self.room_code, player=bot, card=card, declared_suit=declared_suit)
    
    @database_sync_to_async
    def _get_game(self):
        service = GameService()
        return service._games.get(self.room_code)
    
    @database_sync_to_async
    def _resolve_tournament_if_needed(self, game):
        room = Room.objects.get(room_code=self.room_code)

        if not room.is_tournament_match:
            return None
        
        winner_id = game.ranking[0]
        loser_id = game.ranking[1]

        service = TournamentService()
        match = service.resolve_match(room_code=self.room_code, winner_id=winner_id, loser_id=loser_id)
        return match.tournament.code
    
    async def _notify_tournament_players(self, game, tournament_code):
        tournament = await self._get_tournament(tournament_code)
        is_finale = tournament.status == 'finished'

        #Le vrai gagnant est toujours ranking[0], bot ou humain
        actual_winner = str(game.ranking[0])

        for pid in list(game.players.keys()):
            pid_str = str(pid)
            if pid_str.startswith("BOT_"): 
                continue

            if pid_str == actual_winner:
                #Cet humain a gagné
                if is_finale:
                    
                    msg = {
                        'type': 'tournament_finished',
                        'winner_id': pid_str,
                        'code': tournament_code,
                        'is_winner' : True,
                    }  
                else:

                    msg = {
                        'type': 'tournament_match_finished',
                        'tournament_code': tournament_code,
                        'result' : 'win',
                    }
            else: 
                #cet humain a perdu
                msg = {
                    'type': 'tournament_match_finished',
                    'result' : 'lose',
                }

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'game_update',
                    'data': msg,
                    'player_id': pid_str,           
                }
            )
    
    @database_sync_to_async
    def _get_tournament(self, code):
        return Tournament.objects.get(code=code)