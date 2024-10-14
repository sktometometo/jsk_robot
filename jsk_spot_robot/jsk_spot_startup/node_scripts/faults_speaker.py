#!/usr/bin/env python

import rospy
from queue import Queue
import threading
from sound_play.libsoundplay import SoundClient
from spot_msgs.msg import SystemFaultState


class FaultsSpeaker:

    def __init__(self):

        self._severity_level = rospy.get_param('~severity_level', 2)
        self._ignore_messages = rospy.get_param('~ignore_messages', [])

        self.client = SoundClient()
        self.sub = rospy.Subscriber(
                '/spot/status/system_faults',
                SystemFaultState,
                self._cb
                )
        self.queue = []
        self.lock = threading.Lock()
        threading.Thread(target=self._speaking_thread).start()

    def _speaking_thread(self):
        rate = rospy.Rate(1)
        while not rospy.is_shutdown():
            rate.sleep()
            with self.lock:
                if len(self.queue) > 0:
                    message = self.queue.pop(0)
                    self.client.say(message, blocking=True)

    def _cb(self, msg):
        for fault in msg.faults:
            if fault.severity >= self._severity_level:
                message = "System error {}.".format(fault.name) + "{}".format(fault.error_message)
                if fault.error_message in self._ignore_messages:
                    rospy.logwarn_throttle_identical(10., "message: \"{}\" is ignored".format(message))
                    continue
                with self.lock:
                    if message not in self.queue:
                        self.queue.append(message)


if __name__ == '__main__':

    rospy.init_node('faults_speaker')
    node = FaultsSpeaker()
    rospy.spin()
