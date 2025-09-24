from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from terminal_backend import PtyTerminal
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aiaiai'

# Escolha async_mode 'gevent' se for usar gevent/gevent-websocket.
socketio = SocketIO(app, async_mode='gevent')

# Map client session id -> terminal instance
terminals = {}
threads = {}

def background_read(sid):
    term = terminals.get(sid)
    if not term:
        return
    while term.isalive():
        data = term.read()
        if data:
            try:
                socketio.emit('terminal-output', {'output': data}, to=sid)
            except Exception:
                pass
        time.sleep(0.01)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def on_connect():
    sid = getattr(socketio, 'sid', None) or getattr(request, 'sid', None)
    # flask-socketio fornece sid via `request.sid`
    from flask import request
    sid = request.sid
    # cria um PTY para este cliente
    term = PtyTerminal(['/bin/bash'])
    terminals[sid] = term
    # inicia thread de leitura
    t = threading.Thread(target=background_read, args=(sid,), daemon=True)
    threads[sid] = t
    t.start()
    print(f'Client connected: {sid}')

@socketio.on('disconnect')
def on_disconnect():
    from flask import request
    sid = request.sid
    term = terminals.pop(sid, None)
    if term:
        term.close()
    threads.pop(sid, None)
    print(f'Client disconnected: {sid}')

@socketio.on('terminal-input')
def on_terminal_input(message):
    from flask import request
    sid = request.sid
    data = message.get('input', '')
    term = terminals.get(sid)
    if term:
        term.write(data)

@socketio.on('resize')
def on_resize(message):
    from flask import request
    sid = request.sid
    cols = int(message.get('cols', 80))
    rows = int(message.get('rows', 24))
    term = terminals.get(sid)
    if term:
        term.resize(cols, rows)

if __name__ == '__main__':
    # Apenas para desenvolvimento com gevent
    socketio.run(app, host='0.0.0.0', port=5000)