#!/usr/bin/env python

import rospy

import tf2_ros
import tf2_geometry_msgs

import PyKDL

from nav_msgs.msg import OccupancyGrid
from nav_msgs.msg import MapMetaData
from nav_msgs.msg import Path


def get_cell_from_pose(pose_stamped, msg_grid, msg_metadata, tf_buffer):

    stamp = msg_grid.header.stamp

    grid_frame_id = msg_grid.header.frame_id
    pose_frame_id = pose_stamped.header.frame_id

    try:
        transform_grid_to_pose = tf2_geometry_msgs.transform_to_kdl(
            tf_buffer.lookup_transform(
                grid_frame_id,
                pose_frame_id,
                rospy.Time()
            )
        )
    except (tf2_ros.LookupException,
            tf2_ros.ConnectivityException,
            tf2_ros.ExtrapolationException):
        return None

    grid_pose_on_grid_frame = PyKDL.Frame(
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

    path_pose_on_path_frame = PyKDL.Frame(
        PyKDL.Rotation.Quaternion(
            msg_meta.origin.orientation.x,
            msg_meta.origin.orientation.y,
            msg_meta.origin.orientation.z,
            msg_meta.origin.orientation.w
        ),
        PyKDL.Vector(
            msg_meta.position.x,
            msg_meta.position.y,
            msg_meta.position.z
        )
    )


def main():

    rospy.init_node('local_plan_to_semantics_list')

    tf_buffer = tf2_ros.Buffer()
    tf_listener = tf2_ros.TransformListener(tf_buffer)


if __name__ == '__main__':
    main()
