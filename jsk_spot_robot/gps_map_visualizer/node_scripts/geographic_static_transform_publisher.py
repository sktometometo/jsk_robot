#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import math

import rospy
import tf2_ros
from geometry_msgs.msg import TransformStamped

from gps_map_visualizer import calc_transform_from_geographic_coords


class GeographicStaticTransformPublisher:

    def __init__(self):

        self.reference_frame_id = rospy.get_param("~reference_world_frame_id")
        self.reference_latitude = rospy.get_param("~reference_latitude")
        self.reference_longitude = rospy.get_param("~reference_longitude")
        self.reference_altitude = rospy.get_param("~reference_altitude", 0.0)

        self.target_frame_id = rospy.get_param("~target_world_frame_id")
        self.target_latitude = rospy.get_param("~target_latitude")
        self.target_longitude = rospy.get_param("~target_longitude")
        self.target_altitude = rospy.get_param("~target_altitude", 0.0)

        self.tf_br = tf2_ros.StaticTransformBroadcaster()

        diff_x, diff_y = calc_transform_from_geographic_coords(
            self.reference_longitude,
            self.reference_latitude,
            self.target_longitude,
            self.target_latitude,
        )

        transform = TransformStamped()
        transform.header.frame_id = self.reference_frame_id
        transform.child_frame_id = self.target_frame_id
        transform.transform.translation.x = diff_x
        transform.transform.translation.y = diff_y
        transform.transform.translation.z = (
            self.target_altitude - self.reference_altitude
        )
        transform.transform.rotation.w = 1.0

        self.tf_br.sendTransform(transform)


if __name__ == "__main__":
    rospy.init_node("geographic_static_transform_publisher", anonymous=True)
    node = GeographicStaticTransformPublisher()
    rospy.spin()
