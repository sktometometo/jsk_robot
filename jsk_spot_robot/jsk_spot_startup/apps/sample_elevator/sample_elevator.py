#!/usr/bin/env python3

import rospy
from spot_ros_client.libspotros import SpotRosClient
import actionlib
from jsk_spot_behavior_msgs.msg import NavigationAction
from jsk_spot_behavior_msgs.msg import NavigationGoal


if __name__ == '__main__':

    rospy.init_node("sample_navigation_with_behaviors")
    client = SpotRosClient()

    behavior_client = actionlib.SimpleActionClient("/spot_behavior_manager_server/execute_behaviors", NavigationAction)
    behavior_client.wait_for_server()

    start_node = rospy.get_param('~start_node', 'eng2_73B2_dock')
    target_node = rospy.get_param('~target_node', 'eng2_3FElevator')
    dock_id = int(rospy.get_param('~dock_id', 521))

    client.claim()
    client.power_on()
    client.undock()

    client.reset_current_node(start_node)
    client.execute_behaviors(target_node_id=target_node)
    client.wait_execute_behaviors_result()
    result = client.get_execute_behaviors_result()
    rospy.loginfo("Result forward: {} {}".format(result.success, result.message))

    client.execute_behaviors(target_node_id=start_node)
    result = client.get_execute_behaviors_result()
    rospy.loginfo("Result backward: {} {}".format(result.success, result.message))

    client.dock(dock_id)
