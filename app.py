#!/usr/bin/env python3
# author: https://github.com/def-fun
# repo: https://github.com/def-fun/rtm2
# based on https://github.com/miguelgrinberg/Flask-SocketIO/blob/master/example/app.py
from threading import Lock
from flask import Flask, send_from_directory, request, render_template, jsonify
from flask_compress import Compress
from flask_socketio import SocketIO
from flask_httpauth import HTTPBasicAuth
import cv2
import time
import os
# import platform
from driver import FrameDiff, timestamps2xyz

#######################################
#           configure start           #
#######################################
# if platform.system() == 'Windows':
#     camera = cv2.VideoCapture(0)
# elif platform.system() == 'Linux':
#     camera = cv2.VideoCapture('/dev/video0')
camera = cv2.VideoCapture(0)
# camera = cv2.VideoCapture('vtest.avi')
# your camera

FPS = 30
# frames per second, it based on your device performance. I think 10~40 is ok.

SAVE_MOTION_FRAMES = True
# save all motion frames to disk

FRAMES_IN_MEM_LIMIT = 64
# motion frames that cached in memory and can be shown in web page.

KEEP_DETECT = True
# set False to keep detect run only when clients num > 0

# UPDATE_FREQ = 0
# update frames even no motion detected every UPDATE_FREQ frames
# set 0 to disable update, set 1 to send every frame to clients.

async_mode = "eventlet"
# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
#######################################
#           configure end             #
#######################################

app = Flask(__name__)
Compress(app)
app.config['SECRET_KEY'] = 'secret!!!'
socketio = SocketIO(app, async_mode=async_mode)
auth = HTTPBasicAuth()
users = {
    'user': 'change_it'
}


@auth.get_password
def get_pwd(username):
    print(request.headers)
    if username in users:
        return users.get(username)
    else:
        return None


thread = None
thread_lock = Lock()
if KEEP_DETECT:
    CLIENTS = {'locker': {'ip': 'x', 'header': (('User-Agent', 'x'),)}}
else:
    CLIENTS = dict()
FRAMES_IN_MEM = dict()  # {timestamp1: frame_binary1, timestamp2: frame_binary2}
NEW_TIMESTAMPS = []  # frames timestamps that obtained from last run
OLD_TIMESTAMPS = []  # old frames timestamps list
for i in os.listdir('frames'):
    if i.endswith('.jpg'):
        OLD_TIMESTAMPS.append(int(i.split('.')[0]))
OLD_TIMESTAMPS_OUT = timestamps2xyz(sorted(OLD_TIMESTAMPS))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(filename='favicon.ico', directory='static')


@app.route('/')
@app.route('/index.html')
@auth.login_required
def index():
    return send_from_directory(filename='chart.html', directory='static')


@app.route('/static/<filename>')
@auth.login_required
def static_file(filename):
    return send_from_directory(filename=filename, directory='static')


@app.route('/frames/<filename>.jpg')
@auth.login_required
def show_history(filename):
    timestamp = int(filename)
    if timestamp in FRAMES_IN_MEM:
        return FRAMES_IN_MEM[timestamp], 200, {'Content-Type': 'image/jpeg'}
    elif os.path.isfile('./frames/{}.jpg'.format(timestamp)):
        return send_from_directory(filename='{}.jpg'.format(timestamp), directory='./frames')
    else:
        return send_from_directory(directory='static', filename='image_not_found.jpg')


def get_frame():
    try:
        _, frame = camera.read()
        return frame
    except Exception as e:
        print(e)
        socketio.emit('err', str(e), namespace='/state')
        return cv2.imread('./static/stream_error.jpg')


@app.route('/api')
@auth.login_required
def query_something():
    q = request.args.get('q')
    num = request.args.get('num')
    print(request.args)
    if q == 'frames_list':
        tmp = OLD_TIMESTAMPS_OUT + timestamps2xyz(NEW_TIMESTAMPS)
        if num == 'all':
            return jsonify(tmp)
        else:
            return jsonify(tmp[-int(num):])
    elif q == 'clients_list':
        return render_template('clients.html',
                               clients=[{'sid': k, 'ip': v['ip'], 'header': v['header']} for k, v in CLIENTS.items()])
    else:
        return 'undefined var.'


def background_thread():
    """send openCV motion frames to clients."""
    print('start detection.')
    global FRAMES_IN_MEM
    global NEW_TIMESTAMPS
    # counter = 0
    # global camera
    # camera = cv2.VideoCapture('vtest.avi')
    bg = get_frame()
    update_cache = [round(time.time() * 1000), ]
    while (len(CLIENTS) > 0) or KEEP_DETECT:
        socketio.sleep(1.0 / FPS)
        try:
            frame = get_frame()
            diff = FrameDiff(bg, frame)
            diff.do_default()
            if diff.count > 0:  # send frames and notices when motion detected.
                timestamp = round(time.time() * 1000)  # ms
                if len(update_cache) > 0:
                    if int(update_cache[0] / 1000) == int(timestamp / 1000):
                        update_cache.append(timestamp)
                    elif len(update_cache) == 1:
                        socketio.emit('update', [int(update_cache[0] / 1000) * 1000, 1, [update_cache[0]]],
                                      namespace='/data')
                        update_cache = []
                    elif len(update_cache) > 1:
                        update_pack = list(timestamps2xyz(update_cache)[0])
                        socketio.emit('update', update_pack, namespace='/data')
                        update_cache = []
                else:
                    update_cache.append(timestamp)
                NEW_TIMESTAMPS.append(timestamp)
                if SAVE_MOTION_FRAMES:
                    diff.save('frames/{}.jpg'.format(timestamp))
                image = cv2.imencode('.jpg', diff.marked_frame)[1]
                FRAMES_IN_MEM[timestamp] = image.tobytes()
                FRAMES_IN_MEM = {k: v for k, v in FRAMES_IN_MEM.items() if
                                 k in sorted(FRAMES_IN_MEM.keys())[-FRAMES_IN_MEM_LIMIT:]}
                socketio.emit('move', namespace='/state')
                socketio.emit('frame', image.tobytes(), namespace='/motion')
                bg = get_frame()
            else:
                socketio.emit('heartbeat', namespace='/data')
                socketio.emit('heartbeat', namespace='/state')
                image = cv2.imencode('.jpg', diff.marked_frame)[1]
                socketio.emit('frame', image.tobytes(), namespace='/live')
                # if UPDATE_FREQ != 0:
                #     counter += 1
                #     if counter % UPDATE_FREQ == 0:
                #         counter = 0
                #         image = cv2.imencode('.jpg', diff.marked_frame)[1]
                #         socketio.emit('frame',
                #                       image.tobytes(),
                #                       namespace='/stream')
        except Exception as e:
            print(e)
            socketio.emit('err', str(e), namespace='/state')

    global thread
    thread = None
    print('exit stream.')


@socketio.on('connect', namespace='/data')
@socketio.on('connect', namespace='/state')
def when_connect():
    global thread
    global CLIENTS
    CLIENTS[request.sid] = {'ip': request.headers.environ['REMOTE_ADDR'], 'connectAt': time.time(),
                            'header': request.headers}
    print('new connect with sid:', request.sid)
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    socketio.emit('clients_num', {'count': len(CLIENTS)}, namespace='/data')
    if len(FRAMES_IN_MEM) > 0:
        socketio.emit('frame', FRAMES_IN_MEM[max(FRAMES_IN_MEM.keys())], namespace='/motion')
    else:
        frame = get_frame()
        image = cv2.imencode('.jpg', frame)[1]
        socketio.emit('frame', image.tobytes(), namespace='/motion')


@socketio.on('disconnect', namespace='/data')
@socketio.on('disconnect', namespace='/state')
def when_disconnect():
    global CLIENTS
    del CLIENTS[request.sid]
    socketio.emit('clients_num', {'unit': 'stream_clients', 'count': len(CLIENTS)}, namespace='/data')
    print('clients num now:', len(CLIENTS))


if __name__ == '__main__':
    # run this script with `python3 app.py` instead of `flask run`
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
