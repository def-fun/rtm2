# rtm2

![python3.0+](https://img.shields.io/badge/python-3.0+-blue)
![PR](https://img.shields.io/badge/PRs-welcome-brightgreen)
English | [中文](README-zh.md)

**A real-time motion monitor**
![screenshot](doc/chart_page.PNG)

## Table of Contents
- [Introduction](#Introduction)
- [Install and usage](#Install)
- [Todo](#Todo)
- [Similar projects](#Similar_works)

## Introduction
**rtm2** is a real-time motion monitor developed by python3, flask, [socketIO](https://socket.io/) and openCV.
Unlike [similar projects'](#Similar_works) transferring every frame to clients, rtm2 send frames and notices to clients using [websocket](https://en.wikipedia.org/wiki/WebSocket) protocol only when motion🏃 detected.
It can avoid unnecessary traffic transfer and send data real-time.


some project transfer base64ed images/frames and decode it after transfer:
```python
def video_thread():
    print('send')
    while True:
        image = cv2.imencode('.jpg', frame)[1]
        base64_data = base64.b64encode(image)
        s = base64_data.decode()
        server.send_message_to_all(s)
```

and some project transfer all frames to clients:
```python
def gen(camera):
    frame = camera.getFrame()
    while frame != None:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        time.sleep(0.06)
        frame = camera.getFrame()
```

and what i do here:
```python
def background_thread():
    """send openCV motion frames to clients."""
    ...
    while (len(CLIENTS) > 0) or KEEP_DETECT:
        socketio.sleep(1.0 / FPS)
            _, frame = camera.read()
            diff = FrameDiff(bg, frame)
            diff.do_default()
        if diff.count > 0:  # send frames and notices when motion detected.
           
            socketio.emit('update', [int(update_cache[0] / 1000) * 1000, 1, [update_cache[0]]],
                          namespace='/data')
        else:
            if SAVE_MOTION_FRAMES:
                diff.save('frames/{}.jpg'.format(timestamp))
                image = cv2.imencode('.jpg', diff.marked_frame)[1]
            socketio.emit('move', namespace='/state')
            socketio.emit('frame',
                              image.tobytes(),
                          namespace='/motion')
                _, bg = camera.read()
            else:
            socketio.emit('heartbeat', namespace='/data')
            socketio.emit('heartbeat', namespace='/state')

    global thread
    thread = None
    print('exit stream.')
```


## Install
### ubuntu
```shell script
$ wget https://github.com/def-fun/rtm2/master.zip
$ unzip master.zip
$ cd master/
$ pip3 install -r requirements.txt
$ gunicorn --worker-class eventlet -w 1 app:app -b 0.0.0.0:5000  # ubuntu
```
then visit http://127.0.0.1:5000/


If terminal shows something like:
```
[ WARN:0] global /io/opencv/modules/videoio/src/cap_v4l.cpp (802) open VIDEOIO ERROR: V4L: can't open camera by index 0
```
it means you need to install right webcam drive (note: you can get driver from http://www.ideasonboard.org/uvc/),
 or run command with `sudo`.
```shell script
[def@ubuntu ~/rtm2/rtm2]$ which gunicorn 
/home/def/.local/bin/gunicorn
[def@ubuntu ~/rtm2/rtm2]$ sudo /home/def/.local/bin/gunicorn --worker-class eventlet -w 1 app:app -b 0.0.0.0:5000
[2020-03-23 11:35:17 +0800] [4861] [INFO] Starting gunicorn 20.0.4
[2020-03-23 11:35:17 +0800] [4861] [INFO] Listening at: http://0.0.0.0:5000 (4861)
[2020-03-23 11:35:17 +0800] [4861] [INFO] Using worker: eventlet
[2020-03-23 11:35:17 +0800] [4864] [INFO] Booting worker with pid: 4864
ImmutableMultiDict([('num', '1000'), ('q', 'frames_list')])
new connect with sid: 24cae136c62b429caf12f21e31d8727e
start detection.
clients num now: 1
ImmutableMultiDict([('num', '1000'), ('q', 'frames_list')])
new connect with sid: e90e133a208d492392415439678f2006

```

### windows
install python3 first, then download [master.zip](https://github.com/def-fun/rtm2/master.zip) and uncompressed it.
Open cmd
```
1. cd master/
1. pip install -r requirements.txt
python app.py
```


## Todo
+ optimize network transfer, for example, transfer changed area only.
+ alarms or vibrate your device(mobile phone) when motion detected.
+ beautify web page

I'm not familiar with `html` `js` and `css`, and have little experience in programing.
So, current web page is very ugly, and many function haven't been finished. I hope someone could help me :)

## Similar_works
https://www.pyimagesearch.com/2019/04/15/live-video-streaming-over-network-with-opencv-and-imagezmq/
https://blog.miguelgrinberg.com/post/video-streaming-with-flask
https://gist.github.com/n3wtron/4624820 
https://github.com/Kr1s77/flask-video-streaming-recorder 
https://www.geeksforgeeks.org/webcam-motion-detector-python/ 
https://www.pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/ 
https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/ 
