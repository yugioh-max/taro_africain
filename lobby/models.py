from django.db import models

# Create your models here.

class Room(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False, default="room1")
    room_code = models.CharField(max_length=6, unique=True)
    host = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    options_json = models.JSONField()
    current_index =  models.IntegerField()
    takeit_penalty = models.IntegerField()
    declared_suit = models.CharField(max_length=10, null=True, blank=True)
    waiting_game_response = models.CharField(max_length=50, null=True, blank=True)
    game_candidate_id = models.IntegerField(null=True, blank=True)
    bank_json = models.JSONField()
    pot_json = models.JSONField()
    ranking_json = models.JSONField()
    is_private = models.BooleanField(default=False)
    password = models.CharField(max_length=50, null=True, blank=True)
    max_players = models.IntegerField(default=5, null=True, blank=True)
    is_vs_ai = models.BooleanField(default=False)
    is_tournament_match = models.BooleanField(default=False)

class RoomPlayer(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    hand_json = models.JSONField(null=True, blank=True)
    position = models.IntegerField()
    connected = models.BooleanField(default=False)
    eliminated = models.BooleanField(default=False)
    

class Tournament(models.Model):
    code         = models.CharField(max_length=6, unique=True)
    host         = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    max_players  = models.IntegerField()              # nb d'humains acceptés (1 à 8)
    options_json = models.JSONField(default=dict)
    status       = models.CharField(
        max_length=20,
        choices=[('waiting', 'En attente'), ('in_progress', 'En cours'), ('finished', 'Terminé')],
        default='waiting',
    )
    current_round = models.IntegerField(default=0)    # 1=poules, 2=demies, 3=finale
    winner        = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='tournaments_won')
    created_at    = models.DateTimeField(auto_now_add=True)


class TournamentSlot(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    user       = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    is_bot     = models.BooleanField(default=False)
    bot_label  = models.CharField(max_length=20, null=True, blank=True)   # ex: "BOT_3"
    eliminated = models.BooleanField(default=False)
    position   = models.IntegerField()


class TournamentMatch(models.Model):
    tournament    = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    round_number  = models.IntegerField()
    player1_label = models.CharField(max_length=50)   # user.id en string OU "BOT_x"
    player2_label = models.CharField(max_length=50)
    room_code     = models.CharField(max_length=6, null=True, blank=True)   # null si bot vs bot
    winner_label  = models.CharField(max_length=50, null=True, blank=True)
    finished      = models.BooleanField(default=False)

