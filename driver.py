#!/usr/bin/env python3
import cv2
# from skimage.measure import compare_ssim
from datetime import datetime, timedelta
import time
import json

es = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 4))


def mark_time(frame):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = (255, 255, 255)
    position = (20, 20)
    cv2.putText(frame, time_str, position, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 1)
    return frame


class FrameDiff:
    def __init__(self, bg, frame):
        self.gray_bg = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
        self.gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.frame = frame
        self.bg = bg
        self.marked_frame = None
        self.count = 0
        self.area_limit = 400  # 800
        self.area = 0

    # def ssim(self):
    #     self.count = 0
    #     # https://stackoverflow.com/questions/56183201/detect-and-visualize-differences-between-two-images-with-opencv-python
    #     (score, diff) = compare_ssim(self.gray_bg, self.gray_frame, full=True)
    #     print("Image similarity", score)
    #     diff = (diff * 255).astype("uint8")
    #     thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    #     contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #     contours = contours[0] if len(contours) == 2 else contours[1]
    #
    #     for c in contours:
    #         self.count += 1
    #         area = cv2.contourArea(c)
    #         if area > self.area_limit:
    #             x, y, w, h = cv2.boundingRect(c)
    #             cv2.rectangle(self.frame, (x, y), (x + w, y + h), (36, 255, 12), 2)
    #     self.marked_frame = mark_time(self.frame)

    def do_default(self):
        self.count = 0
        g_factor = 21  # 21
        bg = cv2.GaussianBlur(self.gray_bg, (g_factor, g_factor), 0)
        frame = cv2.GaussianBlur(self.gray_frame, (g_factor, g_factor), 0)
        diff = cv2.absdiff(bg, frame)
        diff = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
        diff = cv2.dilate(diff, es, iterations=2)
        contours, _ = cv2.findContours(diff.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:  # mark differences
            if cv2.contourArea(c) > self.area_limit:  # ignore small differences
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(self.frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                self.count += 1
                self.area += w * h
        self.marked_frame = mark_time(self.frame)

    def save(self, path):
        cv2.imwrite(path, self.marked_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

    def show(self):
        cv2.imshow('marked_frame', self.marked_frame)


def ts2dates(timestamp):
    time_local = time.localtime(timestamp / 1000)
    dt = time.strftime("%Y-%m-%d\n%H:%M:%S", time_local)
    return dt


def timestamps2xyz(timestamp_list: list):
    if len(timestamp_list) < 2:
        return []
    date_json = dict()
    for t in timestamp_list:
        # d = ts2dates(t)
        ts = int(t / 1000) * 1000
        if date_json.get(ts) is None:
            date_json[ts] = []
        date_json[ts].append(t)
    return [(k, len(date_json[k]), date_json[k]) for k in sorted(date_json.keys())]

    # out_data = []
    # date_json_keys = sorted(date_json.keys())
    # for ts in range(int(timestamp_list[0] / 1000) - 2, int(timestamp_list[-1]) + 2):
    #     date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d\n%H:%M:%S")
    #     if date_str in date_json_keys:
    #         out_data.append([date_str, 0])
    #         timestamps = []
    #         count = 0
    #         for t in date_json[date_str]:
    #             timestamps.append(t)
    #             count += 1
    #         out_data.append([date_str, count, timestamps])
    # return out_data
