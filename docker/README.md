# Creating docker images for running the iiwa software

This directory contains a collection of utilities to create, maintain,
and run docker images for controlling the iiwa robot arm.

## Building the base image

Creating an image from scratch is done by running
`docker_build_base.py`.  You'll need to specify a spartan source
directory to import into the image.

These specify a version of spartan living in
https://github.com/sammy-tri/spartan/tree/no_ros_prereqs which
splits the prereq install not to include ROS deps.

`git clone https://github.com/sammy-tri/spartan.git`
`git checkout fda56e4fc4beddb0cad6fb477fe07b2e15decaec`

Example: `docker_build_base.py -s ~/spartan -i my-image-name -u robot-lab`

The resulting image will exclude any directories named `build`.

Once the process completes, you should have a docker image containing
all of the prerequisites to build drake+spartan along with the source
directory passed to the `-s` argument (as well as these tools).

The home directory of the user in the newly created container looks
like:

    sammy@a130da10d316:~$ ls -l
    total 8
    drwxr-xr-x 1 sammy sammy 4096 Oct 17 21:38 iiwa-tools
    drwxr-xr-x 1 sammy sammy 4096 Oct 17 21:27 spartan


TODO(sam.creasey) should there be some nominal process for tagging images?

## Compiling the source (and maintaining the image)

The base image contains the source code, but does not compile anything
(this is mostly because the build may check out private repositories
and thus require ssh keys).  To run a container with an interative
shell, run `docker_run_interactive.py`.

Example: `docker_run_interactive.py -i my-image-name -u robot-lab`

The container will not be removed after it is stopped.

`~/.ssh` and `~/.ccache` will be mounted from the user's home
directory on the host into the container.  (`.ssh` to provide
credentials for checking out private repositories from github, and
`.ccache` to speed up the spartan portion of the build).  No link to
the bazel cache is provided, due to the fact that the bazel artifacts
are run directly from the cached directory and those artifacts should
be within the container.

Next, build spartan.  If you're updating an existing image, this is a
convenient time to update the drake/spartan source.

    rm -rf build && mkdir build && cd build && cmake .. -DCMAKE_C_COMPILER_LAUNCHER=/usr/bin/ccache -DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache -DWITH_IIWA_DRIVER_TRI=OFF -DWITH_PERCEPTION=ON -DWITH_SCHUNK_DRIVER=OFF -DWITH_SNOPT=ON -DWITH_ROS=OFF -DWITH_IIWA_DRIVER_RLG=OFF
    make -j

Next, checkout (into the docker user's home directory) and build
https://github.com/RobotLocomotion/drake-iiwa-driver,
https://github.com/RobotLocomotion/drake-schunk-driver, and
https://github.com/RobotLocomotion/optitrack-driver
using `bazel`
according to their instructions.

Once the build is complete, exit the shell (terminating the
container), and create a new image/tag from the container.

Example: `docker container commit sammy-spartan-iiwa-interactive my-image-name:compiled`

## Running a robot from an image

The script `docker_run_iiwa.py` will start up a temporary container
configured for a particular robot.  `sample_config.json` has a minimal
configuration.

Example: `docker_run_iiwa.py -C sample_config.json -i my-image-name:compiled -u robot-lab`
