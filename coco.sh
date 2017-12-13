#!/bin/bash

COCO_PATH=/opt/coco

if [ $USER == 'root' ] || [ $USER == 'rong' ]; then
    echo ""
else
    cd $COCO_PATH
    tools/with_venv.sh coco-bastion --config-file=etc/prod.conf
fi
