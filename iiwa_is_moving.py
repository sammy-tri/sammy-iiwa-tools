#!/usr/bin/env python2

import argparse
import datetime
import os
import sys

# Yes, I'm just going to hardcode the location where this usually
# lives in the docket image.  Sigh.
docker_spartan_python = "/home/robot-lab/spartan/build/install/lib/python2.7/site-packages/"

if os.path.isdir(docker_spartan_python):
    sys.path.append(docker_spartan_python)

import drake
import lcm


class IiwaMovingChecker(object):
    def __init__(self):
        self.last_running_ts_sec = 0;

    def handle_iiwa_status(self, channel, data):
        msg = drake.lcmt_iiwa_status.decode(data)
        ts_sec = msg.utime * 1e-6;

        timestamp = datetime.datetime.fromtimestamp(ts_sec)
        velocity_epsilon = 0.1;

        if sum(msg.joint_velocity_estimated) < velocity_epsilon:
            if self.last_running_ts_sec != 0 and (ts_sec - self.last_running_ts_sec) > 60:
                # We were moving, but stopped.
                print timestamp.isoformat() + ": iiwa NOT MOVING"
                self.last_running_ts_sec = 0
        else:
            if self.last_running_ts_sec == 0:
                print timestamp.isoformat() + ": iiwa moving"
            self.last_running_ts_sec = ts_sec

    def run(self):
        lc = lcm.LCM()
        lc.subscribe("IIWA_STATUS", self.handle_iiwa_status)
        while True:
            try:
                lc.handle()
            except IOError:
                break


if __name__ == "__main__":
    IiwaMovingChecker().run()
