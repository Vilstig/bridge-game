import eventlet
eventlet.monkey_patch(os=False)
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from game_handler_jason import Handler

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tanuki???'
socketio = SocketIO(app, async_mode='eventlet')
handler = Handler()


@app.route('/')
def index():
    return render_template('test_temp.html')


@socketio.on('connect')
def handle_connect():
    sid = request.sid
    if not handler.game_running:
        emit('available_roles', handler.available_dirs(), broadcast=True)
    '''elif handler.get_game_status_str() == 'AUCTION':
        emit('bidding_phase', room=sid)
        emit('update_auction', handler.auction_status(), room=sid)
        update_player_auction_single(sid)
    elif handler.get_game_status_str() == 'PLAY':
        emit('play_phase', room=sid)
        emit('update_play', handler.play_status(), room=sid)
        update_player_play_single(sid)
    elif handler.get_game_status_str() == 'DISPLAY_SCORE':
        emit('score_phase', room=sid)
        emit('update_score', handler.score_status(), room=sid)
    elif handler.get_game_status_str() == 'GAME_OVER':
        emit('game_finished', room=sid)
        emit('update_game_over', handler.game_over_status(), room=sid)'''


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    was_running = handler.game_running
    if handler.remove_player(sid) and was_running:
        emit('game_paused', broadcast=True)
        emit('lobby_phase', broadcast=True)
    emit('update_lobby', handler.get_status(), broadcast=True) #outside the if for potential spectator handling


@socketio.on('choose_role')
def choose_role(role: str):
    sid = request.sid
    if not handler.add_player(sid, role):
        emit('action_failed', f'Role {role} is taken. Select a different role.')
        return
    emit('role_assigned', role)
    emit('update_lobby', handler.get_status(), broadcast=True)
    emit('available_roles', handler.available_dirs(), broadcast=True)


@socketio.on('toggle_ready')
def toggle_ready():
    sid = request.sid
    handler.toggle_ready(sid)
    emit('update_lobby', handler.get_status(), broadcast=True)

    if handler.game_running:
        if handler.get_game_status_str() == 'DEAL_CARDS':
            handler.deal_cards()

        if handler.get_game_status_str() == 'AUCTION':
            emit('bidding_phase', broadcast=True)
            emit('update_auction', handler.auction_status(), broadcast=True)
            update_player_auction()
        elif handler.get_game_status_str() == 'PLAY':
            emit('play_phase', broadcast=True)
            #emit('update_play', handler.play_status(), broadcast=True) when implementing spectators, this should be modified to update their play screen correctly
            update_player_play()
        elif handler.get_game_status_str() == 'DISPLAY_SCORE':
            emit('score_phase', broadcast=True)
            emit('update_score', handler.score_status(), broadcast=True)
        elif handler.get_game_status_str() == 'GAME_OVER':
            emit('game_finished', broadcast=True)
            emit('update_game_over', handler.game_over_status(), broadcast=True)


@socketio.on('make_bid')
def make_bid(bid):
    sid = request.sid
    if not handler.make_bid(sid, bid):
        emit('action_failed', "Can't bid. Not your turn or wrong phase.")
        return
    emit('update_auction', handler.auction_status(), broadcast=True)
    update_player_auction()
    if handler.get_game_status_str() == 'PLAY':
        emit('play_phase', broadcast=True)
        #emit('update_play', handler.play_status(), broadcast=True)
        update_player_play()


@socketio.on('play_card')
def play_card(card):
    handler.play_card(card)

    if handler.get_game_status_str() == 'DISPLAY_SCORE':
        emit('score_phase', broadcast=True)
        emit('update_score', handler.score_status(), broadcast=True)
        return
    elif handler.get_game_status_str() == 'GAME_OVER':
        emit('game_finished', broadcast=True)
        emit('update_game_over', handler.game_over_status(), broadcast=True)
        return

    #emit('update_play', handler.play_status(), broadcast=True)
    update_player_play()


@socketio.on('end_scores')
def end_scores():
    handler.end_scores()
    emit('bidding_phase', broadcast=True)
    emit('update_auction', handler.auction_status(), broadcast=True)
    update_player_auction()


def update_player_auction(sid=None):
    if sid:
        emit('player_update_auction', handler.get_player_hands()[sid], room=sid)
    else:
        for sid in handler.player_dict:
            emit('player_update_auction', handler.get_player_hands()[sid], room=sid)



def update_player_play(sid=None):
    hand_status = handler.player_hand_update()
    visible_hands = handler.get_visible_hands_per_sid()
    play_status = handler.play_status()
    if sid:
        emit('update_play', {
            'turn': hand_status['player_turns'][sid],
            'trick_count': play_status['trick_count'],
            'trick': play_status['trick'],
            'last_full_trick': play_status['last_full_trick'],
            'direction_hands': visible_hands[sid],
            'legal_hand': hand_status['legal_hand']
        }, room=sid)
    else:
        for sid in handler.player_dict:
            emit('update_play', {
                'turn': hand_status['player_turns'][sid],
                'trick_count': play_status['trick_count'],
                'trick': play_status['trick'],
                'last_full_trick': play_status['last_full_trick'],
                'direction_hands': visible_hands[sid],
                'legal_hand': hand_status['legal_hand']
            }, room=sid)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
