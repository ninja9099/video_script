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
# GPIO.setup(4, GPIO.OUT)
update_flag = True


def glass(command):
    # if command ==  "opaque":
    #     GPIO.output(4, GPIO.LOW)
    # elif command == 'transparent':
    #     GPIO.output(4, GPIO.HIGH)
    return True

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
    global update_flag
    update_flag = False
    base_url =os.getcwd()
    for item in actions:
        if item.get('Action') == "Play File(s)":
            movie_name = item.get('MovieFile').split('/')[-1]
            if os.path.isfile(movie_name):
                print "file witn name %s already exist" %(movie_name)
                q.put(base_url + '/' + movie_name)
            else:
                filedata = urllib2.urlopen(item.get('MovieFile'))
                datatowrite = filedata.read()
                with open(base_url + '/' + movie_name, 'wb') as f:
                    f.write(datatowrite)
                    q.put(f.name)
    print  "video queue is  ----> ", q
    return True
    

def coil(q, isloop, actions, fromdate, todate):
    print "isloop variable is", isloop
    while not q.empty():
        for item in actions:
            print 'in item action'
            if item.get('Action') == 'Transparent':
                glass('transparent')
            if item.get('Action') == 'Wait':
                time.sleep(item.get('Interval')  * 60 if item.get('IntervalType') else 1)
            if item.get('Action') == 'Play File(s)':
                print "in play files"
                movie_name = item.get('MovieFile').split('/')[-1]
                cap = cv2.VideoCapture(q.get())
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
                glass('opaque')
                pass
        if fromdate > datetime.now().time() or todate < datetime.now().time():
           break    
        if not isloop:
            while todate > datetime.now().time():
                print "waiting for period to complete"
                time.sleep(10)
            # TODO implement busy waiting here in time if isloop is  false
    return True

class Schedular(object):
    def __init__(self, data):
        self.__dict__ = data


def fetch_data(url, data):
    response = requests.post(url=url, data=data)
    current_schedular = Schedular(response.json())
    return current_schedular


def StartVideo(url, data, q):
    current_response = fetch_data(url, data)
    if current_response.GetWemoScheduler[0].get('ActiveStatus'):
        actions = [item for item in current_response.GetWemoScheduler[0].get('WemoAction')]  
        video_queue_update = multiprocessing.Process(target=video_download_helper, name="coil",  args=(q,actions))
        if q.empty():
            print "please update video queue first to get started"
        if current_response.GetWemoScheduler[0].get('IsBetweenTime'):
            
            projection_dates = [datetime.strptime(item.get('ScheduleDate'), '%d-%b-%Y %H:%M:%S').date() for item in current_response.GetWemoScheduler[0].get('WemoReportDates')] 
            start_time = datetime.strptime(current_response.GetWemoScheduler[0].get('SchedulerFromDate'), "%m/%d/%Y %H:%M:%S %p").time()
            end_time = datetime.strptime(current_response.GetWemoScheduler[0].get('SchedulerToDate'), "%m/%d/%Y %H:%M:%S %p").time()
            video_play = multiprocessing.Process(target=coil, name="coil",  args=(q,current_response.GetWemoScheduler[0].get('ContinuousLoop'),actions, start_time, end_time))
            
            if datetime.now().time() >= start_time and datetime.now().date() in  projection_dates:
                ProjectorOnOff(1, "on")
                
                video_play.start()
                while video_play.is_alive():
                    print "playing video files .... Please Wait" 
                    time.sleep(20)
                video_play.join()

            if datetime.now().time() >= end_time :
                ProjectorOnOff(1, "off")
                if video_play.is_alive():
                    video_play.terminate()
                    video_queue_update.terminate()
                else:
                    pass
        if not current_response.GetWemoScheduler[0].get('IsBetweenTime'):
            '''write logic for the IsBetweenTime =0 and we gotcha'''
            projection_dates = [datetime.strptime(item.get('ScheduleDate'), '%d-%b-%Y %H:%M:%S') for item in current_response.GetWemoScheduler[0].get('WemoReportDates')] 
            # video_play = multiprocessing.Process(target=coil, name="coil",  args=(q,current_response.GetWemoScheduler[0].get('ContinuousLoop'),actions, projector_on__time, projector_off__time))
            pass

        global update_flag
        if update_flag or datetime.now().time() > datetime.strptime('23:00', '%H:%M').time():
            video_queue_update.start()
        while video_queue_update.is_alive():
            print "waiting for helper to update the video queue"
            time.sleep(10)
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
        StartVideo(url, data, q)
        print "back in video player main calee function"
        time.sleep(10)
        print "the gap that is provided between two runs"

