const socket = io();

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

socket.on('role_taken', role =>{
    alert(`Role ${role} is taken. Select a different role.`);
});

socket.on('role_assigned', role => {
    document.getElementById('your-role').innerText = role;
    document.getElementById('role-selection').style.display = 'none';
    document.getElementById('game').style.display = 'block';
});

socket.on('update_status', status => {
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

function joinGame(){
    const role = document.getElementById('role-dropdown').value;
    socket.emit('choose_role', role)
}

function toggleReady(){
    socket.emit('toggle_ready');
    const btn = document.getElementById('ready-btn');
    btn.innerText = btn.innerText === 'Ready' ? 'Unready' : 'Ready';
}