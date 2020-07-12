#!/usr/bin/env python3
from flask import Flask, request
import os
from werkzeug.utils import secure_filename

if not os.path.isdir('IMG'):
    os.mkdir('IMG')
app = Flask(__name__)


@app.route('/api/report/<cid>', methods=['POST', ])
def report(cid):
    print(cid)
    print(request.data)
    return 'ok'


@app.route('/api/upload/<cid>/<timestamp>', methods=['POST', ])
def upload(cid, timestamp):
    if not os.path.isdir('IMG/' + cid):
        os.mkdir('IMG/' + cid)
    print(cid, timestamp)
    f = request.files['file']
    basepath = os.path.dirname(__file__)  # 当前文件所在路径
    upload_path = os.path.join(basepath, 'IMG/' + cid, secure_filename(f.filename))
    print(upload_path)
    return 'ok'


if __name__ == '__main__':
    app.run(port=5011, host='0.0.0.0')
