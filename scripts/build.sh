#!/bin/bash

WORKING_DIR=$(pwd)
pushd -n "$WORKING_DIR" > /dev/null 2>&1 || exit
popd > /dev/null 2>&1 || exit && pushd "lvgl_micropython" > /dev/null 2>&1 || exit

python make.py
BOARD="ESP32_GENERIC_S3"





