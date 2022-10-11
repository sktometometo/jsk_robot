#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import copy
import rospy
import actionlib
import tf2_ros

from move_base_msgs.msg import MoveBaseAction
from move_base_msgs.msg import MoveBaseActionGoal
from move_base_msgs.msg import MoveBaseGoal
from move_base_msgs.msg import MoveBaseResult
from nav_msgs.srv import GetPlan
from nav_msgs.srv import GetPlanRequest
from geometry_msgs.msg import PoseStamped


class SuperMoveBaseServer(object):

    def __init__(self):

        self.map_frame_id = rospy.get_param('~map_frame_id', 'map')
        self.base_frame_id = rospy.get_param('~base_frame_id', 'base_link')

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

        self.planning_client = rospy.ServiceProxy('~plan', GetPlan)

        self.move_base_client = actionlib.SimpleActionClient('~target_move_base', MoveBaseAction)
        self.move_base_server = actionlib.SimpleActionServer('~move_base', MoveBaseAction, self.execute, False)
        self.action_goal_pub = rospy.Publisher('~move_base/goal', MoveBaseActionGoal, queue_size=1)
        self.simple_move_base = rospy.Subscriber('~move_base_simple', PoseStamped, self.callback)

        self.move_base_server.start()

    def callback(self, msg):

        action_goal = MoveBaseActionGoal()
        action_goal.header.stamp = rospy.Time.now()
        action_goal.goal.target_pose = msg
        self.action_goal_pub.publish(action_goal)

    def get_current_pose(self):

        try:
            transform = self.tf_buffer.lookup_transform(
                    self.base_frame_id,
                    self.map_frame_id,
                    rospy.Time(),
                    rospy.Duration(1)
                    )
        except (tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as e:
            rospy.logwarn('Error: {}'.format(e))
            return None

        current_pose = PoseStamped()
        current_pose.header = transform.header
        current_pose.position.x = transform.translation.x
        current_pose.position.y = transform.translation.y
        current_pose.position.z = transform.translation.z
        current_pose.rotation.x = transform.orientation.x
        current_pose.rotation.y = transform.orientation.y
        current_pose.rotation.z = transform.orientation.z
        current_pose.rotation.w = transform.orientation.w

        return current_pose

    def feedback_cb(self, feedback):

        self.move_base_server.publish_feedback(feedback)

    def execute(self, goal):

        start_pose = self.get_current_pose()
        goal_pose = goal.target_pose()

        req = GetPlanRequest()
        req.start_pose = start_pose
        modified_goal = None
        for (dx, dy) in itertools.product([0, -1, 1], [0, -1, 1]):
            req.goal_pose = copy.deepcopy(goal_pose)
            req.goal_pose.position.x += dx
            req.goal_pose.position.y += dy
            plan = self.planning_client(req)
            if len(plan.poses) != 0:
                modified_goal = MoveBaseGoal()
                modified_goal.target_pose = req.goal_pose
                break

        if modified_goal is None:
            rospy.logerr('No valid plan found.')
            result = MoveBaseResult()
            self.move_base_server.set_aborted(result)
            return

        rospy.logwarn('modified goal: {}'.format(modified_goal))

        self.move_base_client.send_goal(
                                modified_goal,
                                feedback_cb=self.feedback_cb
                                )
        retry_count = 0
        planning_failed_count = 0
        while not rospy.is_shutdown():
            if self.move_base_client.wait_for_result(timeout=rospy.Duration(1)):
                result = self.move_base_client.get_result()
                self.move_base_server.set_succeeded(result)
                return
            if self.move_base_server.is_preempt_requested():
                self.move_base_client.cancel_goal()
                result = self.move_base_client.get_result()
                self.move_base_server.set_aborted(result)
                return
            current_pose = self.get_current_pose()
            target_pose = modified_goal.goal_pose
            req = GetPlanRequest()
            req.start_pose = current_pose
            req.goal_pose = target_pose
            plan = self.planning_client(req)
            if len(plan.poses) == 0:
                planning_failed_count += 1
            else:
                planning_failed_count = 0
            if planning_failed_count > 2:
                if retry_count > 2:
                    rospy.logerr('Failure continued after retrying.')
                    self.move_base_client.cancel_goal()
                    result = MoveBaseResult()
                    self.move_base_server.set_aborted(result)
                    return
                retry_count += 1
                req = GetPlanRequest()
                req.start_pose = current_pose
                modified_goal = None
                for (dx, dy) in itertools.product([0, -1, 1], [0, -1, 1]):
                    req.goal_pose = copy.deepcopy(goal_pose)
                    req.goal_pose.position.x += dx
                    req.goal_pose.position.y += dy
                    plan = self.planning_client(req)
                    if len(plan.poses) != 0:
                        modified_goal = MoveBaseGoal()
                        modified_goal.target_pose = req.goal_pose
                        break
                if modified_goal is None:
                    rospy.logerr('No valid plan found even after retrying.')
                    self.move_base_client.cancel_goal()
                    result = MoveBaseResult()
                    self.move_base_server.set_aborted(result)
                    return
                else:
                    self.move_base_client.send_goal(
                                            modified_goal,
                                            feedback_cb=self.feedback_cb
                                            )


if __name__ == '__main__':

    rospy.init_node('super_move_base_server')
    node = SuperMoveBaseServer()
    rospy.spin()
