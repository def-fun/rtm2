#!/usr/bin/env python3
"""
在树莓派上运行的http server，用于提供对截图、视频的访问
"""
from flask import Flask, request, render_template, make_response
import os
from glob import glob
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)


def list_files():
    files = glob('frames/*jpg')
    files.sort()
    return files


@app.route('/files', methods=['GET', ])
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


if __name__ == '__main__':
    app.run(port=5011, host='0.0.0.0')
