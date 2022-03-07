import spot_ros_client.libspotros as libspotros

import PyKDL
import rospy
import math
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import PoseArray


def calc_distance_to_pose(pose):

    return pose.position.x ** 2 + pose.position.y ** 2 + pose.position.z ** 2


def convert_msg_point_to_kdl_vector(point):

    return PyKDL.Vector(point.x, point.y, point.z)


def get_nearest_person_pose():

    try:
        msg = rospy.wait_for_message('~people_pose_array', PoseArray,
                                     timeout=rospy.Duration(5))
    except rospy.ROSException as e:
        rospy.logwarn('Timeout exceede: {}'.format(e))
        return None

    if len(msg.poses) == 0:
        rospy.logwarn('No person visible')
        return None

    distance = calc_distance_to_pose(msg.poses[0])
    target_pose = msg.poses[0]
    for pose in msg.poses:
        if calc_distance_to_pose(pose) < distance:
            distance = calc_distance_to_pose(pose)
            target_pose = pose

    pose_stamped = PoseStamped()
    pose_stamped.header = msg.header
    pose_stamped.pose = target_pose

    return pose_stamped


def get_diff_for_person(pose_stamped):

    x = pose_stamped.pose.position.x
    y = pose_stamped.pose.position.y
    z = pose_stamped.pose.position.z

    yaw = math.atan2(y, x)
    try:
        pitch = math.acos(z / math.sqrt(x**2 + y**2))
    except ValueError:
        pitch = 0
    return pitch, yaw
