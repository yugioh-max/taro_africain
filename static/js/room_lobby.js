const roomData = document.getElementById('room-data');
const roomCode = roomData.dataset.roomCode;
const maxPlayers = parseInt(roomData.dataset.maxPlayers);

const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
const socket = new WebSocket(`${wsProtocol}://${window.location.host}/ws/game/${roomCode}/`);

socket.onopen = function() {
    console.log("WebSocket connecté !");
};

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'lobby_update') {
        updatePlayers(data.players);
    }

    if(data.type === 'host_left'){
        alert(data.message);
        window.location.href = '/accounts/home/';
    }

    if(data.type === 'game_started'){
        window.location.href = `/game/room/${data.room_code}/`;
    }
    
};

socket.onclose = function() {
    console.log("WebSocket déconnecté !");
};

function updatePlayers(players) {
    const section = document.getElementById('players-list');
    section.innerHTML = '';

    // Joueurs connectés
    players.forEach(player => {
        const div = document.createElement('div');
        div.className = 'player-item';
        div.innerHTML = `
            <span class="player-status">✅</span>
            <span class="player-name">
                ${player.username}
                ${player.is_host ? '<span class="host-badge">Host</span>' : ''}
            </span>
        `;
        section.appendChild(div);
    });

    // Slots vides
    const empty = maxPlayers - players.length;
    for (let i = 0; i < empty; i++) {
        const div = document.createElement('div');
        div.className = 'player-item empty';
        div.innerHTML = `
            <span class="player-status">⏳</span>
            <span class="player-name">En attente...</span>
        `;
        section.appendChild(div);
    }
}

