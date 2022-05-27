# jsk_magni_startup

## SetUp (Running following commands in the first time within the robot)

### Install Official Raspberry Pi image

TODO

### fix ROS_HOSTNAME within the robot

Edit /etc/ubiquity/env.sh
```
  #!/bin/sh
- #export ROS_HOSTNAME=$(hostname).local
+ export ROS_HOSTNAME=$(hostname)
  export ROS_MASTER_URI=http://$ROS_HOSTNAME:11311
```

### Update workspace

use [jsk_magni.rosinstall](./jsk_magni.rosinstall)

### Build driver for USB WiFi

[tp-link Archer T2U Nano](https://www.tp-link.com/jp/home-networking/adapter/archer-t2u-nano/) is added for `sanshiro` connection.

```bash
sudo apt install raspberrypi-kernel-headers
git clone https://github.com/aircrack-ng/rtl8812au.git
cd rtl8812au
make
sudo make install
```

### Setup pigpid.services

see https://github.com/UbiquityRobotics/pi_sonar,

```bash
wget https://raw.githubusercontent.com/joan2937/pigpio/master/util/pigpiod.service
sudo cp pigpiod.service /etc/systemd/system
sudo systemctl enable pigpiod.service
sudo systemctl start pigpiod.service
```

### add jsk_magni.service

Copy [`jsk-magni-startup`](./system/scripts/jsk-magni-startup) to `/usr/sbin/jsk-magni-startup`.
```bash
$ roscd jsk_magni_startup/
$ cat system/scripts/jsk-magni-startup
#!/bin/bash

# Please put this script to /usr/sbin/jsk-magni-startup

function log() {
  logger -s -p user.$1 ${@:2}
  }

log info "magni-base: Using workspace setup file /home/ubuntu/catkin_ws/devel/setup.bash"
source /home/ubuntu/catkin_ws/devel/setup.bash

log_path="/tmp"

source /etc/ubiquity/env.sh
log info "magni-base: Launching ROS_HOSTNAME=$ROS_HOSTNAME, ROS_IP=$ROS_IP, ROS_MASTER_URI=$ROS_MASTER_URI, ROS_LOG_DIR=$log_path"

# Punch it.
export ROS_HOME=/home/ubuntu/.ros
export ROS_LOG_DIR=$log_path
roslaunch jsk_magni_startup magni_bringup.launch &
PID=$!

log info "jsk-magni-startup: Started roslaunch as background process, PID $PID, ROS_LOG_DIR=$ROS_LOG_DIR"
echo "$PID" > $log_path/jsk-magni-startup.pid
wait "$PID"
$ sudo cp system/scripts/jsk-magni-startup /usr/sbin/
```

Copy [`jsk-magni-startup.service`](./system/systemd/jsk-magni-startup.service) to `/etc/systemd/system/jsk-magni-startup.service`.
```bash
$ roscd jsk_magni_startup/
$ cat system/systemd/jsk-magni-startup.service
[Unit]
Requires=roscore.service
PartOf=roscore.service
After=magni-base.service
[Service]
Type=simple
User=ubuntu
ExecStart=/usr/sbin/jsk-magni-startup
[Install]
WantedBy=multi-user.target
$ sudo cp system/systemd/jsk-magni-startup.service /etc/systemd/system/
```

Enable service
```bash
$ sudo systemctl enable jsk-magni-startup.service
$ sudo systemctl start jsk-magni-startup.service
```

