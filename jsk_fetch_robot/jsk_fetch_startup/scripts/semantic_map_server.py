#!/usr/bin/env python

import rospy
import cv2
import PyKDL


def main():

    rospy.init_node('semantic_map_server')

    map_file = rospy.get_param('~map_file')

    semantic_map = cv2.imread(map_file)


if __name__ == '__main__':
    main()
