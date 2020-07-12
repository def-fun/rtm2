#!/usr/bin/env python3
"""
首次联网时，向服务器发送系统情况
在线通知
检测到动作时，立刻向服务器汇报，汇报完成后发送画面
每5秒钟最多允许发送1个画面
每秒钟最多保存2个画面
支持实时直播
"""
from threading import Lock
import requests
import cv2
import time
import json
import os
# import platform
from driver import FrameDiff, timestamps2xyz

#######################################
#           configure start           #
#######################################
CONF = json.load(open('client-conf.json'))
print(CONF)
# if platform.system() == 'Windows':
#     camera = cv2.VideoCapture(0)
# elif platform.system() == 'Linux':
#     camera = cv2.VideoCapture('/dev/video0')
camera = cv2.VideoCapture(0)
# camera = cv2.VideoCapture('vtest.avi')
# your camera

FPS = CONF.get('fps')
# frames per second, it based on your device performance. I think 10~40 is ok.

SAVE_MOTION_FRAMES = False
# save all motion frames to disk

FRAMES_IN_MEM_LIMIT = 64
# motion frames that cached in memory and can be shown in web page.

#######################################
#           configure end             #
#######################################


FRAMES_IN_MEM = dict()  # {timestamp1: frame_binary1, timestamp2: frame_binary2}
NEW_TIMESTAMPS = []  # frames timestamps that obtained from last run
OLD_TIMESTAMPS = []  # old frames timestamps list
for i in os.listdir('frames'):
    if i.endswith('.jpg'):
        OLD_TIMESTAMPS.append(int(i.split('.')[0]))
OLD_TIMESTAMPS_OUT = timestamps2xyz(sorted(OLD_TIMESTAMPS))
INTERVAL = 1.0 / FPS


def upload(image_path, timestamp, try_count=0):
    try_count += 1
    if try_count > 3:
        return
    # files = {'file': ('report.xls', open('report.xls', 'rb'), 'application/vnd.ms-excel', {'Expires': '0'})}
    files = {'file': open(image_path, 'rb')}
    r2 = requests.post('http://%s/upload/%s/%s'.format(CONF['server'], CONF['cid'], timestamp), files=files, timeout=10)
    if r2.text == 'ok':
        return
    else:
        time.sleep(1)
        upload(image_path, timestamp, try_count)


def report(timestamp, info, try_count=0):
    try_count += 1
    if try_count > 3:
        return
    r = requests.post('http://%s/api/report/%s'.format(CONF['server'], CONF['cid']), timeout=5, data=info,
                      auth=(CONF['cid'], CONF['token']))
    if r.text == 'ok':
        return
    else:
        time.sleep(1)
        report(timestamp, info)


def get_frame():
    try:
        _, frame = camera.read()
        return frame
    except Exception as e:
        print('debug "get_frame()":', e)
        return cv2.imread('./static/stream_error.jpg')


def main():
    """detect and send motion frames to server."""
    print('start detection.')
    global FRAMES_IN_MEM
    global NEW_TIMESTAMPS
    last_upload_at = time.time()
    # global camera
    # camera = cv2.VideoCapture('vtest.avi')
    bg = get_frame()
    while True:
        time.sleep(INTERVAL)
        try:
            frame = get_frame()
            diff = FrameDiff(bg, frame)
            diff.do_default()
            if diff.count > 0:  # send frames and notices when motion detected.
                timestamp = round(time.time() * 1000)  # ms
                report(timestamp, info='motion detected!', try_count=0)

                if SAVE_MOTION_FRAMES and (time.time() - last_upload_at > 0.5):
                    # image = cv2.imencode('.jpg', diff.marked_frame)[1]
                    # image.tobytes()
                    save_path = 'frames/{}.jpg'.format(timestamp)
                    diff.save(save_path)
                    upload(save_path, timestamp, try_count=0)
                    last_upload_at = time.time()

                bg = get_frame()
            else:
                report(time.time(), 'online', try_count=0)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
