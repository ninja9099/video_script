import R64.GPIO as GPIO
from time import sleep


def ProjectorOnOff(id, state):
    print "projector %s  is now is in  %s state" % (id, state)
    print("Testing R64.GPIO Module...")
    print("GPIO.ROCK      " + str(GPIO.ROCK))
    print("GPIO.BOARD     " + str(GPIO.BOARD))
    print("GPIO.BCM       " + str(GPIO.BCM))
    print("GPIO.OUT       " + str(GPIO.OUT))
    print("GPIO.IN        " + str(GPIO.IN))
    print("GPIO.HIGH      " + str(GPIO.HIGH))
    print("GPIO.LOW       " + str(GPIO.LOW))
    print("GPIO.PUD_UP    " + str(GPIO.PUD_UP))
    print("GPIO.PUD_DOWN  " + str(GPIO.PUD_DOWN))
    print("GPIO.VERSION   " + str(GPIO.VERSION))
    print("GPIO.RPI_INFO  " + str(GPIO.RPI_INFO))

    # Set Variables
    var_gpio_out = 16
    var_gpio_in = 18

    # GPIO Setup
    GPIO.setwarnings(True)
    GPIO.setmode(GPIO.BOARD)
    # Set up GPIO as an output, with an initial state of HIGH
    GPIO.setup(var_gpio_out, GPIO.OUT, initial=GPIO.HIGH)
    # Set up GPIO as an input, pullup enabled
    GPIO.setup(var_gpio_in, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Test Output
    print("")
    print("Testing GPIO Input/Output:")

    # Return state of GPIO
    var_gpio_state = GPIO.input(var_gpio_out)
    print("Output State : " + str(var_gpio_state))              # Print results
    sleep(1)
    GPIO.output(var_gpio_out, GPIO.LOW)                         # Set GPIO to LOW
    return True


ProjectorOnOff(1, "on")