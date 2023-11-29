#!/usr/bin/env python

import rospy
import actionlib
from sensor_msgs.msg import CompressedImage
from jsk_recognition_msgs.msg import VQATaskAction, VQATaskGoal

import cv2
import numpy as np

def cb(msg):
    # check if image is too dark
    im = cv2.imdecode(np.fromstring(msg.data, np.uint8), cv2.IMREAD_COLOR)[:, :, ::-1]
    # Calculate mean brightness as percentage (https://stackoverflow.com/questions/52505906/find-if-image-is-bright-or-dark)
    meanpercent = np.mean(im) * 100 / 255
    rospy.loginfo("mean brightness {}".format(meanpercent))
    if meanpercent < 35:
        rospy.logerr("Image is too dark")
        return
    goal = VQATaskGoal()
    goal.compressed_image = msg
    goal.questions = rospy.get_param('~questions', ['what does this image describe?'])
    # get vqa result
    ac.send_goal(goal)
    ac.wait_for_result()
    result = ac.get_result()
    rospy.loginfo('Q: {}'.format(goal.questions))
    for result in result.result.result:
        rospy.loginfo('- {}'.format(result.answer))

if __name__ == '__main__':
    try:
        rospy.init_node('store_image_description', anonymous=True)
        rospy.loginfo("wait for '/vqa/inference_server'")
        ac = actionlib.SimpleActionClient('/vqa/inference_server' , VQATaskAction)
        ac.wait_for_server()
        rospy.Subscriber('image', CompressedImage, cb, queue_size=1)
        rospy.loginfo("start subscribing {}".format(rospy.resolve_name('image')))
        rospy.spin()
    except rospy.ROSInterruptException:
        pass

