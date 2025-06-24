const socket = io();
let myRole = 'Spectator';

socket.on('lobby_phase', () => lobbyPhase());

socket.on('available_roles', roles => {
    document.getElementById('join-button').disabled = (roles.length === 0);
    const dropdown = document.getElementById('role-dropdown');
    dropdown.innerHTML = '';
    roles.forEach(role => {
        const opt = document.createElement('option');
        opt.value = role;
        opt.text = role;
        dropdown.appendChild(opt);
    });
});

socket.on('action_failed', msg => alert(msg));

socket.on('role_assigned', role => {
    myRole = role;
    document.getElementById('your-role').innerText = role;
    lobbyPhase();
});

socket.on('update_lobby', status => {
    const list = document.getElementById('player-status');
    list.innerHTML = '';

    for (let player in status.players) {
        const ready = status.players[player];
        const li = document.createElement('li');
        li.className = ready ? 'ready' : 'not-ready';
        li.textContent = player;

        const state = document.createElement('span');
        state.textContent = ready ? 'Ready' : 'Not Ready';
        li.appendChild(state);

        list.appendChild(li);
    }
});


socket.on('game_paused', () => {
    alert('Game paused. A player left the game.');
    const btn = document.getElementById('ready-btn');
    btn.innerText = 'Ready';
});

socket.on('bidding_phase', () => {
    document.getElementById('your-role-bid').innerText = myRole;
    switchView('auction');
});

socket.on('update_auction', data => {
    const {turn, contract, bids, bidding_history} = data;

    document.getElementById('curr-turn').innerText = turn;
    document.getElementById('contract').innerText = contract;

    renderBiddingTable(bidding_history);
    renderBidButtons(bids);
});


socket.on('player_update_auction', data => {
    const {hand} = data;
    renderOwnHand('your-auction-hand', hand);
});


socket.on('play_phase', () => {
    document.getElementById('your-role-play').innerText = myRole;
    switchView('play');
});

socket.on('update_play', data => {
    const {turn, trick_count, trick, direction_hands, legal_hand} = data;


    document.getElementById('curr-turn-play').innerText = turn;
    document.getElementById('tricks-ns').innerText = trick_count[0];
    document.getElementById('tricks-we').innerText = trick_count[1];

    renderTrick(trick);

    renderHands('hands-view', direction_hands, legal_hand, turn, myRole[0]);
});


socket.on('update_score', data => {
    const {trick_count, contract, scores} = data;
    document.getElementById('tricks-ns-score').innerText = trick_count[0];
    document.getElementById('tricks-we-score').innerText = trick_count[1];
    document.getElementById('contract-score').innerText = contract;
    document.getElementById('score-display').innerText = scores;
});

socket.on('score_phase', () => switchView('score'));

socket.on('game_finished', () => switchView('game-over'));

function joinGame() {
    const role = document.getElementById('role-dropdown').value;
    socket.emit('choose_role', role);
}

function toggleReady() {
    socket.emit('toggle_ready');
    const btn = document.getElementById('ready-btn');
    btn.innerText = btn.innerText === 'Ready' ? 'Unready' : 'Ready';
}

function playCard(card) {
    socket.emit('play_card', card);
}


function endScores() {
    socket.emit('end_scores');
}

function lobbyPhase() {
    switchView('lobby');
}

function switchView(viewId) {
    ['role-selection', 'lobby', 'auction', 'play', 'score', 'game-over'].forEach(id => {
        document.getElementById(id).style.display = (id === viewId) ? 'block' : 'none';
    });
}

function renderBiddingTable([rounds, dirNames]) {
    const table = document.getElementById('bidding-history');
    table.innerHTML = '';

    // Header
    const header = document.createElement('tr');
    dirNames.forEach(dir => {
        const th = document.createElement('th');
        th.innerText = dir;
        header.appendChild(th);
    });
    table.appendChild(header);

    // Bidding rounds
    rounds.forEach(row => {
        const tr = document.createElement('tr');
        row.forEach(bid => {
            const td = document.createElement('td');
            if (bid === '?') {
                td.innerHTML = '<strong style="font-size: 22px; color: lightblue;">?</strong>';
            } else {
                td.innerText = bid;
            }
            tr.appendChild(td);
        });
        table.appendChild(tr);
    });
}


function renderBidButtons(legalBids) {
    const table = document.getElementById('bidding-buttons-table');
    table.innerHTML = '';

    const suits = [['C', '♣'], ['D', '♦'], ['H', '♥'], ['S', '♠'], ['NT', 'NT']];
    for (let level = 1; level <= 7; level++) {
        const tr = document.createElement('tr');
        suits.forEach(([suit, symbol]) => {
            const code = `${level}${suit}`;
            const td = document.createElement('td');
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.innerText = `${level}${symbol}`;
            btn.onclick = () => makeBidFromButton(code);
            btn.disabled = !legalBids.includes(code);
            btn.style.fontSize = '28px';
            btn.style.width = '90px';
            btn.style.height = '54px';
            btn.style.margin = '2px';
            btn.style.borderRadius = '6px';
            if (['H', 'D'].includes(suit)) btn.style.color = 'red';

            td.appendChild(btn);
            tr.appendChild(td);
        });
        table.appendChild(tr);
    }

    // Special buttons
    document.getElementById('bid-pass').disabled = !legalBids.includes('PASS');
    document.getElementById('bid-x').disabled = !legalBids.includes('X');
    document.getElementById('bid-xx').disabled = !legalBids.includes('XX');
}

function makeBidFromButton(bid) {
    socket.emit('make_bid', bid);
}

function renderHands(containerId, view, legalCards = [], isMyTurn = false, currentDir = null) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    const rotations = {N: 180, S: 0, E: 270, W: 90};
    const layoutOrder = {N: 'north', S: 'south', E: 'east', W: 'west'};

    for (const dir of ['N', 'E', 'S', 'W']) {
        const handWrapper = document.createElement('div');
        handWrapper.className = layoutOrder[dir];

        const label = document.createElement('strong');
        label.innerText = layoutOrder[dir][0].toUpperCase() + layoutOrder[dir].slice(1);
        handWrapper.appendChild(label);

        const handDiv = document.createElement('div');
        handDiv.className = 'card-hand ' + (['E', 'W'].includes(dir) ? 'vertical' : 'horizontal');

        view[dir].forEach(card => {
            const button = document.createElement('button');
            button.className = 'card-button';

            const isVisible = dir === currentDir;
            const isLegal = isVisible && isMyTurn && legalCards.includes(card);

            if (isLegal) {
                button.onclick = () => playCard(card);
            } else {
                button.disabled = true;

                if (isVisible && isMyTurn) {
                    button.classList.add('dimmed-card');
                }
            }


            const img = document.createElement('img');
            img.className = `card rotate-${rotations[dir]}`;
            img.src = isVisible
                ? `/static/assets/${card}.png`
                : '/static/assets/card_back.png';

            button.appendChild(img);
            handDiv.appendChild(button);
        });

        handWrapper.appendChild(handDiv);
        container.appendChild(handWrapper);
    }
}


function renderOwnHand(containerId, cards) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    cards.forEach(card => {
        const button = document.createElement('button');
        button.className = 'card-button';
        button.disabled = true;

        const img = document.createElement('img');
        img.className = 'card rotate-0'; // zawsze poziomo
        img.src = card === '*' ? '/static/assets/card_back.png' : `/static/assets/${card}.png`;

        button.appendChild(img);
        container.appendChild(button);
    });
}

function renderTrick(trick) {
    const container = document.getElementById('trick-center');
    container.innerHTML = '';

    const rotations = {N: 180, S: 0, E: 270, W: 90};
    const offsets = {
        N: [0, -30], S: [0, 30], E: [30, 0], W: [-30, 0]
    };

    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    wrapper.style.width = '100px';
    wrapper.style.height = '100px';
    wrapper.style.margin = '0 auto';

    trick.forEach(([dir, card]) => {
        const img = document.createElement('img');
        img.src = `/static/assets/${card}.png`;
        img.className = `card rotate-${rotations[dir]}`;

        const [x, y] = offsets[dir];
        img.style.position = 'absolute';
        img.style.left = `calc(50% + ${x}px - 40px)`;
        img.style.top = `calc(50% + ${y}px - 60px)`;
        img.style.width = '100px';
        img.style.zIndex = '10';

        wrapper.appendChild(img);
    });

    container.appendChild(wrapper);
}
