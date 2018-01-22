#!/usr/bin/env python

import argparse
import getpass
import os
import subprocess
import sys
import tarfile
import tempfile

# These specify a version of spartan living in
# https://github.com/sammy-tri/spartan/tree/no_ros_prereqs which
# splits the prereq install not to include ROS deps.
_DEFAULT_SPARTAN_REPO = "https://github.com/sammy-tri/spartan.git"
_DEFAULT_SPARTAN_REV = "fda56e4fc4beddb0cad6fb477fe07b2e15decaec"

# Build a tarfile containing the docker context
def make_context_tar(spartan_path):
    (fd, path) = tempfile.mkstemp()
    print "Creating docker context in %s" % (path)

    fileobj = os.fdopen(fd, "w")
    tar = tarfile.open(mode='w', fileobj=fileobj)

    def exclude_fn(filename):
        if "build" in filename.split('/'):
            print "Excluding build directory:", filename
            return True
        return False


    tar.add(spartan_path, arcname="/spartan", exclude=exclude_fn)
    my_path = os.path.dirname(os.path.abspath(__file__))
    print "my path", my_path, os.path.dirname(my_path)
    tar.add(os.path.dirname(my_path), arcname="/iiwa-tools")
    tar.add(os.path.join(my_path, "dockerfile"), arcname="/Dockerfile")
    tar.close()
    fileobj.flush()
    fileobj.close()

    return path


def main():
    print "Building base docker container"

    user_name = getpass.getuser()
    default_image_name = user_name + "-spartan-iiwa"

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--image", type=str,
		        help="name for the newly created docker image",
                        default=default_image_name)

    parser.add_argument("-d", "--dry_run", action='store_true',
                        help="(optional) perform a dry_run, print the command that would have been executed but don't execute it.")

    parser.add_argument("-p", "--password", type=str,
                    help="(optional) password for the user", default="password")

    parser.add_argument('-U','--user_id', type=int,
                        help="(optional) user id for this user",
                        default=os.getuid())
    parser.add_argument('-G','--group_id', type=int,
                        help="(optional) user gid for this user",
                        default=os.getgid())
    parser.add_argument('-s', '--spartan',
                        help="Path to the spartan source to include in the image")
    parser.add_argument("-u", "--user", type=str, default=user_name,
                        help="Username to run as inside container")

    args = parser.parse_args()
    user_name = args.user

    if not args.spartan:
        print "Use --spartan to specify the spartan source directory to include"
        sys.exit(1)

    if not os.path.isdir(args.spartan):
        print "Spartan source must be a directory."
        sys.exit(1)

    tarfile_name = make_context_tar(args.spartan)

    print "building docker image named ", args.image
    cmd = ["docker", "build",
           "--build-arg", "USER_NAME=" + user_name,
           "--build-arg", "USER_PASSWORD=" + args.password,
           "--build-arg", "USER_ID=" + str(args.user_id),
           "--build-arg", "USER_GID=" + str(args.group_id),
           "-t", args.image,
           "-"]

    print "command = \n" + " ".join(cmd)

    if args.dry_run:
        print "Dry run specified, exiting"
        sys.exit(0)

    subprocess.check_call(cmd, stdin=open(tarfile_name, "r"))
    os.unlink(tarfile_name)

if __name__=="__main__":
    main()
