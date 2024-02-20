#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy

from jsk_spot_behavior_manager.behavior_graph_ros import BehaviorGraphNode


def main():
    rospy.init_node("behavior_graph_node")
    node = BehaviorGraphNode()
    node.spin()


if __name__ == "__main__":
    main()
