#!/bin/bash

set -e

sudo hostname $ROBOT_NAME

me=$(python -c 'import os; print(os.path.realpath("'"$0"'"))')
MY_DIR=$(dirname $me)
#echo $MY_DIR
#. $MY_DIR/setup_environment.sh

# The spartan setup script does some ROS stuff which doesn't always work.  Sigh.
. $SPARTAN_DIR/build/setup_environment.sh || true

export DRAKE_DIR=$SPARTAN_DIR/drake
export DRAKE_BIN_DIR=$DRAKE_DIR/bazel-bin
export IIWA_TOOLS_DIR=$(dirname $MY_DIR)
export IIWA_DRIVER_DIR=$HOME/drake-iiwa-driver
export SCHUNK_DRIVER_DIR=$HOME/drake-schunk-driver
export OPTITRACK_DRIVER_DIR=$HOME/optitrack-driver

cd $DRAKE_DIR

export STARTUP_LOGFILE=$LOGFILE_BASE`date +'%Y-%m-%dT%H-%M-%S'`.version
echo Starting robot $ROBOT_NAME at `date` >> $STARTUP_LOGFILE

for PROG_DIR in $SPARTAN_DIR $DRAKE_DIR $IIWA_TOOLS_DIR $IIWA_DRIVER_DIR $SCHUNK_DRIVER_DIR $OPTITRACK_DRIVER_DIR; do
    echo $PROG_DIR : `git -C $PROG_DIR rev-parse HEAD` >> $STARTUP_LOGFILE
    echo "remotes" >> $STARTUP_LOGFILE
    git -C $PROG_DIR remote -vv >> $STARTUP_LOGFILE
    echo "branches" >> $STARTUP_LOGFILE
    git -C $PROG_DIR branch -vv >> $STARTUP_LOGFILE
done

$SPARTAN_INSTALL_DIR/bin/bot-procman-sheriff -l $MY_DIR/$PROCMAN_CONFIG
