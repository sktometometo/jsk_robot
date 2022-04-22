#!/usr/bin/env python

import rospy
import message_filters
import tf2_ros
import tf2_geometry_msgs
import PyKDL

from jsk_recognition_msgs.msg import BoundingBox
from jsk_recognition_msgs.msg import BoundingBoxArray
from jsk_recognition_msgs.msg import ObjectArray

from std_msgs.msg import Header

from geometry_msgs.msg import PointStamped


class TrackSinglePersonNode(object):

    def __init__(self):

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

        self.pub_bbox = rospy.Publisher(
            '~target_bbox', BoundingBox, queue_size=1)

        self.target_track_id = None
        self.target_point = None
        self.time_target_track_lost = None
        self.param_target_track_duration = rospy.Duration(
            rospy.get_param('~target_track_duration', 3.0))
        sub_bbox_array = message_filters.Subscriber(
            '~bbox_array', BoundingBoxArray)
        sub_obj_array = message_filters.Subscriber('~obj_array', ObjectArray)
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [sub_bbox_array, sub_obj_array], 10, 0.1, allow_headerless=False)
        self.ts.registerCallback(self.callback)

        self.point_clicked = None
        self.time_clicked = None
        self.param_target_search_distance = rospy.get_param(
            '~target_search_distance', 3.0)
        self.param_target_search_duration = rospy.Duration(
            rospy.get_param('~target_search_duration', 5.0))
        self.sub_clicked_point = rospy.Subscriber(
            '~clicked_point', PointStamped, self.callback_clicked)

    def callback_clicked(self, msg):

        self.time_clicked = msg.header.stamp
        self.point_clicked = msg

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

    def callback(self, msg_bbox_array, msg_obj_array):

        if self.point_clicked is not None:

            if rospy.Time.now() > self.param_target_search_duration + self.time_clicked:
                rospy.logerr('Not found target.')
                self.point_clicked = None
                self.time_clicked = None
            else:
                if len(msg_bbox_array.boxes) == 0:
                    return

                closest_index = self.get_nearest_bbox_index(
                        self.point_clicked,
                        msg_bbox_array,
                        self.param_target_search_distance
                        )

                if closest_index is not None:
                    self.target_track_id = msg_obj_array.objects[closest_index].id
                    self.target_pose = None
                    self.point_clicked = None
                    self.time_clicked = None
                    rospy.loginfo('Find target with {}'.format(self.target_track_id))

        if self.target_track_id is not None:
            if self.target_track_id in [obj.id for obj in msg_obj_array.objects]:
                target_index = [obj.id for obj in msg_obj_array.objects].index(
                    self.target_track_id)
                bbox = msg_bbox_array.boxes[target_index]
                obj = msg_obj_array.objects[target_index]
                self.target_point = PointStamped(
                        header=Header(frame_id=bbox.header.frame_id),
                        point=bbox.pose.position
                        )
                bbox.header.stamp = rospy.Time.now()
                self.pub_bbox.publish(bbox)
                self.time_target_track_lost = None
            else:
                if self.time_target_track_lost is None:
                    self.time_target_track_lost = rospy.Time.now()
                else:
                    if rospy.Time.now() > self.time_target_track_lost + self.param_target_track_duration:
                        rospy.logerr('Lost ID: {}'.format(
                            self.target_track_id))

                        closest_index = self.get_nearest_bbox_index(
                            self.target_point,
                            msg_bbox_array,
                            self.param_target_search_distance
                            )

                        if closest_index is None:
                            self.target_track_id = None
                            self.target_point = None
                            self.time_target_track_lost = None
                        else:
                            self.target_track_id = msg_obj_array.objects[closest_index].id
                            rospy.loginfo('Find a new target with {}'.format(self.target_track_id))


if __name__ == '__main__':
    rospy.init_node('track_single_person_node')
    node = TrackSinglePersonNode()
    rospy.spin()
