const gameData = document.getElementById('game-data');
const roomCode = gameData.dataset.roomCode;
const playerId = gameData.dataset.playerId;
let gameEnded = false;

//============CONNEXION WEBSOCKET
const wsProtocol = window.location.protocol === 'https:' ? 'wss//' : 'ws://';
const socket = new WebSocket(`${wsProtocol}${window.location.host}/ws/game/${roomCode}/`);

socket.onopen = function(){
    console.log("WebSocket jeu Connecté !");
    socket.send(JSON.stringify({action: 'get_state'}));
};

socket.onmessage = function(event){
    const data = JSON.parse(event.data);
    updateGameUI(data);
};

socket.onclose = function(){
    console.log('Websocket deconnecté !');
};

//===========jouer une carte
function playCard(rank, suit, declaredSuit = null){
    socket.send(JSON.stringify({
        action: 'play',
        rank: rank,
        suit: suit,
        declared_suit: declaredSuit,
    }));
}

//===========piocher une carte
function drawCard(){
    socket.send(JSON.stringify({
        action: 'draw',
    }));
}

function updateGameUI(state) {
    

    if(state.type === 'error'){
        alert(state.message);
        return;
    }
    
    if  (state.type === 'tournament_match_finished'){
        if(state.result === 'lose'){
            alert('Vous avez perdu. Bonne chance la prochaine fois !!');
            window.location.href = '/accounts/home/';
        } 
        else{
        window.location.href = `/lobby/tournament/${state.tournament_code}/status/`;
        }
        return;
    }

    if (state.type === 'tournament_finished'){
        if (state.is_winner){
            alert('Bravo. Vous avez remporté le tournoi !');
        }
        window.location.href = '/accounts/home/';
        return;
    }
    updateTourInfo(state);
    updatePot(state);
    updateAdversaires(state);
    updateMyHand(state);
    updateGameInfo(state);

   
    if(state.finished){
        console.log('Finished recu, is_tournament_match:', state.is_tournament_match, 'gameEnded:', gameEnded);
        if(state.is_tournament_match){
            return;
        }
        if(!gameEnded){
            gameEnded = true;
            setTimeout(() => {
                alert('Partie Terminée');
                window.location.href = '/accounts/home/';
            }, 500);
            
        }
        return;
    }
}

// ===== TOUR =====
function updateTourInfo(state) {
    const tourInfo = document.getElementById('tour-info');
    const playerId = document.getElementById('game-data').dataset.playerId;

    document.getElementById('game-data').dataset.currentPlayer = state.current_player;
    if (state.current_player === playerId) {
        tourInfo.innerHTML = '🟢 Votre tour !';
        document.getElementById('btn-draw').disabled = false;
    } else {
        tourInfo.innerHTML = `🔵 Tour de ${state.current_player_username}`;
        document.getElementById('btn-draw').disabled = true;
    }
}

// ===== POT =====
function updatePot(state) {
    const potCard = document.getElementById('pot-card');
    const penalty = document.getElementById('penalty-info');

    potCard.src = `/static/images/cards/${state.pot.image}`;

    if (state.takeit_penalty > 0) {
        penalty.innerHTML = `⚠️ Pénalité : ${state.takeit_penalty} cartes`;
    } else {
        penalty.innerHTML = '';
    }
}

// ===== ADVERSAIRES =====
function updateAdversaires(state) {
    const zone    = document.getElementById('zone-adversaires');
    const myId    = document.getElementById('game-data').dataset.playerId;
    zone.innerHTML = '';

    state.players.forEach(player => {
        if (player.id === myId) return; // sauter le joueur courant

        let cards = '';
        for (let i = 0; i < player.nb_cards; i++) {
            cards += `<img src="/static/images/cards/back.png" alt="carte">`;
        }

        zone.innerHTML += `
            <div class="adversaire-card">
                <span class="adversaire-name">${player.username}</span>
                <div class="adversaire-cards">${cards}</div>
                <span class="adversaire-count">${player.nb_cards} cartes</span>
            </div>
        `;
    });
}

// ===== MA MAIN =====
function updateMyHand(state) {
    if (!state.my_hand) return;

    const handCards = document.getElementById('hand-cards');
    handCards.innerHTML = '';

    state.my_hand.forEach(card => {
        const img = document.createElement('img');
        img.src     = `/static/images/cards/${card.image}`;
        img.alt     = `${card.rank}${card.suit}`;
        img.dataset.rank = card.rank;
        img.dataset.suit = card.suit;
        img.onclick = () => selectCard(img, card.rank, card.suit);
        handCards.appendChild(img);
    });
}

// ===== INFOS JEU =====
function updateGameInfo(state) {
    const declaredSuit = document.getElementById('declared-suit');
    const bankCount    = document.getElementById('bank-count');

    if (state.declared_suit) {
        declaredSuit.innerHTML = `🎨 Couleur imposée :<img src="/static/images/cards/suit-${state.declared_suit}.png" class="declared-suit-icon">`;
    } else {
        declaredSuit.innerHTML = '';
    }
    bankCount.innerHTML = `Banque: ${state.bank_count} cartes`;
}

// ===== SÉLECTIONNER UNE CARTE =====
let selectedCard = null;

function selectCard(img, rank, suit) {
    const myId    = document.getElementById('game-data').dataset.playerId;
    const current = document.getElementById('game-data').dataset.currentPlayer;

    if (myId !== current) return; // pas ton tour

    // Désélectionner si déjà sélectionnée
    if (selectedCard === img) {
        img.classList.remove('selected');
        selectedCard = null;
        return;
    }

    // Désélectionner l'ancienne
    if (selectedCard) {
        selectedCard.classList.remove('selected');
    }

    img.classList.add('selected');
    selectedCard = img;

    // Si c'est un valet → demander la couleur
    if (rank === 'J') {
        askDeclaredSuit(rank, suit);
    } else {
        playCard(rank, suit);
        selectedCard = null;
    }
}

// ===== VALET → CHOISIR COULEUR =====
let pendingJackPlay = null;

function askDeclaredSuit(rank, suit) {
    pendingJackPlay = { rank, suit };
    document.getElementById('suit-modal').style.display = 'flex';
}

document.querySelectorAll('.suit-icon').forEach(icon => {
    icon.addEventListener('click', () => {
        const chosenSuit = icon.dataset.suit;
        document.getElementById('suit-modal').style.display = 'none';

        if (pendingJackPlay) {
            playCard(pendingJackPlay.rank, pendingJackPlay.suit, chosenSuit);
            pendingJackPlay = null;
            selectedCard = null;
        }
    });
});
