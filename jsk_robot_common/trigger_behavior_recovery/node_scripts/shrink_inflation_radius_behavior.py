#!/usr/bin/env python

import rospy
import actionlib
import dynamic_reconfigure.client
import threading

from trigger_behavior_msgs.msg import TriggerBehaviorAction
from trigger_behavior_msgs.msg import TriggerBehaviorResult
from move_base_msgs.msg import MoveBaseActionResult


class ShrinkInflationRadiusBehavior(object):

    def __init__(self):

        self.target_local_radius = rospy.get_param('~target_local_radius', 0.1)
        self.target_global_radius = rospy.get_param('~target_global_radius', 0.1)

        target_local_param_name = rospy.get_param('~target_local_param_name', '/move_base/local_costmap/inflater')
        target_global_param_name = rospy.get_param('~target_global_param_name', '/move_base/global_costmap/inflater')

        self.lock_stored_radius = threading.Lock()
        self.stored_local_radius = None
        self.stored_global_radius = None

        self._reconfigure_client_local = dynamic_reconfigure.client.Client(
                target_local_param_name,
                timeout=30,
                config_callback=callback
                )

        self._reconfigure_client_global = dynamic_reconfigure.client.Client(
                target_global_param_name,
                timeout=30,
                config_callback=callback
                )

        self._result_subscriber = rospy.Subscriber(
                '/move_base/result',
                MoveBaseActionResult,
                self.callback_result
                )

        self._action_server = actionlib.SimpleActionServer(
            '~behavior',
            TriggerBehaviorAction,
            self.handler,
            False)
        self._action_server.start()

    def update_inflation_radius(self, local_radius, global_radius):

        self._reconfigure_client_local.update_configuration({'inflation_radius': local_radius})
        self._reconfigure_client_global.update_configuration({'inflation_radius': global_radius})

    def get_inflation_radius(self):

    def handler(self, goal):

        result = TriggerBehaviorResult()
        result.success = True

        with self.lock_stored_radius:

        self._action_server.set_succeeded(result)


if __name__ == '__main__':

    rospy.init_node('shrink_inflation_radius_behavior')
    node = SpeakAndWaitBehavior()
    rospy.spin()
