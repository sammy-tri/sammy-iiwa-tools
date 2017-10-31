#!/bin/bash

set -e

me=$(python -c 'import os; print(os.path.realpath("'"$0"'"))')
MY_DIR=$(dirname $me)
#echo $MY_DIR
#. $MY_DIR/setup_environment.sh

# The spartan setup script does some ROS stuff which doesn't always work.  Sigh.
. $SPARTAN_DIR/build/setup_environment.sh || true

export DRAKE_DIR=$SPARTAN_DIR/drake
export DRAKE_BIN_DIR=$DRAKE_DIR/bazel-bin

cd $DRAKE_DIR

$SPARTAN_INSTALL_DIR/bin/bot-procman-sheriff -l $MY_DIR/$PROCMAN_CONFIG
