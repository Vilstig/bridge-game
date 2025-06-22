from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from game_handler import Handler

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
    emit('available_roles', handler.available_dirs(), broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if handler.remove_player(sid):
        emit('game_paused', broadcast=True)
    update_status()

@socketio.on('choose_role')
def choose_role(role: str):
    sid = request.sid
    if not handler.add_player(sid, role):
        emit('role_taken', role)
        return
    emit('role_assigned', role)
    update_status()
    emit('available_roles', handler.available_dirs(), broadcast=True)

@socketio.on('toggle_ready')
def toggle_ready():
    sid = request.sid
    handler.toggle_ready(sid)
    update_status()

def update_status():
    emit('update_status', handler.get_status(), broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)