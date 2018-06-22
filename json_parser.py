import json
import requests
import pprint
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
# GPIO.setup(2, GPIO.OUT)
# GPIO.setup(3, GPIO.OUT)
pp = pprint.PrettyPrinter()

def glass(command):
    print "in glass function", command
    # if command ==  "opaque":
    #     GPIO.output(2, GPIO.LOW)
    # elif command == 'transparent':
    #     GPIO.output(2, GPIO.HIGH)
    return True

def ProjectorOnOffSwitch(pin, state):
    # if state == 'off':
    #     GPIO.output(3, GPIO.HIGH)
    # if state == 'on':
    #     GPIO.output(3, GPIO.LOW)
    return True

def internet_on():
    try:
        urllib2.urlopen('http://216.58.192.142', timeout=1)
        return True
    except urllib2.URLError as err:
        print err
        raise Exception("No Connectivity Please Check your internet connection")

def video_download_helper(video_q, actions):
    base_url =os.getcwd()
    for item in actions:
        if item.get('Action') == "Play File(s)":
            movie_name = item.get('MovieFile').split('/')[-1]
            if os.path.isfile(movie_name):
                print "file witn name %s already exist" %(movie_name)
                video_q.put(base_url + '/' + movie_name)
            else:
                filedata = urllib2.urlopen(item.get('MovieFile'))
                datatowrite = filedata.read()
                with open(base_url + '/' + movie_name, 'wb') as f:
                    f.write(datatowrite)
                    video_q.put(f.name)
    print  "video queue is  ----> ", video_q
    return True

def coil(video_q, loops):
    actions = []
    loop_schedule = loops[0]
    for actn in loop_schedule.get('WemoAction'):
        actions.insert(actn.get('SrNo'), actn)
    start_time = datetime.strptime(loop_schedule.get('SchedulerFromDate'), "%m/%d/%Y %I:%M:%S %p").time()
    end_time = datetime.strptime(loop_schedule.get('SchedulerToDate'), "%m/%d/%Y %I:%M:%S %p").time()
    projection_dates = [datetime.strptime(item.get('ScheduleDate'), '%d-%b-%Y %H:%M:%S').date() for item in loop_schedule.get('WemoReportDates')] 
    
    if video_q.empty():
        print 'updating queues please wait !'
        video_download_helper(video_q, actions)
    print 'in coil spring out', video_q.empty(), start_time, datetime.now().time().replace(microsecond=0), end_time
    while True: #not video_q.empty() and datetime.now().time().replace(microsecond=0) >= start_time and datetime.now().time().replace(microsecond=0) < end_time:
        new_video_q = video_q
        for item in actions:
            print 'in item action==>', item.get('Action')
            if item.get('Action') == 'Transparent':
                glass('transparent')
            if item.get('Action') == 'Wait':
                time.sleep(item.get('Interval')  * 60 if item.get('IntervalType') else 1)
            if item.get('Action') == 'Play File(s)':
                print "in play files"
                movie_name = item.get('MovieFile').split('/')[-1]
                cap = cv2.VideoCapture(video_q.get())
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
        coil(new_video_q, loops)


def get_schedule(url, data):
    response = requests.post(url=url, data=data)
    return response.json() 

def ProjectorOnOff(schedulers):
    projector_status = False
    for schedule in schedulers:
        for sch_action in schedule.get('WemoAction'):
            if sch_action.get('Action') == 'Transparent':
                projection_dates = [datetime.strptime(p_date.get('ScheduleDate'),'%d-%b-%Y %H:%M:%S').date() for p_date in schedule.get('WemoReportDates')]
                on_time = datetime.strptime(schedule.get('SchedulerStartDate'), '%m/%d/%Y %I:%M:%S %p').time()
            else:
                off_time = datetime.strptime(schedule.get('SchedulerStartDate'), '%m/%d/%Y %I:%M:%S %p').time()


    while True:
        if datetime.now().date() in projection_dates:
            if on_time <= datetime.now().time().replace(microsecond=0) <= off_time:
                if not projector_status:
                    ProjectorOnOffSwitch(3, 'on')
                    print "projector is on now"
                    projector_status = True
            else:
                ProjectorOnOffSwitch(3, 'off')
                projector_status = False
        time.sleep(10)



def WemoSchedular(current_schedular, video_q, on_off_queue):
    one_time_runs = [sched for sched in current_schedular['GetWemoScheduler'] if not sched.get('IsBetweenTime')]
    loops = [sched for sched in current_schedular['GetWemoScheduler'] if sched.get('IsBetweenTime')]

    p_on_off = multiprocessing.Process(target=ProjectorOnOff, name="ProjectorOnOff",  args=(one_time_runs,))
    video_play = multiprocessing.Process(target=coil, name="coil",  args=(video_q, loops))
    p_on_off.start()
    video_play.start()
    print 'blocking on the process to complete the execution'
    video_play.join()

    return True


if __name__ == '__main__':
    
    internet_on()
    data = {
        'AuthKey': "VLXFPwJfJEUqBjPhquC1QAhA+LFVfS3+p4zKcanYnUY=",
        'LocationId': 10
    }
    url = "http://rwscloud.devs-vipl.com/WebService/RWSCloudData.asmx/GetWemoScheduler"    
    video_q = Queue()
    on_off_queue = Queue()
    
    while True:
        schedular = get_schedule(url, data)
        WemoSchedular(schedular, video_q, on_off_queue)
        print "Sleeping for some rest See you Soon !"
        time.sleep(1)