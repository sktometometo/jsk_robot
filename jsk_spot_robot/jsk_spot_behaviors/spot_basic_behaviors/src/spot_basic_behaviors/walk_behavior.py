# -*- coding: utf-8 -*-

from jsk_spot_behavior_manager.base_behavior import BaseBehavior

import rospy
import time


class WalkBehavior(BaseBehavior):

    def run_initial(self, start_node, end_node, edge, pre_edge):

        rospy.logdebug('run_initial() called')
        self.silent_mode = rospy.get_param('~silent_mode', True)
        return True

    def run_main(self, start_node, end_node, edge, pre_edge):

        rospy.logdebug('run_main() called')

        graph_name = edge.properties['graph']
        start_id = list(filter(
            lambda x: x['graph'] == graph_name,
            start_node.properties['waypoints_on_graph']
        ))[0]['id']
        end_id = list(filter(
            lambda x: x['graph'] == graph_name,
            end_node.properties['waypoints_on_graph']
        ))[0]['id']
        localization_method = list(filter(
            lambda x: x['graph'] == graph_name,
            start_node.properties['waypoints_on_graph']
        ))[0]['localization_method']

        # graph uploading and localization
        if pre_edge is not None and \
                graph_name == pre_edge.properties['graph']:
            rospy.loginfo('graph upload and localization skipped.')
        else:
            # Upload
            ret = self.spot_client.upload_graph(graph_name)
            if ret[0]:
                rospy.loginfo('graph {} uploaded.'.format(graph_name))
            else:
                rospy.logerr('graph uploading failed: {}'.format(ret[1]))
                return False
            # Localization
            if localization_method == 'fiducial':
                ret = self.spot_client.set_localization_fiducial()
            elif localization_method == 'waypoint':
                ret = self.spot_client.set_localization_waypoint(start_id)
            else:
                ret = (False, 'Unknown localization method')
            if ret[0]:
                rospy.loginfo('robot is localized on the graph.')
            else:
                rospy.logwarn('Localization failed: {}'.format(ret[1]))
                return False

        # start navigation
        success = False
        rate = rospy.Rate(10)
        num_trials = rospy.get_param('/spot_basic_behaviors/walk_behaviors/num_trials', 5)
        velocity_limit_linear_x = rospy.get_param('/spot_basic_behaviors/walk_behaviors/velocity_limit_linear_x', 1.0)
        velocity_limit_linear_y = rospy.get_param('/spot_basic_behaviors/walk_behaviors/velocity_limit_linear_y', 1.0)
        velocity_limit_angular_z = rospy.get_param('/spot_basic_behaviors/walk_behaviors/velocity_limit_angular_z', 1.0)

        for i in range(num_trials):
            rospy.logerr("{}/{} th trial".format(i, num_trials))
            if not self.silent_mode:
                self.sound_client.say('移動します', blocking=True)
            self.spot_client.navigate_to(
                    end_id,
                    velocity_limit=(
                        velocity_limit_linear_x,
                        velocity_limit_linear_y,
                        velocity_limit_angular_z
                        ),
                    blocking=False)
            while not rospy.is_shutdown():
                rate.sleep()
                if self.spot_client.wait_for_navigate_to_result(rospy.Duration(0.1)):
                    result = self.spot_client.get_navigate_to_result()
                    success = result.success
                    rospy.logerr('Navigation result: {}'.format(result))
                    rospy.logerr('Navigation suceess type: {} value: {}'.format(type(success), success))
                    break

            # recovery on failure
            if success:
                rospy.loginfo("Moving success")
                break
            else:
                rospy.logerr("Returning to {} because of failure".format(start_id))
                if not self.silent_mode:
                    self.sound_client.say('失敗したので元に戻ります', blocking=True)
                self.spot_client.navigate_to(start_id, blocking=True)

            time.sleep(10.)

        return success

    def run_final(self, start_node, end_node, edge, pre_edge):

        rospy.logdebug('run_finalize() called')
