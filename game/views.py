from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# Create your views here.

@login_required
def game_room_view(request, room_code):
    return render(request, 'game_room.html', {
        'room_code' : room_code,
    })