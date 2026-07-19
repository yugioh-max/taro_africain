

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from game.service.game_service import GameService
from lobby.models import Room, RoomPlayer, TournamentSlot
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from game.service.tournament_service import TournamentService, Tournament, TournamentMatch
from accounts.models import User

# Create your views here.
def label_to_name(label):
    if label.startswith("BOT_"):
        return "IA"
    try:
        return User.objects.get(id=label).username
    except:
        return label
            

@login_required
def create_room_views(request): #Formulaire de creation de salle
    if request.method == 'POST':
        name = request.POST['name']
        max_players = int(request.POST['max_players'])
        is_private = request.POST.get('is_private') == 'on'
        password = request.POST.get('password', None)

        service = GameService()
        room_code = service.create_game(
            host=request.user,
            name=name,
            max_players=max_players,
            is_private=is_private,
            password=password,
            jack_blocks_takeit=request.POST.get('jack_blocks_takeit') == 'on',
            two_wildcard=request.POST.get('two_wildcard') == 'on',
            is_vs_ai=request.POST.get('is_vs_ai') == 'on',
        )
        return redirect('room_lobby', room_code=room_code)
    
    return render(request, 'create_room.html')

@login_required
def join_room_views(request): #Joindre une salle
    if request.method == 'POST':
        room_code = request.POST['room_code']
        password = request.POST.get('password', None)
        service = GameService()
        try:
            service.join_game(
                room_code=room_code,
                user=request.user,
                password=password,
            )
            channel_layer = get_channel_layer()

            #recuperer la liste mise a jour des joueurs
            room = Room.objects.get(room_code=room_code)
            players = RoomPlayer.objects.filter(room=room)
            players_data = [
                {
                    'username': rp.user.username,
                    'is_host': rp.user == room.host,
                }
                for rp in players
            ]

            #Envoyer a tousles joueurs du groupe
            async_to_sync(channel_layer.group_send)(
                f"lobby_{room_code}",
                {
                    'type': 'lobby_update',
                    'data':{
                        'type':'lobby_update',
                        'players':players_data,
                    }
                }
            )
            return redirect('room_lobby', room_code=room_code)
        except Exception as e:
            #Récupérer les salles dispo
            rooms = Room.objects.filter(started=False, is_vs_ai=False)
            return render(request, 'join_room.html', {'rooms': rooms, 'error': str(e)})
        
    rooms = Room.objects.filter(started=False, is_vs_ai=False)
    return render(request, 'join_room.html', {'rooms': rooms})
    


@login_required
def room_lobby_view(request, room_code): #page d'attente lorsqu'on rejoint la salle
    room=Room.objects.get(room_code=room_code)
    players = RoomPlayer.objects.filter(room=room)
    empty_slots = range(room.max_players - players.count())

    return render(request, 'room_lobby.html', {
        'room': room,
        'room_code': room_code,
        'players': players,
        'room_code': room_code,
        'is_host': room.host == request.user,
        'empty_slots': empty_slots,
        })

def start_game_view(request, room_code):
    if request.method == 'POST':
        try:
           service = GameService()
           service.start_game(
               room_code=room_code,
               host=request.user
           )
           #Notifier tous les joueurs
           channel_layer = get_channel_layer()
           async_to_sync(channel_layer.group_send)(
               f"lobby_{room_code}",
               {
                   'type': 'lobby_update',
                   'data': {
                       'type': 'game_started',
                       'room_code': room_code,
                   }
               }
           )
        except Exception as e:
           return redirect('room_lobby', room_code=room_code)
        
    return redirect('room_lobby', room_code=room_code)

@login_required
def leave_room_view(request, room_code):
    room = Room.objects.get(room_code=room_code)

    #Cas1 : c'est le host
    if room.host == request.user:
        #Notifier les joueurs
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"lobby_{room_code}",
            {
                'type':'lobby_update',
                'data': {
                    'type': 'host_left',
                    'message': 'Le host a quitté la salle'
                }
            }
        )
        #supprimer la salle
        room.delete()
        return redirect('home')
    
    #cas2: joueur normal
    RoomPlayer.objects.filter(room=room, user=request.user).delete()

    #notifier les autres
    channel_layer = get_channel_layer()
    players = RoomPlayer.objects.filter(room=room)
    players_data = [
        {
            'username': rp.user.username,
            'is_host': rp.user == room.host,
        }
        for rp in players
    ]
    async_to_sync(channel_layer.group_send)(
        f"lobby_{room_code}",
        {
            'type': 'lobby_update',
            'data':{
                'type': 'lobby_update',
                'players': players_data,
            }
        }
    )
    return redirect('home')

@login_required
def update_options_view(request, room_code):
    if request.method == 'POST':
        room = Room.objects.get(room_code=room_code)
        if room.host != request.user:
            return redirect('room_lobby', room_code=room_code)
        
        room.options_json = {
            'jack_blocks_takeit': request.POST.get('jack_blocks_takeit') == 'on',
            'two_wildcard': request.POST.get('two_wildcard') == 'on',
        }
        room.save()

        return redirect('room_lobby', room_code=room_code)
    
    redirect('room_lobby', room_code=room_code)

@login_required
def ai_room_view(request):
    if request.method == 'POST':
        max_players = int(request.POST['max_players'])
        jack_blocks_takeit = request.POST.get('jack_blocks_takeit') == 'on'
        two_wildcard = request.POST.get('two_wildcard') == 'on'

        service = GameService()
        try:
            room_code = service.create_game(
                host = request.user,
                name="Partie VS IA",
                max_players=max_players,
                is_private=True,
                password=None,
                jack_blocks_takeit=jack_blocks_takeit,
                two_wildcard=two_wildcard,
                is_vs_ai=True,
            )
            service.start_game(room_code=room_code, host=request.user)
            return redirect('game_room', room_code=room_code)
        except Exception as e:
            return render(request, 'ai_room.html', {'error': str(e)})
        
    return render(request, 'ai_room.html')



@login_required
def create_tournament_view(request):
    if request.method == 'POST':
        max_players         = int(request.POST['max_players'])
        jack_blocks_takeit   = request.POST.get('jack_blocks_takeit') == 'on'
        two_wildcard         = request.POST.get('two_wildcard') == 'on'

        service = TournamentService()
        code = service.create_tournament(
            host=request.user,
            max_players=max_players,
            jack_blocks_takeit=jack_blocks_takeit,
            two_wildcard=two_wildcard,
        )
        return redirect('tournament_lobby', code=code)

    return render(request, 'create_tournament.html')


@login_required
def tournament_lobby_view(request, code):
    service = TournamentService()
    state   = service.get_lobby_state(code)
    return render(request, 'tournament_lobby.html', {
        'code':  code,
        'state': state,
        'is_host': state['host_id'] == str(request.user.id),
        'empty_slots_range': range(state['empty_slots']),
        'total_bots_range': range(state['total_bots']),
    })

@login_required
def start_tournament_view(request, code):
    if request.method == 'POST':
        service = TournamentService()
        try:
            service.start_tournament(code=code, host=request.user)
        except Exception as e:
            return redirect('tournament_lobby', code=code)
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"tournament_{code}",
            {
                'type': 'tournament_update',
                'data': {'type': 'tournament_started', 'code': code},
            }
        )
        
        return redirect('tournament_status', code=code)
    
    return redirect('tournament_lobby', code=code)

@login_required
def tournament_status_view(request, code):
    tournament = Tournament.objects.get(code=code)
    my_id      = str(request.user.id)

    # Cherche si CE joueur a un match en cours dans le round actuel
    all_matches = TournamentMatch.objects.filter(tournament=tournament).order_by('round_number')

    if not all_matches.exists():
        return redirect('home')

    current_round = all_matches.order_by('-round_number').first().round_number

    my_match = TournamentMatch.objects.filter(
        tournament=tournament,
        round_number=current_round,
    ).filter(
        Q(player1_label=my_id) | Q(player2_label=my_id)
    ).first()

    if my_match and my_match.room_code and not my_match.finished:
        return redirect('game_room', room_code=my_match.room_code)

    # Déterminer le nombre total de rounds (log2 de 8 = 3)
    total_rounds = 3  # Toujours 3 pour un tournoi à 8 joueurs

    # Construire les données de chaque round pour le bracket
    all_rounds = []
    for r in range(1, current_round + 1):
        matches_in_round = TournamentMatch.objects.filter(
            tournament=tournament,
            round_number=r,
        )

        matches_data = []
        for m in matches_in_round:
            matches_data.append({
                'p1':      label_to_name(m.player1_label),
                'p2':      label_to_name(m.player2_label),
                'winner':  label_to_name(m.winner_label) if m.winner_label else None,
                'finished': m.finished,
                'is_tbd':  False,
            })

        # Calcul de l'espacement visuel (plus les rounds avancent, plus les matchs sont espacés)
        nb_matches   = len(matches_data)
        gap          = 40 * (2 ** (r - 1))
        padding_top  = gap // 2
        connector_height = 80 * (2 ** (r - 1))

        all_rounds.append({
            'round_number':     r,
            'matches':          matches_data,
            'gap':              gap,
            'padding_top':      padding_top,
            'connector_height': connector_height,
        })

    # Nom du champion si tournoi terminé
    champion_name = None
    if tournament.status == 'finished' and tournament.winner:
        champion_name = tournament.winner.username
    elif tournament.status == 'finished':
        champion_name = "🤖 IA"

    return render(request, 'tournament_status.html', {
        'tournament':   tournament,
        'all_rounds':   all_rounds,
        'current_round': current_round,
        'total_rounds': total_rounds,
        'code':         code,
        'my_id':        my_id,
        'champion_name': champion_name,
    })

@login_required
def leave_tournament_view(request, code):
    try:
        tournament = Tournament.objects.get(code=code)
    except Tournament.DoesNotExist:
        return redirect('home')

    if tournament.host == request.user:
        #Cas1 : c'est le host
        #Notifier les joueurs
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"tournament_{code}",

            {
                'type':'tournament_update',
                'data': {
                    'type': 'host_left',
                    'message': 'Le host a quitté le tournoi'
                },
            }
        )
        #supprimer la salle
        tournament.delete()
        return redirect('home')
    
    TournamentSlot.objects.filter(tournament=tournament, user=request.user).delete()

    service = TournamentService()
    state = service.get_lobby_state(code)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
     f"tournament_{code}",
            {
                'type':'tournament_update',
                'data': {
                    'type': 'tournament_update',
                    'state': state
                },
            }   
    )

    return redirect('home')


@login_required
def join_tournament_view(request):
    if request.method == 'POST':
        code = request.POST['code']
        service = TournamentService()
        try:
            service.join_tournament(code=code, user=request.user)

            state = service.get_lobby_state(code)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"tournament_{code}",
                {
                    'type': 'tournament_update',
                    'data': {'type': 'tournament_update', 'state':state},
                }
            )

            return redirect('tournament_lobby', code=code)
        except Exception as e:
            tournaments = Tournament.objects.filter(status='waiting')
            return render(request, 'join_tournament.html', {'tournaments': tournaments, 'error': str(e)})
    
    tournaments = Tournament.objects.filter(status='waiting')
    return render(request, 'join_tournament.html', {'tournaments': tournaments})
        
def tournament_menu_view(request):
    return render(request, 'tournament_menu.html')
    

    
