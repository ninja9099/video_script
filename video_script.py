
import json
import time
import urllib2
import datetime
import multiprocessing

import numpy as np
import cv2



video_queue = ["1.mp4","2.flv","3.flv"]

def coil(Schedular):
    while True:
        for item in video_queue:
            cap = cv2.VideoCapture(item)
            while(cap.isOpened()):
                ret, frame = cap.read()
                if ret == True:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
                    cv2.setWindowProperty("window",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
                    cv2.imshow('window', frame)
                    # & 0xFF is required for a 64-bit system
                    if cv2.waitKey(30) & 0xFF == ord('q'):
                        break
                else:
                    break
            cap.release()
            cv2.destroyAllWindows()
    print 'CoilSpring is heating Hang On'
    time.sleep(4)

class Schedular(object):
    def __init__(self, data):
        self.__dict__= json.load(data) 


def fetch_data(url):
    response = urllib2.urlopen(url)
    current_schedular = Schedular(response)
    return current_schedular



if __name__ == '__main__':
    url = 'http://date.jsontest.com'
    current_response = fetch_data(url)
    p = multiprocessing.Process(target=coil, name="coil", args=(current_response,))
    p.start()
    while True:
        resource =fetch_data(url)
        if True:
            if p.is_alive():
                p.terminate()
                p.join()
            current_response = resource

            p = multiprocessing.Process(target=coil, name="coil", args=(current_response,))
            p.start()
            time.sleep(10)
            print 'sleeping master process lets slave continues to do his work'
        else:
            time.sleep(10)
        x = fetch_data('http://date.jsontest.com')
        print "Schedular date ==> {} time ==> {}".format(x.date, x.time)