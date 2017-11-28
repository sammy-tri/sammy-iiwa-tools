#!/usr/bin/python

import argparse
import datetime
import subprocess

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", type=str, required=True,
                        help="Base filename to append date/time to")
    parser.add_argument("-t", "--rotation-time", type=int, default=600,
                        help="Time intervel between rotating to a new file")
    parser.add_argument("passthrough", type=str, nargs="+",
                        help="Passthrough arguments to ffmpeg")
    args = parser.parse_args()
    print args

    print datetime.datetime.today().isoformat()
    print datetime.datetime.today().replace(microsecond=0).isoformat()

    while True:
        now =  datetime.datetime.today().replace(microsecond=0).isoformat()
        output_file = args.output + now.replace(':', "-") + ".mkv"
        subprocess.check_call(["ffmpeg"] + args.passthrough +
                              ["-t", str(args.rotation_time), output_file])


if __name__ == "__main__":
    main()
