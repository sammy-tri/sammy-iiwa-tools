#!/usr/bin/env python

import argparse
import getpass
import os
import subprocess
import sys
import tarfile
import tempfile

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

    parser.add_argument('-u','--user_id', type=int,
                        help="(optional) user id for this user",
                        default=os.getuid())
    parser.add_argument('-g','--group_id', type=int,
                        help="(optional) user gid for this user",
                        default=os.getgid())
    parser.add_argument('-s', '--spartan',
                        help="Path to the spartan source to include in the image")

    args = parser.parse_args()
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
