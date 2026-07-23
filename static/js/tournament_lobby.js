const tData = document.getElementById('tournament-data');
const code = tData.dataset.code;
const maxPlayers = parseInt(tData.dataset.maxPlayers);
const totalBots = parseInt(tData.dataset.totalBots);

const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
const socket = new WebSocket(`${wsProtocol}://${window.location.host}/ws/tournament/${code}/`);

socket.onmessage = function(event){
    const data = JSON.parse(event.data);
    
    console.log("MESSAGE TOURNOI RECU :", data);
    if (data.type === 'tournament_update'){
        updatePlayers(data.state.players);
    }

    if ( data.type === 'host_left'){
        alert(data.message);
        window.location.href = '/accounts/home/';
    }

    if(data.type === 'next_round_ready'){
        window.location.href = `/lobby/tournament/${data.code}/status/`;
    }

    if (data.type === 'tournament_started'){
        window.location.href = `/lobby/tournament/${data.code}/status`;
    }

    if(data.type === 'tournament_finished'){
        if(data.is_winner){
            alert('Bravo vous avez remporté le tournoi');
        } else{
            alert('Tournoi terminée');
        }
        window.location.href = '/accounts/home/';
    }
};

function updatePlayers(players) {
    const section  = document.getElementById('tournament-players-list');
    if(!section){
        return;
    }
    const nbLabel  = document.getElementById('nb-humains');
    section.innerHTML = '';

    // Mettre à jour le compteur "X/Y humains"
    nbLabel.innerHTML = players.length;

    // ✅ Joueurs humains déjà présents
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

    // ⏳ Slots humains encore vides
    const emptySlots = maxPlayers - players.length;
    for (let i = 0; i < emptySlots; i++) {
        const div = document.createElement('div');
        div.className = 'player-item empty';
        div.innerHTML = `
            <span class="player-status">⏳</span>
            <span class="player-name">En attente...</span>
        `;
        section.appendChild(div);
    }

    // 🤖 Bots — toujours le même nombre, ne change jamais
    for (let i = 0; i < totalBots; i++) {
        const div = document.createElement('div');
        div.className = 'player-item';
        div.innerHTML = `
            <span class="player-status">🤖</span>
            <span class="player-name">IA</span>
        `;
        section.appendChild(div);
    }
}
