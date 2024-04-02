#!/usr/bin/env python

(load "package://spoteus/spot-interface.l")
(load "package://ros_lock/euslisp/ros_lock.l")

(ros::load-ros-package "jsk_spot_startup")


(defun init-look-at-client ()
  (if (not (boundp *ac-look-at*))
      (setq *ac-look-at*
            (instance ros::simple-action-client :init
                      "/spot_look_at"
                      jsk_spot_startup::LookAtAction))
      )
  (send *ac-look-at* :wakt-for-server)
  )


(defun spot-look-at (target-coords &key (frame-id "body") (wait t))
  (let (
        (msg-goal (instance jsk_spot_startup::LookAtGoal))
        )
    (init-look-at-client)
    (send msg-goal :header :frame_id frame-id)
    (send msg-goal :point (ros::pos->tf-point (send target-coords :pos)))
    (send *ac-look-at* :send-goal msg-goal)
    (if wait
      (progn
        (send *ac-look-at* :wait-for-result)
        ))
    ))
