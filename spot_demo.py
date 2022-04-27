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
estop_endpoint = bosdyn.client.estop.EstopEndpoint(client = estop_client, name="main_estop", estop_timeout=9.0)
estop_endpoint.force_simple_setup()

estop_keep_alive = bosdyn.client.estop.EstopKeepAlive(estop_endpoint)
estop_keep_alive.get_status()

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

# AXIS FUNCTION DEFINITIONS ########################################
def x_axis(value):
    x = value
    if (abs(value) < 0.1):
        x = 0.0

def y_axis(value):
    y = value
    if (abs(value) < 0.1):
        y = 0.0

def pivot_axis(value):
    z = value
    if (abs(value) < 0.1):
        z = 0.0

def sit_axis(value):
    if (abs(value) > 0.5):
        sit = value
####################################################################

# Update Functions Defs ############################################
def update_sit_stand():
    if (sit < 0): # Sit down
        start_robot_command('sit', RobotCommandBuilder.synchro_sit_command())
    elif(sit > 0):
        start_robot_command('stand', RobotCommandBuilder.synchro_stand_command())
    return

def update_move():
    if(x > 0):
        velocity_cmd_helper("move_forward", v_x=VELOCITY_BASE_SPEED)
    elif(x < 0):
        velocity_cmd_helper("move_backward", v_x=-VELOCITY_BASE_SPEED)
    if(y > 0):
        velocity_cmd_helper("strafe_right", v_y=-VELOCITY_BASE_SPEED)
    elif(y < 0):
        velocity_cmd_helper("strafe_left", v_y=VELOCITY_BASE_SPEED)
    return 0

def safe_power_off():
    print("Reset Triggered. Powering off robot!")
    start_robot_command("safe_power_off", RobotCommandBuilder.safe_power_off_command())

def update_rotate():
    if (z < 0):
        velocity_cmd_helper("turn_left", v_rot=VELOCITY_BASE_ANGULAR)
    elif(z>0):
        velocity_cmd_helper("turn_right", v_rot=-VELOCITY_BASE_ANGULAR)


if __name__ == "__main__":

    # ClientLibrary setup
    client = client.Client()

    print("Setting name")
    client.set_name("spot-demo")

    print("Setting reset callback")
    client.set_reset(lambda: safe_power_off())

    print("adding axis:x")
    client.register_axis("move", -1.0, 1.0, "walk", "x", x_axis)

    print("adding axis:z")
    client.register_axis("strafe", -1.0, 1.0, "walk", "z", y_axis)

    print("adding axis:y")
    client.register_axis("pivot",-1.0, 1.0, "pivot", "y", pivot_axis)

    print("Sit down and stand up")
    client.register_axis("stand", -1.0, 1.0, "stand", "y", sit_axis)

    client.connect_to_server("192.168.1.7", 45575)

    while (True):
        sleep(1)
        print("updating")
        client.library_update()
        update_sit_stand()
        update_move()
        update_rotate()
    client.shutdown_library()