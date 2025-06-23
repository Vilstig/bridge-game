from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from game_handler import Handler

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tanuki???'
socketio = SocketIO(app, async_mode='eventlet')
handler = Handler()

#==================LOBBY AND CONNECTIONS====================================
@app.route('/')
def index():
    return render_template('test_temp.html')

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    if not handler.game_running:
        emit('available_roles', handler.available_dirs(), broadcast=True)
    elif handler.get_game_status_str() == 'AUCTION':
        emit('bidding_phase')
        update_auction_new_guest(sid)
    elif handler.get_game_status_str() == 'PLAY':
        emit('play_phase')
        update_play_new_guest(sid)
    elif handler.get_game_status_str() == 'DISPLAY_SCORE':
        emit('score_phase')
        update_score(sid)
    elif handler.get_game_status_str() == 'GAME_OVER':
        emit('game_finished')
        update_game_over(sid)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    was_running = handler.game_running
    if handler.remove_player(sid) and was_running:
        emit('game_paused', broadcast=True)
        emit('lobby_phase', broadcast=True)
    update_lobby()

@socketio.on('choose_role')
def choose_role(role: str):
    sid = request.sid
    if not handler.add_player(sid, role):
        emit('action_failed', f'Role ${role} is taken. Select a different role.')
        return
    emit('role_assigned', role)
    update_lobby()
    emit('available_roles', handler.available_dirs(), broadcast=True)

@socketio.on('toggle_ready')
def toggle_ready():
    sid = request.sid
    handler.toggle_ready(sid)
    update_lobby()
    if handler.game_running:
        if handler.get_game_status_str() == 'DEAL_CARDS':
            handler.deal_cards()

        if handler.get_game_status_str() == 'AUCTION':
            emit('bidding_phase', broadcast=True)
            update_auction()
        elif handler.get_game_status_str() == 'PLAY':
            emit('play_phase', broadcast=True)
            update_play()
        elif handler.get_game_status_str() == 'DISPLAY_SCORE':
            emit('score_phase', broadcast=True)
            update_score()
        elif handler.get_game_status_str() == 'GAME_OVER':
            emit('game_finished', broadcast=True)
            update_game_over()

def update_lobby():
    emit('update_lobby', handler.get_status(), broadcast=True)

#==========================AUCTION========================================

@socketio.on('make_bid')
def make_bid(bid):
    sid = request.sid
    if not handler.make_bid(sid, bid):
        emit('action_failed', "Can't bid. Not your turn or wrong phase.")
        return
    update_auction()
    if handler.get_game_status_str() == 'PLAY':
        emit('play_phase', broadcast=True)
        update_play()

def update_auction():
    auction_status = handler.auction_status()
    for sid in auction_status['hands']: #updating player exclusive fields
        emit('player_update_auction', (auction_status['hands'][sid], auction_status['player_turns'][sid]), room=sid)
    emit('update_auction', (auction_status['turn'], auction_status['contract'], auction_status['bids']), broadcast=True)

def update_auction_new_guest(sid):
    auction_status = handler.auction_status()
    emit('update_auction', (auction_status['turn'], auction_status['contract'], auction_status['bids']), room=sid)

#===========================PLAY====================================
def update_play():
    play_status = handler.play_status()
    hand_status = handler.player_hand_update()
    emit('update_play', (play_status['turn'], play_status['trick_count'][0], play_status['trick_count'][1], play_status['trick_str']), broadcast=True)
    for sid in hand_status['player_turns']:
        emit('update_hand', (hand_status['legal_hand'], hand_status['player_turns'][sid]), room=sid)
    for sid in play_status['player_views']:
        emit('update_hands_view', play_status['player_views'][sid], room=sid)

def update_play_new_guest(sid):
    play_status = handler.play_status()
    emit('update_play', (play_status['turn'], play_status['trick_count'][0], play_status['trick_count'][1], play_status['trick_str']), room=sid)

@socketio.on('play_card')
def play_card(card):
    handler.play_card(card)
    if handler.get_game_status_str() == 'DISPLAY_SCORE':
        emit('score_phase', broadcast=True)
        update_score()
        return
    elif handler.get_game_status_str() == 'GAME_OVER':
        emit('game_finished', broadcast=True)
        return
    update_play()

#=======================SCORE================================
def update_score(sid=None):
    score_status = handler.score_status()
    if sid:
        emit('update_score', (score_status['trick_count'][0], score_status['trick_count'][1], score_status['contract'], score_status['scores']), room=sid)
    else:
        emit('update_score', (score_status['trick_count'][0], score_status['trick_count'][1], score_status['contract'], score_status['scores']), broadcast=True)

@socketio.on('end_scores')
def end_scores():
    handler.end_scores()
    emit('bidding_phase', broadcast=True)
    update_auction()

#=============================GAME OVER=============================
def update_game_over(sid=None):
    game_over_status = handler.game_over_status()
    if sid:
        emit('update_game_over', game_over_status, room=sid)
    else:
        emit('update_game_over', game_over_status, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000) # debug=True for debug info