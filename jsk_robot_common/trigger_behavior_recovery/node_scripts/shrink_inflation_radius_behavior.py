#!/usr/bin/env python

import rospy
import actionlib
from trigger_behavior_msgs.msg import TriggerBehaviorAction
from trigger_behavior_msgs.msg import TriggerBehaviorResult


class ShrinkInflationRadiusBehavior(object):

    def __init__(self):

        self._action_server = actionlib.SimpleActionServer(
            '~behavior',
            TriggerBehaviorAction,
            self.handler,
            False)
        self._action_server.start()

    def handler(self, goal):

        result = TriggerBehaviorResult()
        result.success = True
        self._action_server.set_succeeded(result)


if __name__ == '__main__':

    rospy.init_node('shrink_inflation_radius_behavior')
    node = SpeakAndWaitBehavior()
    rospy.spin()
