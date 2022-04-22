from re import X
import client
from time import sleep

# Be sure to run using the correct version of python, which is 3.6 or something
import bosdyn.client



VELOCITY_BASE_SPEED = 0.5  # m/s
VELOCITY_BASE_ANGULAR = 0.8  # rad/sec
VELOCITY_CMD_DURATION = 0.6  # seconds
COMMAND_INPUT_RATE = 0.1

x = 0.0 # forward and backward
y = 0.0 # strafe left and right
z = 0.0 # Pivot left and right/ turning

sit = 0.0 # determines weather to sit or stand.

def x_axis(value):
    x = value
    if (abs(value) < 0.1):
        x = 0.0

def y_axis(value):
    y = value
    if (abs(value) < 0.1):
        y = 0.0
def z_axis(value):
    z = value
    if (abs(value) < 0.1):
        z = 0.0


def sit_axis(value):
    if (abs(value) > 0.5):
        sit = value

def update_sit_stand():

    return

if __name__ == "__main__":
    
    # Spot setup
    sdk = bosdyn.client.create_standard_sdk('Capstone demo')
    spot = sdk.create_robot('192.168.80.3')
    
    username = ""
    password = ""

    with open("auth", "r") as filestream:
        for line in filestream:
            username, password = line.split(',')
    spot.authenticate(username, password)

    # Gets the state of spot
    # state_client = spot.ensure_client('spot_state')
    # state_client.get_robot_state()



    # ClientLibrary setup
    client = client.Client()

    print("Setting name")
    client.set_name("spot-demo")

    print("Setting reset callback")
    client.set_reset(lambda:print("Resetting!", flush=True))

    print("adding axis")
    client.register_axis("move", -1.0, 1.0, "walk", "x", x_axis)

    print("adding axis")
    client.register_axis("strafe", -1.0, 1.0, "walk", "z", y_axis)

    client.register_axis("pivot",-1.0, 1.0, "pivot", "y", z_axis)


    print("Sit down and stand up")
    client.register_axis("stand", -1.0, 1.0, "stand", "y", sit_axis)

    client.connect_to_server("192.168.1.7", 45575)

    while (True):
        sleep(1)
        print("updating")
        client.library_update()
        update_sit_stand()
