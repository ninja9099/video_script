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
# import R64.GPIO as GPIO
from time import sleep
from multiprocessing import Process, Queue

# GPIO.setmode(GPIO.BCM)
# GPIO.setup(3, GPIO.OUT)


def ProjectorOnOff(id, state):
    # if state == 1:
    #     GPIO.output(3, GPIO.HIGH)
    # else:
    #     GPIO.output(3, GPIO.LOW)
    
    # print "projector %s  is now is in  %s state" % (id, state)
    return True


def internet_on():
    try:
        urllib2.urlopen('http://216.58.192.142', timeout=1)
        return True
    except urllib2.URLError as err:
        print err
        raise Exception("No Connectivity Please Check your internet connection")


def video_download_helper(q, actions):
    print "actions are ====> ", actions
    base_url =os.getcwd()
    for item in actions:
        print '\n',item.get('Action')
        if item.get('Action') == "Play File(s)":
            print "+++++++++++++++++++++++++++++++++++++++++++++++++++ in Play file", item.get('MovieFile')
            movie_name = item.get('MovieFile').split('/')[-1]
            filedata = urllib2.urlopen(item.get('MovieFile'))

            datatowrite = filedata.read()
            with open(base_url + movie_name, 'wb') as f:
                f.write(datatowrite)
                q.put(movie_name)
    print  "video queue is  ----> ", q
    return True
    

def coil(q, isloop, actions):
    print "isloop variable is", isloop

    while isloop and not q.empty():
        for item in actions:
            if item.get('Action') == 'Transparent':
                # glass.make_tran()
                pass
            if item.get('Action') == 'Wait':
                time.sleep(item.get('Interval')  * 60 if item.get('IntervalType') else 1)
            if item.get('Action') == 'Play File (s)':
                movie_name = item.get('MovieFile').split('/')[-1]
                cap = cv2.VideoCapture(movie_name)
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
            if item.get('Action') == 'Opaque':
                # glass.make_opeque()
                pass


class Schedular(object):
    def __init__(self, data):
        self.__dict__ = data


def fetch_data(url, data):
    response = requests.post(url=url, data=data)
    current_schedular = Schedular(response.json())
    return current_schedular




def StartVideo(url, data):
    current_response = fetch_data(url, data)
    if current_response.GetWemoScheduler[0].get('ActiveStatus'):
        projection_dates = [datetime.strptime(item.get('ScheduleDate'), '%d-%b-%Y %H:%M:%S').date() for item in current_response.GetWemoScheduler[0].get('WemoReportDates')] 
        actions = [item for item in current_response.GetWemoScheduler[0].get('WemoAction')] 
        
        projector_on__time = datetime.strptime(current_response.GetWemoScheduler[0].get('SchedulerFromDate'), "%m/%d/%Y %H:%M:%S %p").time()
        projector_off__time = datetime.strptime(current_response.GetWemoScheduler[0].get('SchedulerToDate'), "%m/%d/%Y %H:%M:%S %p").time()
    
        if current_response.GetWemoScheduler[0].get('IsBetweenTime'):
            if datetime.now().time() >= projector_on__time and datetime.now().date() in  projection_dates:
                ProjectorOnOff(1, "on")
                video_queue_update = multiprocessing.Process(target=video_download_helper, name="coil",  args=(q,actions))
                video_play = multiprocessing.Process(target=coil, name="coil",  args=(q,current_response.GetWemoScheduler[0].get('ContinuousLoop'),actions))
                video_play.start()
                while video_play.is_alive():
                    pass  
                video_play.join()

            if datetime.now().time() >= projector_off__time :
                ProjectorOnOff(1, "off")
                if video_play.is_alive():
                    video_play.terminate()
                    video_queue_update.terminate()
                else:
                    pass
        else:
            pass
        video_queue_update.start()
        
        while video_queue_update.is_alive():
            pass
        return True

    else:
        return True
        
    


    


if __name__ == '__main__':
    
    internet_on()
   
    data = {
        'AuthKey': "VLXFPwJfJEUqBjPhquC1QAhA+LFVfS3+p4zKcanYnUY=",
        'LocationId': 10
    }

    url = "http://rwscloud.devs-vipl.com/WebService/RWSCloudData.asmx/GetWemoScheduler"
    
    q = Queue()
    while True:
        StartVideo(url, data)
        time.sleep(10)
        print "the gap that is provided between two runs"

