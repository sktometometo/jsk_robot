#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import rospy
import tf2_ros
import math
from geometry_msgs.msg import Twist
from geometry_msgs.msg import PoseStamped


'''
前提条件として
    - 対象者はロボットより後ろにいる
    - 対象者はロボットと一列
    - ロボットのbase_linkは常に進行方向を向いている

    ロボットの速度に以下の係数をかけて、人との位置を保とうとさせる。
'''


class Node(object):

    def __init__(self):

        self.frame_id_robot = rospy.get_param('~frame_id_robot', 'base_link')

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listner = tf2_ros.TransformListner(self.tf_buffer)

        self.target_distance = rospy.get_param('~target_distance', 2.0)

        self.coef_linear = 1.0
        self.coef_angular = 1.0

        self.pub = rospy.Publisher('~output', Twist, queue_size=1)
        self.sub_twist = rospy.Subscriber('~input', Twist, self.callback_twist)
        self.sub_pose = rospy.Subscriber(
            '~input_target_person', PoseStamped, self.callback_pose)

    def callback_pose(self, msg):

        if msg.header.frame_id == self.frame_id_robot:
            distance = math.sqrt(
                msg.pose.position.x ** 2 +
                msg.pose.position.y ** 2 +
                msg.pose.position.z ** 2
            )
        else:
            try:
                transform = self.tf_buffer.lookup_transform(
                    self.frame_id_robot,
                    msg.header.frame_id,
                    rospy.Time()
                )
            except (tf2_ros.LookupException,
                    tf2_ros.ConnectivityException,
                    tf2_ros.ExtrapolationException) as e:
                rospy.logerr('{}'.format(e))
                return
            distance = math.sqrt(
                transform.transform.translation.x ** 2 +
                transform.transform.translation.y ** 2 +
                transform.transform.translation.z ** 2
            )

        diff_distance = self.target_distance - distance
        self.coef_linear = 1.0 + 1.0 * \
            min(diff_distance, self.target_distance) / self.target_distance
        self.coef_angular = 1.0 + 1.0 * \
            min(diff_distance, self.target_distance) / self.target_distance

    def callback_twist(self, msg):

        msg_out = Twist()
        msg_out.linear.x = self.coef_linear * msg.linear.x
        msg_out.linear.y = self.coef_linear * msg.linear.y
        msg_out.angular.z = self.coef_angular * msg.angular.z
        self.pub.publish(msg_out)


if __name__ == '__main__':

    rospy.init_node('fuga')

    node = Node()
