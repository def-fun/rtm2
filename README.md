# rtm2

![python3.0+](https://img.shields.io/badge/python-3.0+-blue)
![PR](https://img.shields.io/badge/PRs-welcome-brightgreen)

**A real-time motion monitor**


## Table of Contents
- [introduction](#introduction)
- [Install and usage](#install)
- [Todo](#todo)
- [Similar projects](#similar_projects)

## introduction
rtm2 is a real-time motion monitor developed by python3, flask, [socketIO](https://socket.io/) and openCV.
Unlike [similar projects'](#similar_projects) transferring every frame to clients, rtm2 send frames and notices to clients using [websocket](https://en.wikipedia.org/wiki/WebSocket) protocol only when motion🏃 detected.
It can avoid unnecessary traffic transfer and send data real-time.
![screenshot](doc/chart_page.PNG)

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
    """Example of how to send openCV motion frames to clients."""
    print('start stream.')
    global history_frames
    counter = 0
    _, bg = camera.read()
    while len(clients) > 0:
        socketio.sleep(1.0 / FPS)
        try:
            _, frame = camera.read()
            diff = FrameDiff(bg, frame)
            diff.do_default()
            if diff.count > 0:  # send frames when motion detected.
                timestamp = round(time.time() * 1000)  # ms
                history_frames.append(timestamp)
                history_frames = history_frames[-HISTORY_LIMIT:]
                diff.save('frames/{}.jpg'.format(timestamp))
                image = cv2.imencode('.jpg', diff.marked_frame)[1]
                socketio.emit('frames',
                              image.tobytes(),
                              namespace='/test')
                _, bg = camera.read()
            else:
                socketio.emit('keep_alive', namespace='/test')
                counter += 1
            if counter % 20 == 0:
                image = cv2.imencode('.jpg', diff.marked_frame)[1]
                socketio.emit('frames',
                              image.tobytes(),
                              namespace='/test')
        except Exception as e:
            print(e)
            socketio.emit('stream_err',
                          namespace='/test')

    global thread
    thread = None
    print('exit stream.')
```


## Install

```sh
$ wget https://github.com/def-fun/rtm2/master.zip
$ unzip master.zip
$ cd master/
$ pip3 install -r requirements.txt
$ python3 app.py
```
then visit http://127.0.0.1:5000/


## todo
+ optimize network transfer, for example, transfer changed area only.
+ alarms or vibrate your device(mobile phone) when motion detected.
+ beautify web page

I'm not familiar with `html` `js` and `css`, and have little experience in programing.
So, current web page is very ugly, and many function have been finished. I hope someone could help me :)

## similar_projects
https://gist.github.com/n3wtron/4624820 
https://github.com/Kr1s77/flask-video-streaming-recorder 
https://www.geeksforgeeks.org/webcam-motion-detector-python/ 
https://www.pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/ 
https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/ 
