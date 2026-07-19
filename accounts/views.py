from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django. contrib.auth.decorators import login_required
from accounts.models import User


# Create your views here.
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request=request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        
        return render(request, 'login.html', {'error': 'username not found'})
    
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

def  register_view(request):
    #Si le joueur soumet le formulaire
    if request.method == 'POST':
        username = request.POST['username'] #recuperer le champ username
        password = request.POST['password'] #recuperer le champ password

        #Verifie si le username n'existe pas deja
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'An account with same username already exists'})
        
        #Crée le compte
        user = User.objects.create_user(username=username, password=password)

        #redirect vers login
        return redirect('login')
    
    #si method==GET affiche la page
    return render(request, 'register.html')

@login_required
def accueil_view(request):
    user = request.user

    return render(request, 'accueil.html', {
        'user': user, 
        'games_played': user.games_played,
        'games_won' : user.games_won,
        'games_lost': user.games_played - user.games_won,
    })