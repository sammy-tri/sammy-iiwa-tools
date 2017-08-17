#!/home/sammy/directorPython.sh

from director import lcmUtils
from director import robotstate
from director import transformUtils

import bot_core

def send_position():

    msg = bot_core.robot_state_t()
    msg.pose = robotstate.getPoseLCMFromXYZRPY([0.80, 0.36, 0.29],
                                               [0., 0., 0.])
    lcmUtils.publish('OBJECT_STATE_EST', msg)

if __name__ == "__main__":
    send_position()
