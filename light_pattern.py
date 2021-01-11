# Import modules
from gpiozero import LED, Button, PWMLED, Buzzer
from smbus import SMBus
from signal import pause
from time import sleep
from threading import Thread

# Device variables
toggle_mode_button = Button(13)
toggle_dir_button = Button(26)
buzzer = Buzzer(4)
signal_led = LED(17)
bus = SMBus(1)
leds = [LED(18), LED(23), LED(24), LED(25), LED(5), LED(6), LED(12), LED(16), LED(20), LED(21)]
patterns = [
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0], # Thinnest
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 0]  # Thickest
]
# Default values
pattern = patterns[0]
speed_buzz, width_buzz = False, False
direction = "left"
mode = "cycle"
delay = 0.2

# Modifies the Pattern cycle, not LED Lighting
def update_pattern(): # Thread 1
    global mode
    while True:
        buzzer.on() if speed_buzz or width_buzz else buzzer.off()
        for i in range(10):
            leds[i].value = pattern[i]
        sleep(delay)
        if mode == "cycle":
            cycle(direction)
        else:
            backnforth()

# A simple toggle using meaningful values (opposed to True or False)
def toggleMode():
    global mode
    mode = 'backnforth' if mode == 'cycle' else 'cycle'

# A function to rearrange a pattern by directly modifying it (I know) using a specified direction
def cycle(direction): # VOID
    global pattern
    if direction == "left":
        pattern = pattern[-1:] + pattern[:-1]
    elif direction == "right":
        pattern = pattern[1:] + pattern[:1] 

# A simple toggle using meaningful values (opposed to True or False)
def toggle_cycle_direction():
    global direction
    direction = "right" if direction == "left" else "left"

# A function that utilizes the directional values of the cycle() function when a pattern reaches the end of the component
def backnforth(): # VOID
    global direction
    if pattern[0] == 1:
        direction = "right"
        cycle('left')
    elif pattern[9] == 1:
        direction = "left"
        cycle('right')
    else:
        cycle('right') if direction == "left" else cycle('left')

# A way to read converted analog values from different potentiometers
ads7830_commands = [0x84, 0xc4]
def readADS(input):
    bus.write_byte(0x4b, ads7830_commands[input])
    return bus.read_byte(0x4b)

# A function to that changes a delay based on values gathered from the potentiometer
speed_value = None
def updateDelay():
    global delay
    global speed_value
    global speed_buzz
    while True:
        mod_value = readADS(0) / 30
        # Has the value changed (for the buzzer)
        if mod_value != speed_value:
            speed_value = mod_value
            if speed_value != 0:
                delay = float("0." + str(speed_value))
            else:
                delay = 0.05
            speed_buzz = True
        else:
            speed_buzz = False
        sleep(0.2)

# A function that modifies the pattern selection using values gathered from the potentiometer
width_value = None
def updateWidth():
    global pattern
    global width_value
    global width_buzz
    while True:
        mod_value = readADS(1) / 30
        # Has the value changed (for the buzzer)
        if mod_value != width_value:
            width_value = mod_value
            pattern = patterns[width_value]
            width_buzz = True
        else:
            width_buzz = False
        sleep(0.2)

# Run the program
try:
    # Signal that program is running
    signal_led.on()
    # Button Event listeners
    toggle_mode_button.when_pressed = toggleMode
    toggle_dir_button.when_pressed = toggle_cycle_direction
    # Applicable threading
    threads = [Thread(target=update_pattern), Thread(target=updateDelay), Thread(target=updateWidth)]
    for thread in threads:
        thread.daemon = True # Allows the threads to finish their tasks on sys.exit()
        thread.start()
    # Wait for commands
    pause()
# End the program and display data
except KeyboardInterrupt:
    print("\n\nKilled all worker threads\n{}\n{}s delay set, \nPattern mode = {}\n".format(("-" * 10), delay, mode))
    signal_led.off()
