import random
from uuid import uuid4
from lobby.models import Tournament, TournamentMatch, TournamentSlot
from lobby.models import Room, RoomPlayer
from accounts.models import User
from game.engine.player import Player
from game.engine.game import Game
from game.engine.game_options import GameOptions
from game.engine.deck import Deck
from game.service.game_service import GameService
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class TournamentService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TournamentService, cls).__new__(cls)
        return cls._instance
    
    def create_tournament(self, host, max_players, jack_blocks_takeit=False, two_wildcard=False):
        while True:
            code = str(uuid4())[:6].upper()
            if Tournament.objects.filter(code=code).exists() == False:
                break

        tournament = Tournament.objects.create(
            code=code,
            host=host,
            max_players=max_players,
            options_json={
                'jack_blocks_takeit': jack_blocks_takeit,
                'two_wildcard':       two_wildcard,
            },
        )

        TournamentSlot.objects.create(
            tournament=tournament,
            user=host,
            is_bot=False,
            position=0,
        )

        return code


    def join_tournament(self, code, user):
        tournament = Tournament.objects.get(code=code)

        if tournament.status != 'waiting':
            raise Exception("Le tournoi a déjà commencé")

        nb_humans = TournamentSlot.objects.filter(
            tournament=tournament,
            is_bot=False
        ).count()

        if nb_humans >= tournament.max_players:
            raise Exception("Tournoi complet")

        slot = TournamentSlot.objects.create(
            tournament=tournament,
            user=user,
            is_bot=False,
            position=nb_humans,
        )

        return slot


    def get_lobby_state(self, code):
        tournament = Tournament.objects.get(code=code)
        slots = TournamentSlot.objects.filter(tournament=tournament, is_bot=False)

        players = [
            {
                "username": slot.user.username,
                "is_host":  slot.user == tournament.host,
            }
            for slot in slots
        ]

        return {
            "code":         tournament.code,
            "max_players":  tournament.max_players,
            "host_id":      str(tournament.host.id),
            "status":       tournament.status,
            "players":      players,
            "empty_slots":  tournament.max_players - len(players),
            "total_bots":   8 - tournament.max_players,
        } 


    def start_tournament(self, code, host):
        tournament = Tournament.objects.get(code=code)

        if tournament.host != host:
            raise Exception("Only host can start tournament")
        
        if tournament.status != 'waiting':
            raise Exception('Tournament has already started')
        
        nb_humans = TournamentSlot.objects.filter(tournament=tournament, is_bot=False).count()
        if nb_humans < tournament.max_players:
            raise Exception("Missing humans players")

        nb_bots = 8 - tournament.max_players
        for i in range(1, nb_bots + 1):
            TournamentSlot.objects.create(
                tournament=tournament,
                is_bot=True,
                bot_label=f"BOT_{i}",
                position=tournament.max_players + i - 1,
            )
        
        tournament.status = 'in_progress'
        tournament.save()

        slots = list(TournamentSlot.objects.filter(tournament=tournament))
        random.shuffle(slots)

        labels = []
        for slot in slots:
            if slot.is_bot:
                labels.append(slot.bot_label)
            else:
                labels.append(str(slot.user.id))

        for i in range(0, len(labels), 2):
            player1_label = labels[i]
            player2_label = labels[i + 1]

            match = TournamentMatch.objects.create(
                tournament=tournament,
                round_number=1,
                player1_label=player1_label,
                player2_label=player2_label,
            )

            is_bot_vs_bot = player1_label.startswith("BOT_") and player2_label.startswith("BOT_")

            if is_bot_vs_bot:
                winner = random.choice([player1_label, player2_label])
                match.winner_label = winner
                match.finished = True
                match.save()
            else:
                self._create_match_room(tournament, match)

    def _create_match_room(self, tournament, match):
        # ===== 1. Construire les 2 joueurs =====
        players    = {}
        turn_order = []
        human_user = None   # on garde un humain pour servir de "host" de la Room

        for label in (match.player1_label, match.player2_label):
            if label.startswith("BOT_"):
                player = Player(id=label, username="🤖 IA")
            else:
                user = User.objects.get(id=label)
                player = Player(id=label, username=user.username)
                human_user = user   # on retient le dernier humain trouvé

            players[label] = player
            turn_order.append(label)

        # ===== 2. Code unique pour cette Room =====
        while True:
            room_code = str(uuid4())[:6].upper()
            if not Room.objects.filter(room_code=room_code).exists():
                break

        # ===== 3. Créer la Room en base =====
        room = Room.objects.create(
            room_code=room_code,
            host=human_user,
            name=f"Tournoi {tournament.code}",
            max_players=2,
            options_json=tournament.options_json,
            bank_json=[], pot_json=[], ranking_json=[],
            current_index=0, takeit_penalty=0,
            is_vs_ai=False,
            is_tournament_match=True,
            started=True,
        )

        # ===== 4. Créer un RoomPlayer pour chaque humain =====
        for i, label in enumerate(turn_order):
            if not label.startswith("BOT_"):
                user = User.objects.get(id=label)
                RoomPlayer.objects.create(
                    user=user,
                    room=room,
                    position=i,
                    connected=True,
                    hand_json=[],
                )

        # ===== 5. Construire le Game en mémoire =====
        options = GameOptions(
            jack_blocks_takeit=tournament.options_json.get('jack_blocks_takeit', False),
            two_wildcard=tournament.options_json.get('two_wildcard', False),
        )
        game = Game(players=players, turn_order=turn_order, options=options, started=True)

        deck = Deck()
        deck.create_deck()
        deck.shuffle()
        deck.distribute(game=game, nb_players=2)

        # ===== 6. Enregistrer dans GameService =====
        service = GameService()
        service._games[room_code] = game

        # ===== 7. Lier ce match à la Room créée =====
        match.room_code = room_code
        match.save()

    def resolve_match(self, room_code, winner_id, loser_id):
        match = TournamentMatch.objects.get(room_code=room_code)
        tournament = match.tournament

        match.winner_label = winner_id
        match.finished = True
        match.save()

        if not loser_id.startswith("BOT_"):
            TournamentSlot.objects.filter(tournament=tournament, user__id=loser_id).update(eliminated=True)
        
        self._check_round_completion(tournament)
        return match

    def _check_round_completion(self, tournament):
        current_round = tournament.current_round if tournament.current_round else 1
        matches = TournamentMatch.objects.filter(
            tournament=tournament,
            round_number=current_round,
        )
        if matches.filter(finished=False).exists():
            return
        
        winners = [m.winner_label for m in matches]

        if len(winners) == 1:
            tournament.status = 'finished'
            if not winners[0].startswith("BOT_"):
                tournament.winner = User.objects.get(id=winners[0])
            tournament.save()
            return
        
        random.shuffle(winners)
        next_round = current_round + 1
        for i in range(0, len(winners), 2):
            p1, p2 = winners[i], winners[i + 1]

            new_match = TournamentMatch.objects.create(
                tournament=tournament,
                round_number=next_round,
                player1_label=p1,
                player2_label=p2,
            )

            if p1.startswith("BOT_") and p2.startswith("BOT_"):
                w = random.choice([p1, p2])
                new_match.winner_label = w
                new_match.finished = True
                new_match.save()
            else:
                self._create_match_room(tournament, new_match)

        tournament.current_round = next_round
        tournament.save()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"tournament_{tournament.code}",
            {
                'type': 'tournament_update',
                'data': {
                    'type': 'next_round_ready',
                    'code': tournament.code,
                }
            }
        )