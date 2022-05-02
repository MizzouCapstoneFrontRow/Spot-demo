import asyncio
from multiprocessing.connection import Client
from re import X
from socket import timeout
import client
import time
from time import sleep

# Be sure to run using the correct version of python, which is 3.6 or something
# import bosdyn.client
# from bosdyn.client.robot_command import RobotCommandClient, blocking_stand


from bosdyn.api import geometry_pb2
import bosdyn.api.power_pb2 as PowerServiceProto
# import bosdyn.api.robot_command_pb2 as robot_command_pb2
import bosdyn.api.robot_state_pb2 as robot_state_proto
import bosdyn.api.basic_command_pb2 as basic_command_pb2
import bosdyn.api.spot.robot_command_pb2 as spot_command_pb2
from bosdyn.client import create_standard_sdk, ResponseError, RpcError
from bosdyn.client.async_tasks import AsyncGRPCTask, AsyncPeriodicQuery, AsyncTasks
from bosdyn.client.estop import EstopClient, EstopEndpoint, EstopKeepAlive
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.lease import Error as LeaseBaseError
from bosdyn.client.power import PowerClient
from bosdyn.client.robot_command import RobotCommandClient, RobotCommandBuilder
from bosdyn.client.image import ImageClient
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.time_sync import TimeSyncError
import bosdyn.client.util
from bosdyn.client.frame_helpers import ODOM_FRAME_NAME
from bosdyn.util import duration_str, format_metric, secs_to_hms

VELOCITY_BASE_SPEED = 0.5  # m/s
VELOCITY_BASE_ANGULAR = 0.8  # rad/sec
VELOCITY_CMD_DURATION = 0.6  # seconds
COMMAND_INPUT_RATE = 0.1

x = 0.0 # forward and backward
y = 0.0 # strafe left and right
z = 0.0 # Pivot left and right/ turning

sit = 0.0 # determines weather to sit or stand.

#SPOT SETUP GOES HERE

sdk = bosdyn.client.create_standard_sdk('Capstone demo')
spot = sdk.create_robot('192.168.80.3')

username = ""
password = ""
# CREATE THIS FILE, WITH ITS CONTENT BEING: "username,password" for your spot
with open("auth", "r") as filestream:
    for line in filestream:
        username, password = line.split(',')
spot.authenticate(username, password)

# # Gets the state of spot
# state_client = spot.ensure_client('spot_state')
# state_client.get_robot_state()

# Software E-Stop
estop_client = spot.ensure_client('estop')
estop_client.get_status()

#Only register an ESTOP when spot motors are powered off
# estop_endpoint = bosdyn.client.estop.EstopEndpoint(client = estop_client, name="main_estop", estop_timeout=9.0)
# estop_endpoint.force_simple_setup()

# estop_keep_alive = bosdyn.client.estop.EstopKeepAlive(estop_endpoint)
# estop_keep_alive.get_status()

# taking ownership of the robot
lease_client = spot.ensure_client('lease')
lease_client.list_leases()

lease = lease_client.acquire()
lease_keep_alive = bosdyn.client.lease.LeaseKeepAlive(lease_client)
lease_client.list_leases()

#power spot on
spot.power_on(timeout_sec=20)
spot.time_sync.wait_for_sync()

# Command setup
command_client = spot.ensure_client(RobotCommandClient.default_service_name)

def _try_grpc(desc, thunk):
    try:
        return thunk()
    except (ResponseError, RpcError, LeaseBaseError) as err:
            print("Failed {}: {}".format(desc, err))
            return None

def start_robot_command(desc, command_proto, end_time_secs=None):
    def start_command():
        command_client.robot_command(lease=None, command=command_proto, end_time_secs=end_time_secs)
    _try_grpc(desc, start_command)

def velocity_cmd_helper(desc="", v_x=0.0, v_y=0.0, v_rot=0.0):
    start_robot_command(desc,
    RobotCommandBuilder.synchro_velocity_command(v_x=v_x, v_y=v_y, v_rot=v_rot), 
    end_time_secs=time.time() + VELOCITY_CMD_DURATION)

def safe_power_off():
    print("Reset Triggered. Powering off robot!")
    start_robot_command("safe_power_off", RobotCommandBuilder.safe_power_off_command())

# AXIS FUNCTION DEFINITIONS ########################################
def x_axis(value):
    global x
    x = value
    if (abs(value) < 0.5):
        x = 0.0
    print("X Axis", value)

def y_axis(value):
    global y
    y = value
    print("Y Axis", value)
    if (abs(value) < 0.5):
        y = 0.0

def pivot_axis(value):
    global z
    z = value
    print("Z Axis", value)
    if (abs(value) < 0.5):
        z = 0.0

def sit_axis(value):
    global sit
    print("Sit Axis", value)
    if (abs(value) > 0.5):
        sit = value
####################################################################
# Update Functions Defs ############################################
def update_sit_stand():
    if (sit > 0): # Sit down
        start_robot_command('sit', RobotCommandBuilder.synchro_sit_command())
    elif(sit < 0):
        start_robot_command('stand', RobotCommandBuilder.synchro_stand_command())
    return

def update_move():
    # global x
    # global y
    if(x > 0):
        velocity_cmd_helper("move_forward", v_x=VELOCITY_BASE_SPEED)
    elif(x < 0):
        velocity_cmd_helper("move_backward", v_x=-VELOCITY_BASE_SPEED)
    if(y > 0):
        velocity_cmd_helper("strafe_right", v_y=-VELOCITY_BASE_SPEED)
    elif(y < 0):
        velocity_cmd_helper("strafe_left", v_y=VELOCITY_BASE_SPEED)
    return 0

def update_rotate():
    if (z < 0):
        velocity_cmd_helper("turn_left", v_rot=VELOCITY_BASE_ANGULAR)
    elif(z > 0):
        velocity_cmd_helper("turn_right", v_rot=-VELOCITY_BASE_ANGULAR)


# # Add Test code here:
# print("Program Ended without error")

# #Should make Robot stand and then power off safely
# print("Standing")
# sit_axis(0.7)
# update_sit_stand()
# # start_robot_command('stand', RobotCommandBuilder.synchro_stand_command())
# time.sleep(2.5)
# print("z is positive")
# x_axis(1)
# update_move()
# time.sleep(0.5)
# update_move()
# time.sleep(0.5)
# update_move()
# time.sleep(2.5)


# velocity_cmd_helper("turn_left", v_rot=VELOCITY_BASE_ANGULAR)
# time.sleep(2.5)
# velocity_cmd_helper("turn_left", v_rot=VELOCITY_BASE_ANGULAR)
# time.sleep(2.5)
# velocity_cmd_helper("turn_right", v_rot=-VELOCITY_BASE_ANGULAR)
# time.sleep(2.5)
# velocity_cmd_helper("turn_right", v_rot=-VELOCITY_BASE_ANGULAR)
# time.sleep(1)
# sit = -1
# update_sit_stand()
# time.sleep(2.5)
# sit = 1
# update_sit_stand()
# time.sleep(5)
# start_robot_command("safe_power_off", RobotCommandBuilder.safe_power_off_command())


# VIDEO Testing code
# from bosdyn.client.image import ImageClient
# image_client = spot.ensure_client(ImageClient.default_service_name)
# sources = image_client.list_image_sources()
# print([source.name for source in sources])

# from PIL import Image
# import io
# # import cv2
# import numpy as np
# image_response = image_client.get_image_from_sources(["frontleft_fisheye_image"])[0]
# # print(image_response)
# image = Image.open(io.BytesIO(image_response.shot.image.data))
# image.show()
# image.save("test.jpg")

# while (True):
#     image = Image.open(io.BytesIO(image_response.shot.image.data))
#     cv_image = np.array(image)
#     cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
#     cv2.imshow('display', cv_image)
#     cv2.waitKey(1)

from PIL import Image
import io
import os

from bosdyn.client.image import ImageClient
image_client = spot.ensure_client(ImageClient.default_service_name)
sources = image_client.list_image_sources()
print([source.name for source in sources])
# image_response = image_client.get_image_from_sources(["left_fisheye_image"])[0]

if __name__ == "__main__":

    # ClientLibrary setup
    client = client.Client()

    print("Setting name")
    client.set_name("spot-demo")

    print("Setting reset callback")
    client.set_reset(lambda: safe_power_off())

    print("adding axis:x")
    client.register_axis("move", -1.0, 1.0, "walk", "z", x_axis)

    print("adding axis:z")
    client.register_axis("strafe", -1.0, 1.0, "walk", "x", y_axis)

    print("adding axis:y")
    client.register_axis("pivot",-1.0, 1.0, "pivot", "x", pivot_axis)

    print("Sit down and stand up")
    client.register_axis("stand", -1.0, 1.0, "stand", "z", sit_axis)

    print("Safe shutdown function")

    # f = io.BytesIO(b"data")
    stream1Read, stream1Write = os.pipe()
    # stream2Read, stream2Write = os.pipe()

    
    client.register_stream("Cam 1","mjpeg", stream1Read)
    # client.register_stream("Cam 2", "mjpeg", stream2Read)

    client.connect_to_server("192.168.80.103", 45575, 45577)

    file1 = os.fdopen(stream1Write, "w")
    # file2 = os.fdopen(stream2Write, "w")

    while (True):

        sleep(0.6)
        print("updating")
        client.library_update()
        # print("image_response")
        # image_response = image_client.get_image_from_sources(["left_fisheye_image"])[0]
        # image = Image.open(io.BytesIO(image_response.shot.image.data))
        # image.save(file1, "jpeg")

        # image_response = image_client.get_image_from_sources(["frontright_depth"])[0]
        # # print("image")
        # image = Image.open(io.BytesIO(image_response.shot.image.data))
        # # print("save")
        # image.save(file2, "jpeg")

        # image.show()
        # print("image done")
        update_sit_stand()
        update_move()
        update_rotate()

    client.shutdown_library()



# image_response = image_client.get_image_from_sources(["left_fisheye_image"])[0]
# from PIL import Image
# import io
# import cv2
# import numpy as np

# image = Image.open(io.BytesIO(image_response.shot.image.data))
# image.show()
# while (True):
#     image = Image.open(io.BytesIO(image_response.shot.image.data))
#     cv_image = np.array(image)
#     cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
#     cv2.imshow('display', cv_image)
#     cv2.waitKey(1)
