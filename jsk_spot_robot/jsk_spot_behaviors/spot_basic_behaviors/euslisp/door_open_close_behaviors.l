(defun open-door ()
  (let (
        )
    ;; first look at the object
    ;;; TODO

    ;; then approach to the object
    ;;; TODO

    ;; relocate the object precisely
    ;;; look at object again
    (send *spotkinova* :angle-vector
          #f(0.0 45.0 -90.0 0.0 45.0 -90.0 0.0 45.0 -90.0 0.0 45.0 -90.0 0 0.0 0.0 90.0 120.0 0))
    (send *ri* :angle-vector (send *spotkinova* :angle-vector) 5000)
    (send *ri* :wait-interpolation)
    ;;; open hand
    (send *ri* :stop-grasp)
    ;;; reach to door_knob
    (setq door_knob_frame (send *tfl* :lookup-transform "base_link" "door_knob_frame" (ros::time 0)))
    (setq ret (send *spotkinova* :head :inverse-kinematics door_knob_frame :rotation-axis nil))
    (if ret
        (progn
          (send *ri* :angle-vector (send *spotkinova* :angle-vector) 5000)
          (send *ri* :wait-interpolation)
          (ros::ros-info "succeed to reach door_knob"))
        (progn
          (ros::ros-error "IK Failed")
          (return-from open-door nil))
        )
    ;;; grasp
    (send *ri* :start-grasp)
    ;;; push down door knob
    (setq door_knob_frame
          (send (send door_knob_frame :copy-worldcoords) :translate #f(-50 20 0)))
    (setq ret (send *spotkinova* :head :inverse-kinematics door_knob_frame))
    (if ret
        (progn
          (send *ri* :angle-vector (send *spotkinova* :angle-vector) 5000)
          (send *ri* :wait-interpolation)
          (ros::ros-info "succeed to push down door knob"))
        (progn
          (ros::ros-error "IK Failed")
          (return-from open-door nil))
        )
    ;;; rotate hand along door knob
    (setq door_knob_frame_rotated
          (send (send door_knob_frame :copy-worldcoords) :rotate -0.5 :y))
    (setq door_knob_frame_opened
          (send (send door_knob_frame :copy-worldcoords) :translate #f(0 0 -200)))
    (setq ret (send *spotkinova* :head :inverse-kinematics door_knob_frame_rotated))
    (if ret
        (progn
          (send *ri* :angle-vector (send *spotkinova* :angle-vector) 5000)
          (send *ri* :wait-interpolation)
          (ros::ros-info "succeed to rotate hand along door knob"))
        (progn
          (ros::ros-error "IK Failed")
          (return-from open-door nil))
        )
    (setq ret (send *spotkinova* :head :inverse-kinematics door_knob_frame_opened :rotation-axis nil))
    (if ret
        (progn
          (send *ri* :angle-vector (send *spotkinova* :angle-vector) 5000)
          (send *ri* :wait-interpolation)
          (ros::ros-info "succeed to pull door knob"))
        (progn
          (ros::ros-error "IK Failed")
          (return-from open-door nil))
        )
  ))
