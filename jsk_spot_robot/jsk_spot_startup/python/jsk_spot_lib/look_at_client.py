import rospy
import actionlib
from typing import Union, List, Tuple, Optional

import numpy as np

from jsk_spot_startup.msg import LookAtAction, LookAtGoal
from geometry_msgs.msg import PointStamped, Point


class SpotLookAtClient:

    def __init__(self):

        self._ac = actionlib.SimpleActionClient(
                 "/spot_look_at",
                 LookAtAction,
                 )

    def look_at(self,
                target_point: Union[PointStamped, Point, List, np.ndarray],
                target_frame_id: str = "body",
                timeout: Optional[float] = None,
                ):
        """Look at

        Args:
            target_point: unit is meter
        """

        if isinstance(target_point, PointStamped):
            goal = LookAtGoal()
            goal.target_point = target_point
        elif isinstance(target_point, Point):
            goal = LookAtGoal()
            goal.target_point.header.frame_id = target_frame_id
            goal.target_point.point = target_point
        elif isinstance(target_point, List):
            goal = LookAtGoal()
            goal.target_point.header.frame_id = target_frame_id
            goal.target_point.point.x = target_point[0]
            goal.target_point.point.y = target_point[1]
            goal.target_point.point.z = target_point[2]
        elif isinstance(target_point, np.ndarray):
            goal = LookAtGoal()
            goal.target_point.header.frame_id = target_frame_id
            goal.target_point.point.x = target_point[0]
            goal.target_point.point.y = target_point[1]
            goal.target_point.point.z = target_point[2]
        else:
            raise ValueError("Unknoown target_point type")

        self._ac.send_goal(goal)

        if timeout is not None:
            self._ac.wait_for_result(timeout=timeout)
