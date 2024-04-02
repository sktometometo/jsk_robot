#!/usr/bin/env python

(load "package://spoteus/spot-interface.l")
(load "package://ros_lock/euslisp/ros_lock.l")

(ros::load-ros-package "jsk_spot_startup")


(setq *odom-coords-to-body* nil)
(setq *odom-frame-id* nil


(defun callback-odom (msg)
  (setq *odom-coords-to-body*
    (ros::tf-pose->coords
      (send msg :pose :pose)))
  (setq *odom-frame-id*
    (send msg :header :frame_id))
  )


(defun execute-cb (server goal)
  (if (not (and *odom-coords-to-body* *odom-frame-id*))
    (progn
      (send server :set-aborted
            (send server :result :success nil :message "Odom not initialized"))
      (ros::ros-error "Odom not initialized")
      (return-from execute-cb nil))
      )
  (let* ((target-frame-id (send goal :goal :target_point :header :frame_id))
         (coords-from-odom-to-goal-frame
           (send *tfl* :lookup-transform
                 *odom-frame-id*
                 target-frame-id
                 (ros::time)))
         (target-coords-from-robot
           (transform-coords
             (transform-coords
               (send *odom-coords-to-body* :inverse-transformation)
               coords-from-odom-to-goal-frame)
             (make-coords
               :pos (ros::tf-point->pos (send goal :goal :target_point :point)))))
         msg-result)
    (send *spot* :angle-vector (send *ri* :state :potentio-vector))
    (send *spot* :head :look-at target-coords-from-robot)
    (send *ri* :angle-vector (send *spot* :angle-vector 1000))
    (send *ri* :wait-interpolation)
    (setq msg-result (send server :result))
    (send server :set-succeeded msg-result)
    ))

(defun main ()
  (ros::roseus "spot_look_at_server")

  (spot-init :auto-start nil)

  (ros::subscribe "/spot/odometry" nav_msgs::Odometry #'callback-odom)
  (setq s (instance ros::simple-action-server :init
                      "/spot_look_at"
                      jsk_spot_startup::LookAtAction
                      :execute-cb #'execute-cb))
  (ros::ros-info "Initialized.")
  (ros::rate 500)
  (while (ros::ok)
   (send s :worker)
   (ros::spin-once)
   (ros::sleep)
   )
  )

(main)
