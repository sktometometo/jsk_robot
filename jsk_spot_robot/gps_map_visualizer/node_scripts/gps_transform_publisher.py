#!/usr/bin/env python3


import threading
from typing import Optional

import rospy
import tf2_ros
from geometry_msgs.msg import TransformStamped
from sensor_msgs.msg import NavSatFix

from gps_map_visualizer import calc_transform_from_geographic_coords


class GpsBasedTransformPublisher:

    def __init__(self):

        self.reference_longitude = rospy.get_param("~reference_longitude")
        self.reference_latitude = rospy.get_param("~reference_latitude")
        self.reference_altitude = rospy.get_param("~reference_altitude")
        self.reference_frame_id = rospy.get_param("~reference_world_frame_id")

        self.base_frame_id = rospy.get_param("~base_frame_id", "gps")

        self._sub_nav_sat_fix = rospy.Subscriber(
            "~nav_sat_fix", NavSatFix, self.callback
        )

        self.lock_transform = threading.Lock()
        self.transform_reference_to_base: Optional[TransformStamped] = None

        self.tf_br = tf2_ros.TransformBroadcaster()

        rospy.loginfo("Initialized")

    def spin(self):
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            rate.sleep()
            with self.lock_transform:
                if self.transform_reference_to_base is not None:
                    self.tf_br.sendTransform(self.transform_reference_to_base)

    def callback(self, msg_nav_sat_fix: NavSatFix):

        longitude = msg_nav_sat_fix.longitude
        latitude = msg_nav_sat_fix.latitude
        altitude = msg_nav_sat_fix.altitude

        diff_x, diff_y = calc_transform_from_geographic_coords(
            self.reference_longitude,
            self.reference_latitude,
            longitude,
            latitude,
        )
        diff_z = altitude - self.reference_altitude

        transform = TransformStamped()
        transform.header.stamp = rospy.Time.now()
        transform.header.frame_id = self.reference_frame_id
        transform.child_frame_id = self.base_frame_id
        transform.transform.translation.x = diff_x
        transform.transform.translation.y = diff_y
        transform.transform.translation.z = diff_z
        transform.transform.rotation.w = 1.0

        with self.lock_transform:
            self.transform_reference_to_base = transform


if __name__ == "__main__":

    rospy.init_node("gps_based_transform_publisher", anonymous=True)
    node = GpsBasedTransformPublisher()
    node.spin()
