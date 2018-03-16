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
    local output=`expect <<"    EOF"
    spawn scp * robot@ev3dev:~/
    expect "robot@ev3dev's password:"
    send "maker\n"
    EOF`
    $debug $output
    return $?
}

get_brick_number() {
    local directory=$1
    if [[ "$directory" == "Controller" ]]; then
        echo 30
    elif [[ "$directory" == "Slave" ]]; then
        echo 10
    else
        debug "Got: $directory, expected one of Controller, Slave"
    fi
}

install() {
    local directory=$1
    local number=$(get_brick_number)
    read -p "Please plug in Brick $number (Press enter to continue)"
    cd "./$directory"
    printf "%s" "Installing..."
    until copy; do
        sleep 5
    done
    # TODO: Install required libraries
    ssh robot@ev3dev <<"    EOF"
    chmod +x ~/00runme.sh
    EOF
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
