# rtm2

![python3.0+](https://img.shields.io/badge/python-3.0+-blue)
![PR](https://img.shields.io/badge/PRs-welcome-brightgreen)
[English](README.md) | 中文

**一个实时移动侦测程序**
![screenshot](doc/chart_page.PNG)

## Table of Contents
- [Introduction](#Introduction)
- [Install and usage](#Install)
- [Todo](#Todo)
- [Similar works](#Similar_works)

## Introduction
(还是中文readme比较好写)

**rtm2**是一个实时移动侦测程序，主要使用python+flask+[socketIO](https://socket.io/)+openCV开发，可跨平台，容易部署。
与类似程序的不同在于，rtm2只在检测到运动🏃的时候才推送视频帧给客户端。
服务端为树莓派、笔记本等带有摄像头的设备，在上面运行openCV和flask。
openCV负责抓取视频帧和比较视频帧之间的区别。发现区别后通过websocket把结果实时发送给浏览器，这样可以避免不必要的数据传输。
如果没有发现运动，就发送心跳包，告知浏览器等客户端通信正常。
检测到移动或通信异常时通过弹框、声音、震动（如手机等移动设备）等方式提醒用户。
移动侦测到的结果会存储在服务器上（可选），在网页上可以查看移动帧的历史情况。

不得不说，类似的使用openCV+web实现监控的项目有很多。据我观察，客户端获得openCV视频帧的方式有这么几种：
 1. ajax轮询
客户端每隔若干秒发送一次请求，服务器端如果有数据就返回给客户端

 2. 利用[multipart](https://www.w3.org/Protocols/rfc1341/7_2_Multipart.html)
网页写一个<img>标签，服务器不停地返回`multipart/x-mixed-replace; boundary=frame`这样的HTTP头，每次把捕获到的帧作为body返回给客户端
这种单次http请求-响应，如果网络中断，视频流就会终止，只能刷新再重连。如果画面大部分时间是不变的，那客户无法判断当前画面就是那样还是自己掉线了。
虽然说可以通过在视频上加入时间水印来解决，但总感觉不够优雅

 3. 使用[imageZMQ](https://github.com/jeffbass/imagezmq)
优点：实时+可分布式，缺点：不能在浏览器上显示，需要专用客户端

 4. 使用ffmpeg推流给rtmp服务器
  曲线救国？总感觉怪怪的
  
 5. websocket
服务器有图片需要发送给客户端时
 + 通过websocket把图片的url发送给客户端，然后客户端浏览器执行`img.src='http://domain.com/img/1.jpg'`
   如果高频率地修改img.src，会导致图片还没加载完就又切换到另一个url，结果是一张图片也显示不出来。帧率低时是个不错的方案
 + 对图片进行base64编码，之后使用websocket发送给客户端，然后客户端浏览器执行`img.src='data:image/png;base64,...'`
   使用base64进行编码，既增加了无意义的运算，又增加了传输的数据量
 + 通过websocket直接把图片的binary推送给客户端，然后客户端执行如下的js显示图片。我用的是这个方案
 ```js
    let blob = new Blob([msg], {type: 'image/jpeg'});
    img.src = window.URL.createObjectURL(blob);
 ```

## Install
### ubuntu
```shell script
$ wget https://github.com/def-fun/rtm2/master.zip
$ unzip master.zip
$ cd master/
$ sudo apt install python3 python3-pip
$ pip3 install -r requirements.txt
$ gunicorn --worker-class eventlet -w 1 app:app -b 0.0.0.0:5000
```
如果终端显示
```
[ WARN:0] global /io/opencv/modules/videoio/src/cap_v4l.cpp (802) open VIDEOIO ERROR: V4L: can't open camera by index 0
```
之类的信息，那可能是没有安装摄像头驱动，或者是当前用户没有打开摄像头的权限。
驱动可以在[这里](http://www.ideasonboard.org/uvc/)找到。权限不足的话可以这样搞
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
安装好python之后，下载[master.zip](https://github.com/def-fun/rtm2/master.zip) ，解压，打开cmd，cd到master目录
```
1. cd master/
1. pip install -r requirements.txt
python app.py
```

启动之后，需要有一次浏览器访问，移动侦测才会工作。浏览器打开http://127.0.0.1:5000/即可。
浏览器端默认为detect mode，即检测到移动时才更新画面，live mode为直播模式，[close]则关闭画面自动更新。
第一次运行时没有历史数据，画面会显示一直加载，刷新一次页面就行。
我摄像头分辨率640*480，拍摄的照片一张大约60KB，live模式需要1.8MB/s以上的宽带，而detect模式只在检测到动作时才更新。
![detect_mode_vs_live_mode](doc/detect_mode_vs_live_mode.PNG)
点击移动帧历史柱状图里面的竖条，可以查看其所对应的画面

## todo
+ 添加用户认证
+ 支持通过网页配置服务器
+ 优化网络传输，比如只传输发生变化的区域
+ 检测到变化时，使手机发生震动、响铃、打开LED等
+ ~~美化网页~~

~~我对开发不熟悉，~~希望各位大佬多多指教


## Similar_works
https://blog.miguelgrinberg.com/post/video-streaming-with-flask
https://gist.github.com/n3wtron/4624820 
https://github.com/Kr1s77/flask-video-streaming-recorder 
https://www.geeksforgeeks.org/webcam-motion-detector-python/ 
https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/ 
https://www.pyimagesearch.com/2019/04/15/live-video-streaming-over-network-with-opencv-and-imagezmq/
https://www.pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/ 

