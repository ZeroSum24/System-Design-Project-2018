#!/usr/bin/env bash

set -eu

err() {
    echo "$*" 2>&1
}

if [[ -z ${DEBUG+x} ]]; then
    debug=err
else
    debug=:
fi

copy() {
    expect <<"    EOF" >/dev/null 2>&1
    spawn scp * robot@ev3dev:~/
    expect "robot@ev3dev's password:"
    send "maker\n"
    EOF
}

get_brick_number() {
    local directory=$1
    if [[ "$directory" == "Controller" ]]; then
        echo 30
    elif [[ "$directory" == "Slave" ]]; then
        echo 10
    else
        $debug "Got: $directory, expected one of Controller, Slave"
    fi
}

base_installs() {
    expect <<"    EOF" >/dev/null 2>&1
    spawn ssh robot@ev3dev chmod +x ~/00runme.sh
    spawn ssh robot@ev3dev echo "maker" | sudo -S apt-get update
    spawn ssh robot@ev3dev echo "maker" | sudo -S apt-get install -y python3-pip
    spawn ssh robot@ev3dev echo "maker" | sudo -S pip3 install paho-mqtt
    expect "robot@ev3dev's password:"
    send "maker\n"
    EOF
}

extra_install() {
    expect <<"    EOF" >/dev/null 2>&1
    spawn ssh robot@ev3dev echo "maker" | sudo -S apt-get install -y fswebcam
    expect "robot@ev3dev's password:"
    send "maker\n"
    EOF
}

install() {
    local directory=$1
    local number=$(get_brick_number "$directory")
    read -p "Please plug in Brick $number (Press enter to continue)"
    cd "./$directory"
    printf "%s" "Installing..."
    until copy; do
        sleep 5
    done
    base_installs
    if [[ "$directory" == "Slave" ]]; then
        extra_install
    fi
    echo "done"
    cd ../
}

echo ' _  _____ _____        __  __ '
echo '| |/ ____|  __ \ /\   |  \/  |'
echo '| | (___ | |__) /  \  | \  / |'
echo '| |\___ \|  ___/ /\ \ | |\/| |'
echo '|_|____) | |  / ____ \| |  | |'
echo '(_)_____/|_| /_/    \_\_|  |_|'

install Controller
install Slave
