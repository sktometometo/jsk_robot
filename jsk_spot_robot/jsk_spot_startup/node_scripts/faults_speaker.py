#!/usr/bin/env python

import rospy
from sound_play.libsoundplay import SoundClient
from spot_msgs.msg import SystemFaultState


class FaultsSpeaker:

    def __init__(self):

        self._severity_level = rospy.get_param('~severity_level', 2)

        self.client = SoundClient()
        self.sub = rospy.Subscriber(
                '/spot/status/system_faults',
                SystemFaultState,
                self._cb
                )

    def _cb(self, msg):
        for fault in msg.faults:
            if fault.severity_level >= self._severity_level:
                self.client.say(
                        "I have got an error {}.".format(fault.name) \
                                + "{}".format(fault.error_message),
                        blocking=True
                        )


if __name__ == '__main__':

    rospy.init_node('faults_speaker')
    node = FaultsSpeaker()
    rospy.spin()
