#!/usr/bin/env python3
"""
首次联网时，向服务器发送系统情况
在线通知
检测到动作时，立刻向服务器汇报，汇报完成后发送画面
每5秒钟最多允许发送1个画面
每秒钟最多保存2个画面
支持实时直播
"""
import json
import time
import cv2
import requests
import os
from datetime import datetime, timedelta

# import platform
from driver import FrameDiff

#######################################
#           configure start           #
#######################################
CONF = json.load(open('monitor-conf.json'))
print(CONF)
timeOffset = timedelta(hours=8)
# if platform.system() == 'Windows':
#     camera = cv2.VideoCapture(0)
# elif platform.system() == 'Linux':
#     camera = cv2.VideoCapture('/dev/video0')
camera = cv2.VideoCapture(0)
# camera = cv2.VideoCapture('vtest.avi')
# your camera

FPS = CONF.get('fps')
# frames per second, it based on your device performance. I think 10~40 is ok.

UPLOAD_MOTION_FRAMES = True
# save all motion frames to disk

FRAMES_IN_MEM_LIMIT = 64
# motion frames that cached in memory and can be shown in web page.

#######################################
#           configure end             #
#######################################

INTERVAL = 1.0 / FPS
for d in ['dumps', 'frames']:
    if not os.path.isdir(d):
        os.mkdir(d)


def upload(image_path, timestamp, try_count=0):
    return
    print('debug: upload()', image_path, try_count)
    try_count += 1
    if try_count > 3:
        return
    # files = {'file': ('report.xls', open('report.xls', 'rb'), 'application/vnd.ms-excel', {'Expires': '0'})}
    files = {'file': open(image_path, 'rb')}
    try:
        r = requests.post('http://{}/api/upload/{}/{}'.format(CONF['server'], CONF['cid'], timestamp), files=files,
                          timeout=10)
        print(r.text)
        if r.text == 'ok':
            return
        else:
            time.sleep(1)
            upload(image_path, timestamp, try_count)
    except Exception as e:
        print('retry upload...', e)
        upload(image_path, timestamp, try_count)


def report(timestamp, info, try_count=0):
    return
    try_count += 1
    if try_count > 3:
        return
    try:
        r = requests.post('http://{}/api/report/{}'.format(CONF['server'], CONF['cid']), timeout=3, data=info,
                          auth=(CONF['cid'], CONF['token']))
        if r.text == 'ok':
            return
        else:
            print('retry to report...')
            time.sleep(1)
            report(timestamp, info, try_count)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout) as e:
        print('debug report()', e)
        report(timestamp, info, try_count)


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
    last_upload_at = time.time()
    last_report_at = time.time()
    # global camera
    # camera = cv2.VideoCapture('vtest.avi')
    bg = get_frame()
    date_m = (datetime.utcnow() + timeOffset).strftime('%Y-%m-%d %H:%M') + ':00'
    min_stamp = time.mktime(time.strptime(date_m, "%Y-%m-%d %H:%M:%S"))
    stamps = {'stamps': [], 'min_stamp': min_stamp, 'date': date_m, 'cid': CONF['cid']}
    while True:
        time.sleep(INTERVAL)
        # try:
        frame = get_frame()
        diff = FrameDiff(bg, frame)
        diff.do_default()
        if diff.count > 0:  # send frames and notices when motion detected.
            print('diff: {}, area: {}'.format(diff.count, diff.area))
            timestamp = round(time.time() * 1000)  # ms
            # report(timestamp, info='move', try_count=0)
            if timestamp / 1000 - min_stamp < 60:
                stamps['stamps'].append(timestamp)
            else:
                dump_path = 'dumps/{}.json'.format(int(min_stamp))
                print('save dump:', dump_path)
                stamps['count'] = len(stamps['stamps'])
                json.dump(stamps, open(dump_path, 'w'))
                date_m = (datetime.utcnow() + timeOffset).strftime('%Y-%m-%d %H:%M') + ':00'
                min_stamp = time.mktime(time.strptime(date_m, "%Y-%m-%d %H:%M:%S"))
                stamps = {'stamps': [], 'min_stamp': min_stamp, 'date': date_m, 'cid': CONF['cid']}

            if UPLOAD_MOTION_FRAMES and (time.time() - last_upload_at > 0.5):
                # image = cv2.imencode('.jpg', diff.marked_frame)[1]
                # image.tobytes()
                save_path = 'frames/{}.jpg'.format(timestamp)
                diff.save(save_path)
                upload(save_path, timestamp, try_count=0)
                last_upload_at = time.time()

            bg = get_frame()
        else:
            if time.time() - last_report_at > 0.5:
                report(time.time(), 'online', try_count=0)
                last_report_at = time.time()
        # except Exception as e:
        #     print(e)


if __name__ == '__main__':
    main()
