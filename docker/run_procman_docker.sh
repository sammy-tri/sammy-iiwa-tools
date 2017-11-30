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

cd $DRAKE_DIR

export STARTUP_LOGFILE=$LOGFILE_BASE`date +'%Y-%m-%dT%H-%M-%S'`.version
echo Starting robot $ROBOT_NAME at `date` >> $STARTUP_LOGFILE
echo $SPARTAN_DIR : `git -C $SPARTAN_DIR rev-parse HEAD` >> $STARTUP_LOGFILE
echo "remotes" >> $STARTUP_LOGFILE
git -C $SPARTAN_DIR remote -vv >> $STARTUP_LOGFILE
echo "branches" >> $STARTUP_LOGFILE
git -C $SPARTAN_DIR branch -vv >> $STARTUP_LOGFILE

echo $DRAKE_DIR : `git -C $DRAKE_DIR rev-parse HEAD` >> $STARTUP_LOGFILE
echo "remotes" >> $STARTUP_LOGFILE
git -C $DRAKE_DIR remote -vv >> $STARTUP_LOGFILE
echo "branches" >> $STARTUP_LOGFILE
git -C $DRAKE_DIR branch -vv >> $STARTUP_LOGFILE

echo $IIWA_TOOLS_DIR : `git -C $IIWA_TOOLS_DIR rev-parse HEAD` >> $STARTUP_LOGFILE
echo "remotes" >> $STARTUP_LOGFILE
git -C $IIWA_TOOLS_DIR remote -vv >> $STARTUP_LOGFILE
echo "branches" >> $STARTUP_LOGFILE
git -C $IIWA_TOOLS_DIR branch -vv >> $STARTUP_LOGFILE

$SPARTAN_INSTALL_DIR/bin/bot-procman-sheriff -l $MY_DIR/$PROCMAN_CONFIG
