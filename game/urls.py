from django.urls import path
from .views import game_room_view

urlpatterns = [
    path('room/<str:room_code>/', game_room_view, name='game_room'),
]