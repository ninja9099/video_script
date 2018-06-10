import os
import sys
import time
import json
import getpass
import urllib2
import requests
import multiprocessing
import numpy as np
import cv2

from datetime import datetime
import R64.GPIO as GPIO
from time import sleep
from multiprocessing import Process, Queue


def ProjectorOnOff(id, state):
    print "projector %s  is now is in  %s state" %(id, state)
    # print("Testing R64.GPIO Module...")
    # print("GPIO.ROCK      " + str(GPIO.ROCK))
    # print("GPIO.BOARD     " + str(GPIO.BOARD))
    # print("GPIO.BCM       " + str(GPIO.BCM))
    # print("GPIO.OUT       " + str(GPIO.OUT))
    # print("GPIO.IN        " + str(GPIO.IN))
    # print("GPIO.HIGH      " + str(GPIO.HIGH))
    # print("GPIO.LOW       " + str(GPIO.LOW))
    # print("GPIO.PUD_UP    " + str(GPIO.PUD_UP))
    # print("GPIO.PUD_DOWN  " + str(GPIO.PUD_DOWN))
    # print("GPIO.VERSION   " + str(GPIO.VERSION))
    # print("GPIO.RPI_INFO  " + str(GPIO.RPI_INFO))


    # # Set Variables
    # var_gpio_out = 16
    # var_gpio_in = 18

    # # GPIO Setup
    # GPIO.setwarnings(True)
    # GPIO.setmode(GPIO.BOARD)
    # # Set up GPIO as an output, with an initial state of HIGH
    # GPIO.setup(var_gpio_out, GPIO.OUT, initial=GPIO.HIGH)
    # # Set up GPIO as an input, pullup enabled
    # GPIO.setup(var_gpio_in, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # # Test Output
    # print("")
    # print("Testing GPIO Input/Output:")

    # # Return state of GPIO
    # var_gpio_state = GPIO.input(var_gpio_out)
    # print("Output State : " + str(var_gpio_state))              # Print results
    # sleep(1)
    # GPIO.output(var_gpio_out, GPIO.LOW)                         # Set GPIO to LOW
    return True


def internet_on():
    try:
        urllib2.urlopen('http://216.58.192.142', timeout=1)
        return True
    except urllib2.URLError as err:
        print err
        raise Exception("No Connectivity Please Check your internet connection")


def video_download_helper(q):
    paths = ['/1.avi','/2.mp4']
    base_url =os.getcwd()
    for item in paths:
        filedata = urllib2.urlopen("http://localhost:8000/static/src/videos/" + item)
        datatowrite = filedata.read()
        
        with open(base_url + str(item), 'wb') as f:
            f.write(datatowrite)
            q.put(f.name.split('/')[-1])
    print  "video queue is  ----> ", q
    return True
    

def coil(q):
    while True:
        if not q.empty():
            item = q.get()
            print "no item is  ", item
            cap = cv2.VideoCapture(item)
            while(cap.isOpened()):
                ret, frame = cap.read()
                if ret == True:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
                    cv2.setWindowProperty(
                        "window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                    cv2.imshow('window', frame)
                    # & 0xFF is required for a 64-bit system
                    if cv2.waitKey(30) & 0xFF == ord('q'):
                        break
                else:
                    break
            cap.release()
            cv2.destroyAllWindows()
            coil(q)
        else:
            return True

class Schedular(object):
    def __init__(self, data):
        print data
        self.__dict__ = data


def fetch_data(url, data):
    response = requests.post(url=url, data=data)
    current_schedular = Schedular(response.json())
    return current_schedular




def StartVideo(url, data):
    current_response = fetch_data(url, data)
    on_schedule = {}
    off_schedule = {}
    for item in current_response.GetWemoScheduler:
        if item['SchedulerName'] =='ProjectorOn':
            on_schedule = item
        if item['SchedulerName'] == "ProjectorOff":
            off_schedule = item
    
    

    projector_on__date = datetime.strptime(on_schedule['SchedulerStartDate'], "%d/%m/%Y %H:%M:%S %p")
    projector_off__date = datetime.strptime(off_schedule['SchedulerStartDate'], "%d/%m/%Y %H:%M:%S %p")
    

    if current_date >= projector_on__date:
        ProjectorOnOff(1, "on")
    if current_date >= projector_off__date:
        ProjectorOnOff(1, "off")

    video_queue_update = multiprocessing.Process(target=video_download_helper, name="coil",  args=(q,))
    video_play = multiprocessing.Process(target=coil, name="coil",  args=(q,))
    
    video_play.start()
    while video_play.is_alive():
        pass  
    video_play.join()

    if 3 > 2:
        video_queue_update.start()
    
    return True


if __name__ == '__main__':
    internet_on()
    last_date = datetime.strptime(
        '3/1/2018 9:42:00 AM', "%d/%m/%Y %H:%M:%S %p")
    current_date = datetime.now()
    data = {
        'AuthKey': "VLXFPwJfJEUqBjPhquC1QAhA+LFVfS3+p4zKcanYnUY=",
        'LocationId': 4
    }

    url = "http://rwscloud.devs-vipl.com/WebService/RWSCloudData.asmx/GetWemoScheduler"
    
    q = Queue()
    while True:
        StartVideo(url, data)
        print "the gap that is provided between two runs"

