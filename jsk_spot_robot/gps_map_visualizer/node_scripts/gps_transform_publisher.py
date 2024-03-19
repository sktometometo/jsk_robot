#!/usr/bin/env python


import rospy
import tf2_ros
from geometry_msgs.msg import TransformStamped
from sensor_msgs.msg import NavSatFix, NavSatStatus

from gps_map_visualizer import calc_transform_from_geographic_coords


class GpsBasedTransformPublisher:

    def __init__(self):

        self.reference_longitude = rospy.get_param("~reference_longitude")
        self.reference_latitude = rospy.get_param("~reference_latitude")
        self.reference_frame_id = rospy.get_param("~reference_world_frame_id")

        self.gps_frame_id = rospy.get_param("~gps_frame_id", "gps")

        self.tf_br = tf2_ros.TransformBroadcaster()

        self.sub_nav_sat_fix = rospy.Subscriber(
            "~nav_sat_fix", NavSatFix, self.nav_sat_fix_callback
        )

    def nav_sat_fix_callback(self, msg: NavSatFix):

        diff_x, diff_y = calc_transform_from_geographic_coords(
            self.reference_longitude,
            self.reference_latitude,
            msg.longitude,
            msg.latitude,
        )

        transform = TransformStamped()
        transform.header.frame_id = self.reference_frame_id
        transform.header.stamp = msg.header.stamp
        transform.child_frame_id = self.gps_frame_id
        transform.transform.translation.x = diff_x
        transform.transform.translation.y = diff_y
        transform.transform.translation.z = 0.0
        transform.transform.rotation.w = 1.0

        self.tf_br.sendTransform(transform)


if __name__ == "__main__":

    rospy.init_node("gps_based_transform_publisher", anonymous=True)
    node = GpsBasedTransformPublisher()
    rospy.spin()
