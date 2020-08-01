#!/usr/bin/env python3
"""
在树莓派上运行的http server，用于提供对截图、视频的访问
"""
from flask import Flask, send_from_directory, render_template, make_response, jsonify
import os
from glob import glob
from flask_httpauth import HTTPBasicAuth
import json
from datetime import datetime, timedelta
import time

app = Flask(__name__)
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


def build_frame_history():
    m_data = dict()
    for f in glob('frames/*jpg'):
        stamp = int(os.path.basename(f).split('.')[0])
        # print(stamp)
        date_m = (datetime.utcfromtimestamp(stamp / 1000)).strftime('%Y-%m-%d %H:%M') + ':00'
        min_stamp = int(time.mktime(time.strptime(date_m, "%Y-%m-%d %H:%M:%S")))
        if min_stamp not in m_data.keys():
            m_data[min_stamp] = []
            m_data[min_stamp].append(stamp)
        else:
            m_data[min_stamp].append(stamp)
    data = list()
    for k, v in m_data.items():
        data.append({"stamps": v,
                     "min_stamp": k,
                     # 'date': (datetime.utcfromtimestamp(k) + timeOffset).strftime('%Y-%m-%d %H:%M') + ':00'
                     })
    return data


@app.route('/files', methods=['GET', ])
@auth.login_required
def files():
    files = list_files()[-10:]
    # print(files)
    return render_template('files.html', files=files)


@app.route('/frames/<string:filename>', methods=['GET'])
def show_photo(filename):
    image_data = open(os.path.join('frames', filename), "rb").read()
    response = make_response(image_data)
    response.headers['Content-Type'] = 'image/jpg'
    return response


@app.route('/static/<string:filename>')
def send_static(filename):
    return send_from_directory('static', filename)


@app.route('/api/data')
def send_api():
    # return jsonify(list_stamps())
    return jsonify(build_frame_history())


if __name__ == '__main__':
    app.run(port=5011, host='0.0.0.0')
