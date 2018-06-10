import R64.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setup(3, GPIO.OUT)

def ProjectorOnOff(id, state):
    if state == 1:
        GPIO.output(3, GPIO.HIGH)
    else:
        GPIO.output(3, GPIO.LOW)
    
    print "projector %s  is now is in  %s state" % (id, state)

ProjectorOnOff(1, "on")
