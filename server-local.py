#!/usr/bin/env python3
"""
在树莓派上运行的http server，用于提供对截图、视频的访问
"""
from flask import Flask, send_from_directory, make_response, jsonify
import os
from glob import glob
from flask_httpauth import HTTPBasicAuth
from flask_compress import Compress
import json
from datetime import datetime, timedelta
import time

app = Flask(__name__)
Compress(app)
auth = HTTPBasicAuth()
timeOffset = timedelta(hours=8)
users = {
    'user': 'pwd241'
}


@auth.get_password
def get_pwd(username):
    if username in users:
        return users[username]
    else:
        return None


def list_files():
    files = glob('frames/*jpg')
    files.sort()
    return files


def list_stamps():
    data = list()
    files = glob('dumps/*json')
    files.sort()
    for i in files:
        data.append(json.load(open(i)))
    return data


def build_frame_history(min_stamp_ms: int):
    """
    从frames文件夹中的图片构建data
    :param min_stamp_ms: 时间戳，单位为秒，时间戳小于该值的图片才会参与构建
    :return:
    """
    print('min_stamp:', min_stamp_ms)
    t0 = time.time()
    m_data = dict()
    files = glob('frames/*jpg')
    files.sort()
    print('debug1:', time.time() - t0)
    for f in files:
        stamp = int(os.path.basename(f).split('.')[0])
        if stamp >= min_stamp_ms:
            # a python bug
            # date_m = (datetime.utcfromtimestamp(stamp / 1000)).strftime('%Y-%m-%d %H:%M') + ':00'
            # min_stamp = int(time.mktime(time.strptime(date_m, "%Y-%m-%d %H:%M:%S")))
            min_stamp = stamp // 60000 * 60
            if min_stamp not in m_data.keys():
                m_data[min_stamp] = []
                m_data[min_stamp].append(stamp)
            else:
                m_data[min_stamp].append(stamp)
    print('debug2:', time.time() - t0)
    return m_data


OLD_FRAME_HISTORY = build_frame_history(0)
LAST_MIN_TIMESTAMP_MS = max(OLD_FRAME_HISTORY.keys()) * 1000
# frames目录下没有数据时会出错


def combine_frames(old: dict, new: dict):
    for k, v in new.items():
        if k in old:
            old[k] = old[k] + new[k]
        else:
            old[k] = new[k]
    return old


@app.route('/files', methods=['GET', ])
@auth.login_required
def show_files():
    # print(files)
    return send_from_directory('static', 'files.html')


@app.route('/frames/<string:filename>', methods=['GET'])
def show_photo(filename):
    # image_data = open(os.path.join('frames', filename), "rb").read()
    # response = make_response(image_data)
    # response.headers['Content-Type'] = 'image/jpg'
    # return response
    return send_from_directory('frames', filename)


@app.route('/static/<string:filename>')
def send_static(filename):
    return send_from_directory('static', filename)


@app.route('/api/data')
def send_api():
    global LAST_MIN_TIMESTAMP_MS
    global OLD_FRAME_HISTORY
    LAST_MIN_TIMESTAMP_MS = max(OLD_FRAME_HISTORY.keys()) * 1000
    OLD_FRAME_HISTORY = combine_frames(OLD_FRAME_HISTORY, build_frame_history(LAST_MIN_TIMESTAMP_MS))

    data = list()
    t0 = time.time()

    for k, v in OLD_FRAME_HISTORY.items():
        data.append([k, len(v), v])
        # 整分钟时间戳，帧数，帧时间戳列表
    print('debug build:', time.time() - t0)
    return jsonify(data)


if __name__ == '__main__':
    app.run(port=5011, host='0.0.0.0', debug=False)
