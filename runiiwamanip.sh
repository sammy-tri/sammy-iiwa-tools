#!/bin/bash

cd $SPARTAN_SOURCE_DIR/src/iiwa_tri
drake-visualizer --script iiwaManipApp.py --bot-config iiwaManip.cfg --director-config $DRAKE_DIR/examples/kuka_iiwa_arm/director_config.json $*
