#!/usr/bin/env python

import argparse
import os
import getpass

if __name__=="__main__":
    user_name = getpass.getuser()
    default_image_name = user_name + '-spartan-iiwa'
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--image", type=str,
		        help="(required) name of the image that this container is derived from",
                        default=default_image_name)

    parser.add_argument("-c", "--container", type=str,
                        default=default_image_name + '-interactive',
                        help="(optional) name of the container")

    parser.add_argument("-d", "--dry_run", action='store_true',
                        help="(optional) perform a dry_run, print the command that would have been executed but don't execute it.")

    parser.add_argument("-e", "--entrypoint", type=str, default="",
                        help="(optional) thing to run in container")
    parser.add_argument("-u", "--user", type=str, default=user_name,
                        help="Username to run as inside container")

    args = parser.parse_args()
    user_name = args.user

    print "running docker container derived from image %s" %args.image

    image_name = args.image
    home_directory = '/home/' + user_name

    cmd = "xhost +local:root \n"
    cmd += "nvidia-docker run "
    if args.container:
	cmd += " --name %(container_name)s " % {'container_name': args.container}

    cmd += " -e DISPLAY -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix:rw "     # enable graphics
    cmd += " -v ~/.ssh:%(home_directory)s/.ssh " % {'home_directory': home_directory}   # mount ssh keys
    cmd += " -v ~/.ccache:%(home_directory)s/.ccache " % {'home_directory': home_directory}   # mount ccache path

    # login as current user
    cmd += " --user %s " % user_name
    cmd += " --privileged -v /dev/bus/usb:/dev/bus/usb " # allow usb access

    #cmd += " --rm " # remove the image when you exit

    if args.entrypoint and args.entrypoint != "":
	cmd += "--entrypoint=\"%(entrypoint)s\" " % {"entrypoint": args.entrypoint}
    else:
	cmd += "-it "
    cmd += args.image
    cmd_endxhost = "xhost -local:root"

    print "command = \n \n", cmd, "\n", cmd_endxhost
    print ""

    if not args.dry_run:
	print "executing shell command"
	code = os.system(cmd)
	print("Executed with code ", code)
	os.system(cmd_endxhost)
	# Squash return code to 0/1, as
	# Docker's very large return codes
	# were tricking Jenkins' failure
	# detection
	exit(code != 0)
    else:
	print "dry run, not executing command"
	exit(0)
