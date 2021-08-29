#!/usr/bin/env roseus

(load "package://spotkinovaeus/spotkinova-interface.l")
(load "package://spot_basic_behaviors/euslisp/door_open_close_behaviors.l")

(ros::load-ros-manifest "std_srvs")


(defun service-handler (req)
  (let ((ret nil)
        (res (send req :response)))
    (setq ret (open-automatic-door))
    (send res :success ret)
    res))


(ros::roseus "open_automatic_door_server")
(spotkinova-init)
(ros::advertise-service "~open_door" std_srvs::Trigger #'service-handler)
(ros::spin)
