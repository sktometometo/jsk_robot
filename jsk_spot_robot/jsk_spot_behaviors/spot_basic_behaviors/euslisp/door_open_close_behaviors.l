(defun open-swing-door ()
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
          (return-from open-swing-door nil))
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
          (return-from open-swing-door nil))
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
          (return-from open-swing-door nil))
        )
    (setq ret (send *spotkinova* :head :inverse-kinematics door_knob_frame_opened :rotation-axis nil))
    (if ret
        (progn
          (send *ri* :angle-vector (send *spotkinova* :angle-vector) 5000)
          (send *ri* :wait-interpolation)
          (ros::ros-info "succeed to pull door knob"))
        (progn
          (ros::ros-error "IK Failed")
          (return-from open-swing-door nil))
        )
  ))

(defun open-automatic-door ()
  (let ()
    ;; first look at the object
    ;;; TODO

    ;; then approach to the object
    ;;; TODO

    ;; relocate the object precisely
    ;;; look at object again
    (send *spotkinova* :angle-vector
          #f(0.0 45.0 -90.0 0.0 45.0 -90.0 0.0 45.0 -90.0 0.0 45.0 -90.0 0 0.0 0.0 90.0 100.0 0))
    ;;; TODO: this should use look at
    (send *ri* :angle-vector (send *spotkinova* :angle-vector) 5000)
    (send *ri* :wait-interpolation)
    ;; get frames
    (setq door-button-approach-frame (send *tfl* :lookup-transform "base_link" "door_button_approach_frame" (ros::time 0)))
    (setq door-button-touch-frame (send *tfl* :lookup-transform "base_link" "door_button_touch_frame" (ros::time 0)))
    (if (or (not door-button-approach-frame) (not door-button-touch-frame))
      (progn
        (ros::ros-error "Transform Failed")
        (send *spotkinova* :kinova-rest-pose)
        (send *ri* :angle-vector (send *spotkinova* :angle-vector) 3000)
        (send *ri* :wait-interpolation)
        (return-from open-automatic-door nil))
       )
      nil)
    ;; close hand
    (send *ri* :wait-interpolation)
    ;; move hand to approach position
    (setq ret (send *spotkinova* :head :inverse-kinematics door-button-approach-frame))
    (if ret
        (progn
          (send *ri* :angle-vector (send *spotkinova* :angle-vector) 5000)
          (send *ri* :wait-interpolation)
          (ros::ros-info "succeed to approach door button"))
        (progn
          (ros::ros-error "IK Failed")
          (send *spotkinova* :kinova-rest-pose)
          (send *ri* :angle-vector (send *spotkinova* :angle-vector) 3000)
          (send *ri* :wait-interpolation)
          (return-from open-automatic-door nil))
        )
    ;; move hand to touch position
    (setq ret (send *spotkinova* :head :inverse-kinematics door-button-touch-frame))
    (if ret
        (progn
          (send *ri* :angle-vector (send *spotkinova* :angle-vector) 1000)
          (send *ri* :wait-interpolation)
          (ros::ros-info "succeed to touch door button"))
        (progn
          (ros::ros-error "IK Failed")
          (send *spotkinova* :kinova-rest-pose)
          (send *ri* :angle-vector (send *spotkinova* :angle-vector) 3000)
          (send *ri* :wait-interpolation)
          (return-from open-automatic-door nil))
        )
    ;;; move to kinova-rest-pose
    (send *spotkinova* :head :inverse-kinematics door-button-approach-frame)
    (send *ri* :angle-vector (send *spotkinova* :angle-vector) 1000)
    (send *ri* :wait-interpolation)
    (send *spotkinova* :kinova-rest-pose)
    (send *ri* :angle-vector (send *spotkinova* :angle-vector) 3000)
    (send *ri* :wait-interpolation)
    t)
  )
