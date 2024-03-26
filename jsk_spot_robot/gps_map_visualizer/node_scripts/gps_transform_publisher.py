#!/usr/bin/env python


import rospy
import PyKDL
import traceback
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
        self.parent_of_gps_frame_id = rospy.get_param("~parent_of_gps_frame_id", None)

        self.tf_br = tf2_ros.TransformBroadcaster()
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

        self.sub_nav_sat_fix = rospy.Subscriber(
            "~nav_sat_fix", NavSatFix, self.nav_sat_fix_callback
        )

        initial_longitude = rospy.get_param("~initial_longitude", None)
        initial_latitude = rospy.get_param("~initial_latitude", None)

        if isinstance(initial_longitude, float) and isinstance(initial_latitude, float):
            rospy.sleep(5.0)
            rospy.loginfo("Publish initial frame")
            self.nav_sat_fix_callback(
                    NavSatFix(
                        status=NavSatStatus(status=NavSatStatus.STATUS_FIX),
                        longitude=initial_longitude,
                        latitude=initial_latitude))

    def nav_sat_fix_callback(self, msg: NavSatFix):

        if msg.status.status != NavSatStatus.STATUS_NO_FIX:

            diff_x, diff_y = calc_transform_from_geographic_coords(
                self.reference_longitude,
                self.reference_latitude,
                msg.longitude,
                msg.latitude,
            )

            transform_reference_to_gps = PyKDL.Frame(
                    PyKDL.Rotation(),
                    PyKDL.Vector(diff_x, diff_y, 0)
                    )
            if self.parent_of_gps_frame_id is None:
                transform_to_broadcast = transform_reference_to_gps
                transform_child_frame_id = self.gps_frame_id
            else:
                try:
                    transform_gps_parent_to_gps = self.tf_buffer.lookup_transform(
                            self.gps_frame_id,
                            self.parent_of_gps_frame_id,
                            rospy.Time(0)
                            )
                except Exception as e:
                    rospy.logerr(e)
                    rospy.logerr(traceback.format_exec())
                    return
                transform_to_broadcast = transform_gps_parent_to_gps * transform_gps_parent_to_gps.Inverse()
                transform_child_frame_id = self.parent_of_gps_frame_id

            transform = TransformStamped()
            transform.header.frame_id = self.reference_frame_id
            transform.header.stamp = rospy.Time.now()
            transform.child_frame_id = transform_child_frame_id
            transform.transform.translation.x = transform_to_broadcast.p[0]
            transform.transform.translation.y = transform_to_broadcast.p[1]
            transform.transform.translation.z = transform_to_broadcast.p[2]
            transform.transform.rotation.x = transform_to_broadcast.M.GetQuaternion()[0]
            transform.transform.rotation.y = transform_to_broadcast.M.GetQuaternion()[1]
            transform.transform.rotation.z = transform_to_broadcast.M.GetQuaternion()[2]
            transform.transform.rotation.w = transform_to_broadcast.M.GetQuaternion()[3]
            self.tf_br.sendTransform(transform)


if __name__ == "__main__":

    rospy.init_node("gps_based_transform_publisher", anonymous=True)
    node = GpsBasedTransformPublisher()
    rospy.spin()
