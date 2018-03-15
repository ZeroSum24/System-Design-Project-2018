#!/usr/bin/env bash

set -eu

if [[ -z ${DEBUG+x} ]]; then
    debug=echo
else
    debug=:
fi

copy() {
    expect <<EOF
    spawn scp * robot@ev3dev:~/
    expect "robot@ev3dev's password:"
    send "maker\n"
EOF
}

install() {
    local number=$1
    local directory=$2
    read -p "Please plug in Brick $number (Press enter to continue)"
    cd "./$directory"
    printf "%s" "Installing..."
    until copy >/dev/null 2>&1; do
        sleep 5
    done
    echo "done"
    cd ../
}

echo ' _  _____ _____        __  __ '
echo '| |/ ____|  __ \ /\   |  \/  |'
echo '| | (___ | |__) /  \  | \  / |'
echo '| |\___ \|  ___/ /\ \ | |\/| |'
echo '|_|____) | |  / ____ \| |  | |'
echo '(_)_____/|_| /_/    \_\_|  |_|'

install 30 Controller
install 10 Slave
