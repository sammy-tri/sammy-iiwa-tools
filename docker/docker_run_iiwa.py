#!/usr/bin/env python

import argparse
import datetime
import getpass
import json
import os
import string
import shutil
import subprocess
import sys
import tempfile

_THIS_FILE = os.path.abspath(__file__)
_THIS_DIR = os.path.dirname(_THIS_FILE)

mandatory_fields = [
    "robot_name",
    "gripper_address",
    "gripper_local_port",
    "gripper_remote_port",
    "iiwa_port",
    "iiwa_local_interface",
    "iiwa_local_ip",
    "iiwa_koni_ip",
    "log_directory",
    "procman_config",
    "iiwa_optitrack_id",
    "target_optitrack_id",
]

optional_fields = [
    "container",
    "image",
    "camera_device",
    "anzu_resource_root",
    "grip_force",
    "grasp_frame_translational_offset",
]

def load_robot_config(config_file):
    with open(config_file, 'r') as f:
        robot_config = json.load(f)

    # Verify that certain mandatory options are present:
    missing_configs = []

    for config_str in mandatory_fields:
        if not config_str in robot_config:
            missing_configs.append(config_str)

    if len(missing_configs):
        print "The following entries are missing from the robot configuration file:"
        print ", ".join(missing_configs)
        sys.exit(1)

    unknown_configs = []
    for k in robot_config.keys():
        if not k in mandatory_fields + optional_fields:
            unknown_configs.append(k)

    if len(unknown_configs):
        print "The robot configuration file contained the following unknown fields:"
        print ", ".join(unknown_configs)

    return robot_config


def make_pick_and_place_config(target_dir, robot_config):
    config_template = string.Template("""

robot {
  model_name: "iiwa"
  optitrack_info {
    id: $iiwa_optitrack_id
  }
  pose {
    xyz: [0.0, 0.0, 0.7645]
  }
}

object {
  model_name: "big_robot_toy"
  optitrack_info {
    id: $target_optitrack_id
  }
  pose {
    xyz: [0.8, -2.14, 0.75]
  }
}
task {
  end_effector_name: "iiwa_link_ee"
  robot_index: 0
  target_index: 0
  $extra_task_config
}
""")

    extra_task_config = ""
    if "grip_force" in robot_config:
        extra_task_config += "grip_force: " + robot_config["grip_force"] + "\n"
    if "grasp_frame_translational_offset" in robot_config:
        extra_task_config += "grasp_frame_translational_offset: " + \
                             robot_config["grasp_frame_translational_offset"] + "\n"

    base_config = open(os.path.join(
        _THIS_DIR, "pick_and_place_configuration_base")).read()

    config = base_config + config_template.substitute(
        iiwa_optitrack_id=robot_config['iiwa_optitrack_id'],
        target_optitrack_id=robot_config['target_optitrack_id'],
        extra_task_config=extra_task_config)

    with open(os.path.join(
            target_dir, "pick_and_place_configuration"), "w") as f:
        f.write(config)


# Do terrible things to the system's network configuration.  We do try
# to restore the state on our way out, which I suppose is something.
class NetworkConfigMangler(object):
    def __init__(self, robot_config, container_name, dry_run):
        self.robot_config = robot_config
        self.container_name = container_name
        self.dry_run = dry_run
        self.if_was_up = False
        self.network_name = None

    def configure_iiwa_network(self):
        robot_config = self.robot_config

        # First check that the ip doesn't already exist.
        try:
            ip_addr_out = subprocess.check_output(
                ["nmcli", "device", "show", robot_config["iiwa_local_interface"]])
        except subprocess.CalledProcessError as e:
            print "Checking existing configuration failed: " + e.output
            raise e

        addresses_found = []
        for line in ip_addr_out.split('\n'):
            if line.startswith("IP4.ADDRESS"):
                addresses_found.append(line.split(':')[1].strip())

        if len(addresses_found) == 0:
            self.if_was_up = False
        else:
            for addr in addresses_found:
                if addr.split("/")[0] != robot_config["iiwa_local_ip"]:
                    raise RuntimeError("iiwa_local_interface " +
                                       robot_config["iiwa_local_interface"] +
                                       "has an unexpected address configured, " +
                                       "aborting")
            self.if_was_up = True

        if self.if_was_up:
            subprocess.check_call(["nmcli", "device", "disconnect",
                                   robot_config["iiwa_local_interface"]])

        network_name = "iiwa_" + robot_config["iiwa_local_interface"]
        if self.dry_run:
            print "Skipping docker network creation for " + network_name
            return


        docker_nets = subprocess.check_output(["docker", "network", "ls"])
        if network_name in docker_nets:
            subprocess.check_call(["docker", "network", "rm", network_name])

        iiwa_subnet = ".".join(robot_config["iiwa_local_ip"].split(".")[0:3] + ["0/24"])
        subprocess.check_call(["docker", "network", "create",
                               "-d", "macvlan",
                               "--subnet", iiwa_subnet,
                               "-o", "parent=" + robot_config["iiwa_local_interface"],
                               network_name])
        subprocess.check_call(["docker", "network", "connect",
                               "--ip", robot_config["iiwa_local_ip"],
                               network_name, self.container_name])
        self.network_name = network_name


    def restore_configuration(self):
        subprocess.check_call(["docker", "network", "rm", self.network_name])
        if self.if_was_up:
            subprocess.check_call(["nmcli", "device", "connect",
                                   self.robot_config["iiwa_local_interface"]])


def main():
    user_name = getpass.getuser()
    default_image_name = user_name + '-spartan-iiwa'
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--image", type=str,
		        help="(optional) name of the image that this container is " +
                        "derived from (overrides config file)")
    parser.add_argument("-c", "--container", type=str,
                        help="(optional) name of the container (overrides config file)")
    parser.add_argument("-d", "--dry_run", action='store_true',
                        help="(optional) perform a dry_run, print the command that would have been executed but don't execute it.")
    parser.add_argument("-e", "--entrypoint", type=str, default="",
                        help="(optional) thing to run in container")
    parser.add_argument("-C", "--config", type=str, required=True,
                        help="Robot configuration file")
    parser.add_argument("-u", "--user", type=str, default=user_name,
                        help="Username to run as inside container")

    args = parser.parse_args()
    user_name = args.user

    robot_config = load_robot_config(args.config)
    image_name = default_image_name
    if "image" in robot_config:
        image_name = robot_config["image"]
    if args.image and len(args.image):
        image_name = args.image

    container_name = image_name + "_" + robot_config["robot_name"]
    if "container" in robot_config:
        container_name = robot_config["container"]
    if args.container and len(args.container):
        container_name = args.container
    if container_name is None:
        print "The name of the container must be specifed (config file or command line)"
        sys.exit(1)

    print "running docker container derived from image %s in container %s" % (
        image_name, container_name)

    home_directory = '/home/' + user_name

    cmd = "xhost +local:root \n"
    cmd += "nvidia-docker create --name " + container_name
    cmd += " -e DISPLAY -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix:rw "     # enable graphics

    # TODO(sam.creasey) Using os.system here is begging for problems
    # with escaping these config values.
    for key in mandatory_fields + optional_fields:
        if key in robot_config:
            cmd += " -e " + key.upper() + "=\"" + robot_config[key] + "\""

    cmd += " -e SPARTAN_DIR=" + home_directory + "/spartan"
    cmd += " -e LOGFILE_BASE=" + home_directory + "/logs/" + robot_config["robot_name"]
    cmd += " -e LCM_LOGFILE_BASE=" + home_directory + "/logs/" + robot_config["robot_name"] + datetime.date.today().isoformat()
    cmd += " -v " + robot_config["log_directory"] + ":" + home_directory + "/logs"
    # login as current user
    cmd += " --user %s " % user_name

    cmd += " -p " + robot_config["gripper_remote_port"] + ":" + robot_config["gripper_remote_port"] + "/udp"
    cmd += " -p " + robot_config["gripper_local_port"] + ":" + robot_config["gripper_local_port"] + "/udp"

    robot_config_dir = tempfile.mkdtemp(
        prefix=robot_config["robot_name"] + "_config_")
    # The docker user might not be the same uid as the user invoking
    # this script.
    os.chmod(robot_config_dir, 0755)
    make_pick_and_place_config(robot_config_dir, robot_config)
    cmd += " -v " + robot_config_dir + ":" + home_directory + "/configuration"

    cmd += " --privileged -v /dev/bus/usb:/dev/bus/usb " # allow usb access

    if "camera_device" in robot_config:
        cmd += " --group-add video "

    cmd += " --ulimit rtprio=30 " # Allow realtime scheduling

    entrypoint = home_directory + "/iiwa-tools/docker/run_procman_docker.sh"
    if args.entrypoint and args.entrypoint != "":
        entrypoint = args.entrypoint
    cmd += "--entrypoint=" + entrypoint
    cmd += " " + image_name
    #cmd += " " + entrypoint
    cmd_endxhost = "xhost -local:root"


    print "command = \n \n", cmd, "\n", cmd_endxhost
    print ""

    net_config = NetworkConfigMangler(robot_config, container_name, args.dry_run)

    if not args.dry_run:
	print "executing shell command"
	code = os.system(cmd)
	print("Creating container exited with code ", code)
        if code != 0:
            raise RuntimeError("Failed to create container")
        net_config.configure_iiwa_network()
        docker_proc = subprocess.Popen(["nvidia-docker", "start", "-a", container_name])
        print "returncode", docker_proc.returncode
        try:
            #code = subprocess.call(["nvidia-docker", "start", "-a", container_name])
            docker_proc.wait()
        finally:
            if docker_proc.returncode is None:
                print "Terminating docker instance..."
                subprocess.check_call(["docker", "stop", "-t", "1", container_name])
                docker_proc.wait()

            subprocess.check_call(["docker", "rm", container_name])
            net_config.restore_configuration()
            os.system(cmd_endxhost)
            shutil.rmtree(robot_config_dir)
	# Squash return code to 0/1, as
	# Docker's very large return codes
	# were tricking Jenkins' failure
	# detection
	exit(code != 0)
    else:
	print "dry run, not executing command"
        print "robot config in " + robot_config_dir
        net_config.configure_iiwa_network()
	exit(0)

if __name__=="__main__":
    main()
