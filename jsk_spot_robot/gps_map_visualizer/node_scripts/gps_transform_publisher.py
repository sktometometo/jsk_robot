#!/usr/bin/env python3


import threading
from typing import Optional

import message_filters
import numpy as np
import PyKDL
import rospy
import tf2_geometry_msgs
import tf2_ros
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
from sensor_msgs.msg import NavSatFix, NavSatStatus

from gps_map_visualizer import calc_transform_from_geographic_coords


class GpsBasedTransformPublisher:

    def __init__(self):

        self.reference_longitude = rospy.get_param("~reference_longitude")
        self.reference_latitude = rospy.get_param("~reference_latitude")
        self.reference_frame_id = rospy.get_param("~reference_world_frame_id")

        self.base_frame_id = rospy.get_param("~base_frame_id", "gps")
        self.odom_frame_id = rospy.get_param("~odom_frame_id", None)

        self.transform_reference_to_odom: Optional[TransformStamped] = None

        self.lock_history = threading.Lock()
        self.history_reference_points = []
        self.history_odom_points = []

        self.tf_br = tf2_ros.TransformBroadcaster()

        sub_nav_sat_fix = message_filters.Subscriber("~nav_sat_fix", NavSatFix)
        sub_odom = message_filters.Subscriber("~odom", Odometry)
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [sub_nav_sat_fix, sub_odom], 10, 0.1
        )
        self.ts.registerCallback(self.callback)

    def spin(self):
        while not rospy.is_shutdown():
            with self.lock_history:
                if len(self.history_reference_points) > 4:
                    rot, rssd, sens = Rotation.align_vectors(
                        np.array(self.history_reference_points).T,
                        np.array(self.history_odom_points).T,
                    )
                    translation = np.mean(
                        np.array(self.history_odom_points)
                        - np.dot(
                            rot.as_matrix(), np.array(self.history_reference_points)
                        ),
                        axis=1,
                    )
                    rospy.loginfo(f"Rotation: {rot}")
                    rospy.loginfo(f"RSSD: {rssd}, SENS: {sens}")
                    rospy.loginfo(f"Translation: {translation}")

    def calback(self, msg_nav_sat_fix: NavSatFix, msg_odom: Odometry):
        if msg_nav_sat_fix.status.status != NavSatStatus.STATUS_NO_FIX:
            diff_x, diff_y = calc_transform_from_geographic_coords(
                self.reference_longitude,
                self.reference_latitude,
                msg_nav_sat_fix.longitude,
                msg_nav_sat_fix.latitude,
            )
            diff_z = msg_nav_sat_fix.altitude

            with self.lock_history:
                self.history_reference_points.append(np.array([diff_x, diff_y, diff_z]))
                self.history_odom_points.append(
                    np.array(
                        [
                            msg_odom.pose.pose.position.x,
                            msg_odom.pose.pose.position.y,
                            msg_odom.pose.pose.position.z,
                        ]
                    )
                )


if __name__ == "__main__":

    rospy.init_node("gps_based_transform_publisher", anonymous=True)
    node = GpsBasedTransformPublisher()
    node.spin()
