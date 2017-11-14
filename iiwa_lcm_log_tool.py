#!/usr/bin/env python2

import argparse
import cPickle
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

        # All the files this instance has processed before, with the
        # size the file was at that time.  Allows us to skip
        # previously processed data.  Keyed on filename, value is file size.
        self.files_processed = {}

    def get_day(self, date):
        if not date in self.days:
            self.days[date] = [0] * 1440
        return self.days[date]

    def handle_iiwa_status(self, channel, data, timestamp):
        self.iiwa_messages += 1
        if self.iiwa_messages % self.iiwa_message_skip != 0:
            return

        msg = drake.lcmt_iiwa_status.decode(data)
        velocity_epsilon = 0.1;
        if sum(msg.joint_velocity_estimated) < velocity_epsilon:
            return

        ts_sec = timestamp * 1e-6;
        timestamp = datetime.datetime.fromtimestamp(ts_sec)
        day = self.get_day(timestamp.date())
        time_of_day = timestamp.time();
        minute = (time_of_day.hour * 60) + time_of_day.minute
        day[minute] += 1

    def load_logfile(self, filename):
        basename = os.path.basename(filename)
        logfile = lcm.EventLog(os.path.abspath(filename))
        if basename in self.files_processed:
            previous_size = self.files_processed[basename]
            assert previous_size <= logfile.size()
            if previous_size == logfile.size():
                return

            # We partially processed this once before, so seek ahead.
            logfile.seek(previous_size)

        self.iiwa_messages = 0
        for event in logfile:
            if event.channel == "IIWA_STATUS":
                self.handle_iiwa_status(event.channel, event.data,
                                        event.timestamp)

        self.files_processed[basename] = logfile.tell()
        logfile.close()

    def print_daily_usage(self):
        for date in sorted(self.days.keys()):
            day = self.days[date]
            # Remember the effect of iiwa_message_skip on the count of
            # messages per minute required.
            minutes = sum([int(n > 100) for n in day])
            # Figure out how many times we went from moving to stopped
            # (this will include manual stops too).
            falling_edges = 0
            for i in xrange(1, len(day)):
                if day[i - 1] > 100 and day[i] <= 100:
                    falling_edges += 1
            print date.isoformat() + ": " + str(minutes) + " (%d stops)" % (falling_edges)

    def load_state(self, state_file):
        with open(state_file, 'r') as f:
            state = cPickle.load(f)
        self.days = state["days"]
        self.files_processed = state["files_processed"]
        assert self.iiwa_message_skip == state["iiwa_message_skip"]

    def save_state(self, state_file):
        state = dict()
        state["days"] = self.days
        state["files_processed"] = self.files_processed
        state["iiwa_message_skip"] = self.iiwa_message_skip
        with open(state_file, 'w') as f:
            cPickle.dump(state, f)


def main():
    parser = argparse.ArgumentParser(description='Count activity in iiwa LCM log')
    parser.add_argument('logfiles', metavar='LOGFILE', type=str, nargs='+',
                        help="A logfile to load")
    parser.add_argument("--state", metavar='FILE', type=str,
                        help="State file from prior invocation of this tool")
    parser.add_argument("--new-state", metavar='FILE', type=str,
                        help="State file to create after this run")
    args = parser.parse_args()

    counter = IiwaActivityCounter()
    if args.state:
        counter.load_state(args.state)

    for logfile in args.logfiles:
        print "Loading " + logfile
        counter.load_logfile(logfile)

    counter.print_daily_usage()

    if args.new_state:
        counter.save_state(args.new_state)


if __name__ == "__main__":
    main()
