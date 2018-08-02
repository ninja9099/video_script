import json
import requests
import pprint
import os
import sys
import shutil
import time as stm
import json
import getpass
import urllib2
import requests
import multiprocessing
import numpy as np
import cv2
import configparser
from datetime import datetime, timedelta, time
import vlc
import ASUS.GPIO as GPIO
from multiprocessing import Process, Queue
from subprocess import call


PROJECTOR_OFF = True

GPIO.setmode(GPIO.BOARD)
GPIO.setup(3, GPIO.OUT)
GPIO.setup(5, GPIO.OUT)
GPIO.output(3, GPIO.HIGH)
GPIO.output(5, GPIO.HIGH)
pp = pprint.PrettyPrinter()

def glass(command):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(3, GPIO.OUT)
    print "in glass function", command
    if command ==  "opaque":
        GPIO.output(3, GPIO.LOW)
	stm.sleep(1)
    if command == "transparent":
        GPIO.output(3, GPIO.HIGH)
        stm.sleep(1)
    return True

def ProjectorOnOffSwitch(pin, state):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(5, GPIO.OUT)
    if state == 'off':
        GPIO.output(5, GPIO.HIGH)
    if state == 'on':
        GPIO.output(5, GPIO.LOW)
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
            if os.path.isfile(base_url + '/vids/' + movie_name):
                print "file witn name %s already exist" %(movie_name)
                video_q.put(base_url + '/vids/' + movie_name)
            else:
                filedata = urllib2.urlopen(item.get('MovieFile'))
                datatowrite = filedata.read()
                with open(base_url + '/vids/' + movie_name, 'wb') as f:
                    f.write(datatowrite)
                    video_q.put(f.name)
    print  "video queue is  ----> ", video_q
    return True

def coil(video_q, loops):
    actions = []
    try:
        loop_schedule = loops[0]
    except:
        raise Exception("No Schedulares found Exiting.....! ")
        return True

    for actn in loop_schedule.get('WemoAction'):
        actions.insert(actn.get('SrNo'), actn)
    print actions
    start_time = datetime.strptime(loop_schedule.get('SchedulerFromDate'), "%m/%d/%Y %I:%M:%S %p").time()
    end_time = datetime.strptime(loop_schedule.get('SchedulerToDate'), "%m/%d/%Y %I:%M:%S %p").time()
    projection_dates = [datetime.strptime(item.get('ScheduleDate'), '%d-%b-%Y %H:%M:%S').date() for item in loop_schedule.get('WemoReportDates')] 

    if video_q.empty():
        print 'updating queues please wait !'
        video_download_helper(video_q, actions)
    print 'in coil spring out', video_q.empty(), start_time, datetime.now().time().replace(microsecond=0), end_time
    while True: #not video_q.empty() and datetime.now().time().replace(microsecond=0) >= start_time and datetime.now().time().replace(microsecond=0) < end_time:
        new_video_q = video_q
        actions = sorted(actions, key=lambda x: x.get('SrNo'))
        for item in actions:
            print 'in item action ==> and sequesnce number is ', item.get('Action'),item.get('SrNo')
            if item.get('ActionId') == 2:
                print "in transparent action"
                glass('transparent')
            elif item.get('ActionId') == 0:
                img = cv2.imread('joker.png',0)
                cv2.namedWindow('image', cv2.WND_PROP_FULLSCREEN)
                cv2.setWindowProperty("image", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
                interval  = item.get('Interval')* (60 if item.get('IntervalType') else 1) 
                cv2.imshow('image',img)
                cv2.waitKey(interval*1000)
                cv2.destroyAllWindows()
		for i in range (1,5):
    		    cv2.waitKey(1)
            elif item.get('ActionId') == 1:
                print "in play files"
                movie_name = item.get('MovieFile').split('/')[-1]
                '''cap = capture =cv2.VideoCapture(video_q.get())
                while(cap.isOpened()):
                    ret, frame = cap.read()
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    cv2.imshow('frame',gray)
                    cv2.waitKey(20)
                cap.release()
                cv2.destroyAllWindows()'''
		#call(['vlc --fullscreen --play-and-exit ' + video_q.get()], shell=True)
                #call('gst-launch-1.0 playbin uri=file://' + video_q.get() + '| video-sink=imxipuvideosink', shell=True)
                x = video_q.get()
		call(['mpv --fullscreen ' + x ], shell=True)

            elif item.get('ActionId') == 3:
                glass('opaque')
            else:
                pass
        coil(new_video_q, loops)


def get_schedule(url, data):
    response = requests.post(url=url, data=data)
    return response.json() 

def ProjectorOnOff(schedulers):

    for schedule in schedulers:
        for sch_action in schedule.get('WemoAction'):
            if sch_action.get('ActionId') == 2:
                projection_dates = [datetime.strptime(p_date.get('ScheduleDate'),'%d-%b-%Y %H:%M:%S').date() for p_date in schedule.get('WemoReportDates')]
                on_time = datetime.strptime(schedule.get('SchedulerStartDate'), '%m/%d/%Y %I:%M:%S %p').time()
            else:
                off_time = datetime.strptime(schedule.get('SchedulerStartDate'), '%m/%d/%Y %I:%M:%S %p').time()

    print "+++++++++++++++++++++++++++++++++++++>",on_time, off_time            
    while True:
        global PROJECTOR_OFF
        if datetime.now().date() in projection_dates:
            if on_time <= datetime.now().time().replace(microsecond=0) <= off_time and PROJECTOR_OFF:
                ProjectorOnOffSwitch(3, 'on')
                PROJECTOR_OFF = False
                print "projector is on now"
            else:
                ProjectorOnOffSwitch(3, 'off')
                PROJECTOR_OFF = True
                print "projector is off now"
        stm.sleep(10)



def WemoSchedular(current_schedular, video_q, on_off_queue):
    one_time_runs = [sched for sched in current_schedular['GetWemoScheduler'] if not sched.get('IsBetweenTime')]
    loops = [sched for sched in current_schedular['GetWemoScheduler'] if sched.get('IsBetweenTime')]

    p_on_off = multiprocessing.Process(target=ProjectorOnOff, name="ProjectorOnOff",  args=(one_time_runs,))
    video_play = multiprocessing.Process(target=coil, name="coil",  args=(video_q, loops))
    p_on_off.start()
    video_play.start()
    print 'blocking on the process to complete the execution'
    video_play.join()

    if time(23, 00) <  datetime.now().time().replace(microsecond=0) < time(23, 59):
        for root, dirs, files in os.walk(os.getcwd() + '/vids/'):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
    return True


if __name__ == '__main__':
    data = {}
    config = configparser.ConfigParser()
    config.read('config.ini')
    for key in config['DEFAULT']:
        if key == "authkey":
            data.update({'AuthKey':config['DEFAULT'][key]})
        if key  == "locationid":
            data.update({'LocationId':config['DEFAULT'][key]})
    internet_on()
    url = "http://rwscloud.devs-vipl.com/WebService/RWSCloudData.asmx/GetWemoScheduler"    
    video_q = Queue()
    on_off_queue = Queue()
    
    while True:
        schedular = get_schedule(url, data)
        WemoSchedular(schedular, video_q, on_off_queue)
