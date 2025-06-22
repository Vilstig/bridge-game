const socket = io();
myRole = null;

socket.on('available_roles', roles => {
    const dropdown = document.getElementById('role-dropdown');
    dropdown.innerHTML = ''; //clears all potential children
    roles.forEach(role => {
        const opt = document.createElement('option');
        opt.value = role;
        opt.text = role;
        dropdown.appendChild(opt);
    });
});

socket.on('action_failed', msg =>{
    alert(msg);
});

socket.on('role_assigned', role => {
    myRole = role;
    document.getElementById('your-role').innerText = role;
    document.getElementById('role-selection').style.display = 'none';
    document.getElementById('lobby').style.display = 'block';
});

socket.on('update_lobby', status => {
    const list = document.getElementById('player-status');
    list.innerHTML = '';
    for (let player in status.players) {
        const li = document.createElement('li');
        li.textContent = `${player}: ${status.players[player] ? 'Ready' : 'Not ready'}`;
        list.appendChild(li);
    }
    document.getElementById('spectator-count').innerText = status.spec_count;
});

socket.on('game_paused', () => {
    alert('Game paused. A player left the game.');
    const btn = document.getElementById('ready-btn');
    btn.innerText = 'Ready';
});

socket.on('bidding_phase', () => {
    document.getElementById('your-role-bid').innerText = myRole;
    document.getElementById('lobby').style.display = 'none';
    document.getElementById('auction').style.display = 'block';
});

socket.on('update_auction', (turn, contract, bids) => {
    document.getElementById('curr-turn').innerText = turn;
    document.getElementById('contract').innerText = contract;
    const dropdown = document.getElementById('bid-dropdown');
    dropdown.innerHTML = '';
    bids.forEach(bid => {
        const opt = document.createElement('option');
        opt.value = bid;
        opt.text = bid;
        dropdown.appendChild(opt);
    });
});

socket.on('player_update_auction', (hand, turn) => {
    document.getElementById('player-hand').innerText = hand;
    document.getElementById('bid-btn').disabled = !turn;
});

function joinGame(){
    const role = document.getElementById('role-dropdown').value;
    socket.emit('choose_role', role);
}

function toggleReady(){
    socket.emit('toggle_ready');
    const btn = document.getElementById('ready-btn');
    btn.innerText = btn.innerText === 'Ready' ? 'Unready' : 'Ready';
}

function makeBid(){
    const bid = document.getElementById('bid-dropdown').value;
    socket.emit('make_bid', bid);
}