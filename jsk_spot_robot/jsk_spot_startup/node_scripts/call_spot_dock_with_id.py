#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import rospy
import threading
import copy
from std_srvs.srv import Trigger, TriggerResponse
from spot_msgs.srv import Dock
from spot_msgs.msg import DockObjArray

class SpotDockWithID(object):

    def __init__(self):

        self._docks = DockObjArray()
        self._lock_docks = threading.Lock()
        self._sub = rospy.Subscriber('/spot/world_object_docks', DockObjArray, self._cb_msg)
        self._server = rospy.Service('/spot/dock_fixed_id', Trigger, self._cb)
        self._client = rospy.ServiceProxy('/spot/dock', Dock)

    @property
    def docks(self):
        with self._lock_docks:
            return copy.deepcopy(self._docks)

    def _cb_msg(self, msg):
        with self._lock_docks:
            self._docks = msg

    def _cb(self, req):

        docks = self.docks
        if len(docks.docks) > 0:
            dock_id = docks.docks[0].dock_id
            resp = self._client(dock_id)
            rospy.loginfo("Call /spot/dock(dock_id={}) returns {}".format(dock_id, resp))
            return TriggerResponse(success=resp.success, message=resp.message)
        else:
            rospy.logerr("No dock found")
            return TriggerResponse(success=False, message="No dock found")

def main():
    rospy.init_node('spot_dock_with_id')
    end_effector_to_joy = SpotDockWithID()
    rospy.spin()


if __name__ == '__main__':
    main()
