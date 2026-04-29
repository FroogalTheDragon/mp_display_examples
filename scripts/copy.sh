#!/bin/bash

pushd "$(pwd)" > /dev/null 2>&1 && popd > /dev/null 2>&1 || exit;
ROOT=$(pwd)
MP_REMOTE_PATH="$ROOT/lvgl_micropython/lib/micropython/tools/mpremote";

function help() {
    echo "Help!"; 
}

if [[ "$1" == *"help"* ]] || [ "$1" == "-h" ]; then
    echo "Help!"
fi

if [ ! -d "$MP_REMOTE_PATH" ]; then
    echo "Failed to find mpremote: $MP_REMOTE_PATH"
    exit 1;
fi

# pushd "$MP_REMOTE_PATH" || exit 1

echo "$@"

python3 "$MP_REMOTE_PATH/mpremote.py" fs cp "$1" :/"$1"



