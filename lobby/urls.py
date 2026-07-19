from django.urls import path
from .views import join_room_views, create_room_views, join_tournament_view, room_lobby_view, start_game_view, leave_room_view, tournament_menu_view, update_options_view, ai_room_view, create_tournament_view, tournament_lobby_view, start_tournament_view, tournament_status_view, leave_tournament_view

urlpatterns = [
    path('create/', create_room_views, name='create_room'),
    path('join/', join_room_views, name='join_room'),

    path('room/<str:room_code>/', room_lobby_view,  name='room_lobby'),
    path('room/<str:room_code>/start/', start_game_view,  name='start_game'),
    path('room/<str:room_code>/leave/', leave_room_view, name='leave_room'),
    path('room/<str:room_code>/options/', update_options_view, name='update_options'),

    path('vs-ai/', ai_room_view, name='ai_room'),

    path('tournament/create/', create_tournament_view, name='create_tournament'),
    path('tournament/join/', join_tournament_view, name='join_tournament'),
    path('tournament/', tournament_menu_view, name='tournament_menu'),
    
    path('tournament/<str:code>/', tournament_lobby_view, name='tournament_lobby'),
    path('tournament/<str:code>/start', start_tournament_view, name='start_tournament'),
    path('tournament/<str:code>/status/', tournament_status_view, name='tournament_status'),
    path('tournament/<str:code>/leave/', leave_tournament_view, name='leave_tournament'),
    
]
