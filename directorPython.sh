#!/bin/bash

set -e

me=$(python -c 'import os; print(os.path.realpath("'"$0"'"))')
MY_DIR=$(dirname $me)

. $MY_DIR/setup_environment.sh

DRAKE_VIS_DIR=${DRAKE_DIR}/bazel-bin/tools/drake_visualizer.runfiles/drake
cd $DRAKE_VIS_DIR
export LD_LIBRARY_PATH="external/director/lib:external/vtk/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PYTHONPATH="drake/bindings/python:drake/lcmtypes:external/director/lib/python2.7/dist-packages:external/vtk/lib/python2.7/site-packages:external/optitrack_driver/lcmtypes:${PYTHONPATH:+:$PYTHONPATH}"

exec "external/director/bin/directorPython" "$@"
