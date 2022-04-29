#!/usr/bin/env python

import rospy

import tf2_ros
import tf2_geometry_msgs

import PyKDL

from semanticmap.msg import GridCellArray
from semanticmap.msg import SemanticMapGrid
from semanticmap.msg import SemanticMapMetaData

from nav_msgs.msg import Path

from geometry_msgs.msg import PoseArray
from geometry_msgs.msg import Pose
from geometry_msgs.msg import Point
from geometry_msgs.msg import TransformStamped
from geometry_msgs.msg import Quaternion


class SemanticCelListServer(object):

    def __init__(self):

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster()

        self.msg_grid = rospy.wait_for_message('/semantic_map', SemanticMapGrid)
        self.msg_meta = rospy.wait_for_message('/semantic_map_metadata', SemanticMapMetaData)

        self.pub_pose_array = rospy.Publisher(
            '~debug_pose_array', PoseArray, queue_size=1)
        self.pub_grid_cell_array = rospy.Publisher(
                '~semantic_cell_array', GridCellArray, queue_size=1)

        self.sub = rospy.Subscriber(
            '/move_base/TrajectoryPlannerROS/local_plan', Path, self.callback)

    def publish_pose_array(self, kdlframe_list, frame_id):

        msg = PoseArray()
        msg.header.stamp = rospy.Time.now()
        msg.header.frame_id = frame_id
        for kdlframe in kdlframe_list:
            msg.poses.append(
                Pose(
                    position=Point(
                        x=kdlframe.p[0],
                        y=kdlframe.p[1],
                        z=kdlframe.p[2]
                    ),
                    orientation=Quaternion(
                        x=kdlframe.M.GetQuaternion()[0],
                        y=kdlframe.M.GetQuaternion()[1],
                        z=kdlframe.M.GetQuaternion()[2],
                        w=kdlframe.M.GetQuaternion()[3]
                    )
                )
            )
        self.pub_pose_array.publish(msg)

    def publish_cell_array(self, grid_cell_array):
        msg = GridCellArray()
        msg.array = grid_cell_array
        self.pub_pose_array.publish(msg)

    def broadcast(self, kdlframe, parent_frame_id, child_frame_id):

        msg = TransformStamped()
        msg.header.stamp = rospy.Time.now()
        msg.header.frame_id = parent_frame_id
        msg.child_frame_id = child_frame_id
        msg.transform.translation.x = kdlframe.p[0]
        msg.transform.translation.y = kdlframe.p[1]
        msg.transform.translation.z = kdlframe.p[2]
        msg.transform.rotation.x = kdlframe.M.GetQuaternion()[0]
        msg.transform.rotation.y = kdlframe.M.GetQuaternion()[1]
        msg.transform.rotation.z = kdlframe.M.GetQuaternion()[2]
        msg.transform.rotation.w = kdlframe.M.GetQuaternion()[3]
        self.tf_broadcaster.sendTransform(msg)

    def callback(self, msg_path):

        kdlframe_list_on_grid, semantics_cell_list = self.get_pose_list_on_grid_from_path(
            msg_path, self.msg_grid, self.msg_meta)
        self.publish_pose_array(kdlframe_list_on_grid, self.msg_grid.header.frame_id)
        self.publish_cell_array(semantics_cell_list)

    def get_pose_list_on_grid_from_path(self, msg_path, msg_grid, msg_meta):

        grid_frame_id = msg_grid.header.frame_id
        path_frame_id = msg_path.header.frame_id

        try:
            transform = self.tf_buffer.lookup_transform(
                grid_frame_id,
                path_frame_id,
                rospy.Time()
            )
            kdlframe_grid_frame_to_path_frame = tf2_geometry_msgs.transform_to_kdl(
                transform
            )
        except (tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException):
            return None

        kdlframe_grid_frame_to_grid_pose = PyKDL.Frame(
            PyKDL.Rotation.Quaternion(
                msg_meta.origin.orientation.x,
                msg_meta.origin.orientation.y,
                msg_meta.origin.orientation.z,
                msg_meta.origin.orientation.w
            ),
            PyKDL.Vector(
                msg_meta.origin.position.x,
                msg_meta.origin.position.y,
                msg_meta.origin.position.z
            )
        )
        self.broadcast(
                kdlframe_grid_frame_to_grid_pose,
                grid_frame_id,
                'map_origin'
                )

        kdlframe_list_on_grid_frame = []
        kdlframe_list_on_grid_pose = []

        for pose in msg_path.poses:

            kdlframe_path_frame_to_path_pose = PyKDL.Frame(
                PyKDL.Rotation.Quaternion(
                    pose.pose.orientation.x,
                    pose.pose.orientation.y,
                    pose.pose.orientation.z,
                    pose.pose.orientation.w
                ),
                PyKDL.Vector(
                    pose.pose.position.x,
                    pose.pose.position.y,
                    pose.pose.position.z
                )
            )

            kdlframe_grid_frame_to_path_pose = \
                kdlframe_grid_frame_to_path_frame \
                * kdlframe_path_frame_to_path_pose
            kdlframe_list_on_grid_frame.append(
                kdlframe_grid_frame_to_path_pose)

            kdlframe_grid_pose_to_path_pose = \
                kdlframe_grid_frame_to_grid_pose.Inverse() \
                * kdlframe_grid_frame_to_path_frame \
                * kdlframe_path_frame_to_path_pose
            kdlframe_list_on_grid_pose.append(kdlframe_grid_pose_to_path_pose)

        semantics_cell_list = []

        for kdlframe in kdlframe_list_on_grid_pose:

            index_x = int(kdlframe.p[0] / msg_grid.info.resolution)
            index_y = int(kdlframe.p[1] / msg_grid.info.resolution)
            semantics_cell = msg_grid.data[index_x + msg_grid.info.width * index_y]
            semantics_cell_list.append(semantics_cell)

        return kdlframe_list_on_grid_frame, semantics_cell_list


def main():

    rospy.init_node('semantic_cell_list_server')
    node = SemanticCelListServer()
    rospy.spin()


if __name__ == '__main__':
    main()
