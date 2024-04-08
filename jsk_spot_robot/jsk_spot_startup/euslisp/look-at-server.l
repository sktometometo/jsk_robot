#!/usr/bin/env roseus

(load "package://spoteus/spot-interface.l")
(load "package://ros_lock/euslisp/ros_lock.l")

(ros::load-ros-package "jsk_spot_startup")


(setq *odom-coords-to-body* nil)
(setq *odom-frame-id* nil)


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
  (ros::ros-info (format nil "goal: ~A" goal))
  (let* (ret
         (target-frame-id (send goal :goal :target_point :header :frame_id))
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
    (send *spot* :reset-pose)
    (send *spot* :arm :inverse-kinematics
          (send (send (send *spot* :arm :end-coords) :copy-worldcoords) :translate #f(0 0 200)))
    (if (send *spot* :head :look-at (send target-coords-from-robot :pos))
      (setq ret t)
      (setq ret nil))
    (if ret
      (progn
        (send *ri* :angle-vector (send *spot* :angle-vector) 1000)
        (send *ri* :wait-interpolation)
        (setq msg-result (send server :result))
        (send msg-result :result :success t)
        (send server :set-succeeded msg-result)
        )
      (progn
        (ros::ros-error "IK Failed....")
        (setq msg-result (send server :result))
        (send msg-result :result :success nil)
        (send server :set-succeeded msg-result)
        ))
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
