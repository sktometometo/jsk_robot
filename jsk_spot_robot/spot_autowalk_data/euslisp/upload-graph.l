#!/usr/bin/env roseus

(load "package://spoteus/spot-interface.l")


(defun main ()
  (spot-init)
  (let*
    ((graph-name (ros::get-param "~graph_name" ""))
     (full-graph-path (format nil "~A/autowalk/~A"
                              (ros::rospack-find "spot_autowalk_data")
                              graph-name)))
    (send *ri* :upload-graph full-graph-path)
    ))

(main)
