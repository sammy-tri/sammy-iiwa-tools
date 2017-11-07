#!/usr/bin/env python2

import argparse
import datetime
import os

import drake
import lcm

class IiwaActivityCounter(object):
    def __init__(self):
        # I (sam.creasey) am a lazy, lazy man sometimes, which is why
        # I've chosen the following wildly inefficient storage
        # mechanism.  Create a dictionary of days for each 24-hour
        # period seen in the logfile.  Each day, when it's first seen,
        # gets initialized with 1440 minute buckets.  Each instance of
        # robot activity seen in a given minute increments that
        # minutes activity counter.  Each minute counter which exceeds
        # a specified threshold counts as an "active" minute, which
        # eventually gets us active minutes per robot per day.
        self.days = dict()

        # Decode only one out of every 5 messages (they do come at
        # 200Hz after all).  This seems to cut the processing time
        # roughly in half.  Lower values don't seem to help much,
        # we're probably IO bound after that.
        self.iiwa_message_skip = 5
        self.iiwa_messages = 0

    def get_day(self, date):
        if not date in self.days:
            self.days[date] = [0] * 1440
        return self.days[date]

    def handle_iiwa_status(self, channel, data):
        self.iiwa_messages += 1
        if self.iiwa_messages % self.iiwa_message_skip != 0:
            return

        msg = drake.lcmt_iiwa_status.decode(data)
        velocity_epsilon = 0.1;
        if sum(msg.joint_velocity_estimated) < velocity_epsilon:
            return

        ts_sec = msg.utime * 1e-6;
        timestamp = datetime.datetime.fromtimestamp(ts_sec)
        day = self.get_day(timestamp.date())
        time_of_day = timestamp.time();
        minute = (time_of_day.hour * 60) + time_of_day.minute
        day[minute] += 1

    def load_logfile(self, filename):
        lc = lcm.LCM("file:///" + os.path.abspath(filename) + "?speed=0")
        lc.subscribe("IIWA_STATUS", self.handle_iiwa_status)
        while True:
            try:
                lc.handle()
            except IOError:
                break

    def print_daily_usage(self):
        for date in sorted(self.days.keys()):
            day = self.days[date]
            # Remember the effect of iiwa_message_skip on the count of
            # messages per minute required.
            minutes = sum([int(n > 100) for n in day])
            print date.isoformat() + ": " + str(minutes)


def main():
    parser = argparse.ArgumentParser(description='Count activity in iiwa LCM log')
    parser.add_argument('logfiles', metavar='LOGFILE', type=str, nargs='+',
                        help="A logfile to load")
    args = parser.parse_args()

    counter = IiwaActivityCounter()
    for logfile in args.logfiles:
        print "Loading " + logfile
        counter.load_logfile(logfile)

    counter.print_daily_usage()


if __name__ == "__main__":
    main()
