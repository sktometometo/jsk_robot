#!/usr/bin/env python

import message_filters
import PyKDL
import rospy
import tf2_ros
from geometry_msgs.msg import Point, Transform, TransformStamped
from nav_msgs.msg import Odometry
from spot_msgs.msg import GraphNavGraph, GraphNavLocalization, NavigateToActionFeedback
from visualization_msgs.msg import Marker, MarkerArray


class RouteVisualizer:

    def __init__(self):

        self.frame_id_graph_reference = rospy.get_param(
            "~frame_id_graph_reference", "graph_reference"
        )
        self.pub_markers = rospy.Publisher(
            "/spot_graph_nav/remaining_route_markers", MarkerArray, queue_size=1
        )

        sub_graph = message_filters.Subscriber("/spot/graph_nav_graph", GraphNavGraph)
        sub_feedback = message_filters.Subscriber(
            "/spot/navigate_to/feedback", NavigateToActionFeedback
        )
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [sub_graph, sub_feedback], 10, 0.1, allow_headerless=True
        )
        self.ts.registerCallback(self.callback)

    def callback(
        self, msg_graph: GraphNavGraph, msg_feedback: NavigateToActionFeedback
    ):
        msg_marker_array = MarkerArray()
        frames = {
            anchor.id: anchor.seed_tform_waypoint
            for anchor in msg_graph.anchoring.anchors
        }
        stamp = rospy.Time.now()
        for index, edge_id in enumerate(msg_feedback.feedback.remaining_route.edge_id):
            marker = Marker()
            marker.header.frame_id = self.frame_id_graph_reference
            marker.header.stamp = stamp
            marker.ns = ""
            marker.id = index
            marker.points = [
                Point(
                    x=frames[edge_id.from_waypoint].p[0],
                    y=frames[edge_id.from_waypoint].p[1],
                    z=frames[edge_id.from_waypoint].p[2],
                ),
                Point(
                    x=frames[edge_id.to_waypoint].p[0],
                    y=frames[edge_id.to_waypoint].p[1],
                    z=frames[edge_id.to_waypoint].p[2],
                ),
            ]
            marker.type = Marker.ARROW
            marker.action = Marker.ADD
            marker.scale.x = 0.1
            marker.scale.y = 0.2
            marker.scale.z = 0.5
            marker.color.a = 1.0
            marker.color.r = 0.0
            marker.color.g = 1.0
            marker.color.b = 0.0
            msg_marker_array.markers.append(marker)
        self.pub_markers.publish(msg_marker_array)


if __name__ == "__main__":
    rospy.init_node("spot_remaining_route_visualizer")
    node = RouteVisualizer()
    rospy.spin()
