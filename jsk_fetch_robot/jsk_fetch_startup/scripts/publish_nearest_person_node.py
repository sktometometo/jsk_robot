#!/usr/bin/env python

import rospy
import tf2_ros
import tf2_geometry_msgs
import PyKDL

from jsk_recognition_msgs.msg import BoundingBox
from jsk_recognition_msgs.msg import BoundingBoxArray

from geometry_msgs.msg import PointStamped


class TrackSinglePersonNode(object):

    def __init__(self):

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

        self.param_target_search_distance = rospy.get_param('~target_search_distance', 3.0)
        self.param_robot_frame_id = rospy.get_param('~robot_frame_id', 'base_link')

        self.pub_bbox = rospy.Publisher('~target_bbox', BoundingBox, queue_size=1)
        self.sub_bbox_array = rospy.Subscriber('~bbox_array', BoundingBoxArray, self.callback)

    def get_nearest_bbox_index(self, msg_point_stamped, msg_bbox_array, target_search_distance):

        try:
            kdlframe_clicked_frame_to_bbox_frame = tf2_geometry_msgs.transform_to_kdl(
                self.tf_buffer.lookup_transform(
                    msg_point_stamped.header.frame_id,
                    msg_bbox_array.header.frame_id,
                    rospy.Time.now()
                )
            )
        except (tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as e:
            rospy.logerr(e)
            return None
        kdlframe_clicked_frame_to_clicked_point = PyKDL.Frame(
            PyKDL.Rotation.Quaternion(0, 0, 0, 1),
            PyKDL.Vector(
                msg_point_stamped.point.x,
                msg_point_stamped.point.y,
                msg_point_stamped.point.z
            )
        )

        def calc_distance_to_clicked_point(bbox):

            kdlframe_bbox_frame_to_bbox_pose = PyKDL.Frame(
                PyKDL.Rotation.Quaternion(
                    bbox.pose.orientation.x,
                    bbox.pose.orientation.y,
                    bbox.pose.orientation.z,
                    bbox.pose.orientation.w,
                ),
                PyKDL.Vector(
                    bbox.pose.position.x,
                    bbox.pose.position.y,
                    bbox.pose.position.z,
                )
            )
            kdlframe_clicked_point_to_box_pose = \
                kdlframe_clicked_frame_to_clicked_point.Inverse() \
                * kdlframe_clicked_frame_to_bbox_frame \
                * kdlframe_bbox_frame_to_bbox_pose
            return kdlframe_clicked_point_to_box_pose.p.Norm()

        closest_index = msg_bbox_array.boxes.index(
            min(msg_bbox_array.boxes,
                key=calc_distance_to_clicked_point)
        )

        if calc_distance_to_clicked_point(msg_bbox_array.boxes[closest_index]) > target_search_distance:
            rospy.logwarn('cannot find object')
            return None

        return closest_index

    def callback(self, msg_bbox_array):

        target_point = PointStamped()
        target_point.header.frame_id = self.param_robot_frame_id

        closest_index = self.get_nearest_bbox_index(
            target_point,
            msg_bbox_array,
            self.param_target_search_distance
            )

        if closest_index is not None:
            msg_bbox = msg_bbox_array.boxes[closest_index]
            self.pub_bbox.publish(msg_bbox)
        else:
            rospy.logerr('Not found a person.')


if __name__ == '__main__':
    rospy.init_node('publish_nearest_person_node')
    node = TrackSinglePersonNode()
    rospy.spin()
