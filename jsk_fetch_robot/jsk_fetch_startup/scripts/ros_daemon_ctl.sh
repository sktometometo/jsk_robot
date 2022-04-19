#!/bin/bash


function usage()
{
    echo "Usage: $0 [-s] [-t] [-h]"
}

MODE="none"

while getopts sth OPT
do
    case $OPT in
        s)
            MODE="start"
            ;;
        t)
            MODE="stop"
            ;;
        h)
            usage
            exit 1
            ;;
    esac
done


echo "MODE: $MODE"
if [ $MODE == "stop" ]; then
    sudo supervisorctl stop jsk-app-scheduler
    sudo supervisorctl stop jsk-dialog
    sudo supervisorctl stop jsk-fetch-startup
    sudo supervisorctl stop jsk-gdrive
    sudo supervisorctl stop jsk-human-pose-estimator
    sudo supervisorctl stop jsk-network-monitor
    sudo supervisorctl stop jsk-object-detector
    sudo supervisorctl stop jsk-panorama-human-pose-estimator
    sudo supervisorctl stop jsk-panorama-object-detector
    sudo supervisorctl stop jsk-rfcomm-bind
    sudo supervisorctl stop jsk-shutdown
    sudo supervisorctl stop robot
    sudo supervisorctl stop roscore
elif [ $MODE == "start" ]; then
    sudo supervisorctl start jsk-app-scheduler
    sudo supervisorctl start jsk-dialog
    sudo supervisorctl start jsk-fetch-startup
    sudo supervisorctl start jsk-gdrive
    sudo supervisorctl start jsk-human-pose-estimator
    sudo supervisorctl start jsk-network-monitor
    sudo supervisorctl start jsk-object-detector
    sudo supervisorctl start jsk-rfcomm-bind
    sudo supervisorctl start jsk-shutdown
    sudo supervisorctl start robot
    sudo supervisorctl start roscore
else
    usage
    exit 1
fi
