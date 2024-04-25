#!/usr/bin/env python

import message_filters
import rospy
import tf2_ros
from geometry_msgs.msg import Point, PoseStamped, Transform, TransformStamped
from nav_msgs.msg import Odometry, Path
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
        self.pub_path = rospy.Publisher(
            "/spot_graph_nav/remaining_route_path", Path, queue_size=1
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
        msg = Marker()
        msg.header.frame_id = self.frame_id_graph_reference
        msg.header.stamp = rospy.Time.now()
        msg.ns = ""
        msg.id = 0
        msg.action = Marker.DELETEALL
        msg.pose.orientation.w = 1.0
        self.pub_markers.publish(MarkerArray([msg]))

        msg_marker_array = MarkerArray()
        msg_path = Path()
        frames = {
            anchor.id: anchor.seed_tform_waypoint
            for anchor in msg_graph.anchoring.anchors
        }
        stamp = rospy.Time.now()
        msg_path.header.frame_id = self.frame_id_graph_reference
        msg_path.header.stamp = stamp
        for index, edge_id in enumerate(msg_feedback.feedback.remaining_route.edge_id):
            if index == 0:
                pose_stamped = PoseStamped()
                pose_stamped.header = msg_path.header
                pose_stamped.pose.position.x = frames[edge_id.from_waypoint].position.x
                pose_stamped.pose.position.y = frames[edge_id.from_waypoint].position.y
                pose_stamped.pose.position.z = frames[edge_id.from_waypoint].position.z
                pose_stamped.pose.orientation.x = frames[
                    edge_id.from_waypoint
                ].orientation.x
                pose_stamped.pose.orientation.y = frames[
                    edge_id.from_waypoint
                ].orientation.y
                pose_stamped.pose.orientation.z = frames[
                    edge_id.from_waypoint
                ].orientation.z
                pose_stamped.pose.orientation.w = frames[
                    edge_id.from_waypoint
                ].orientation.w
                msg_path.poses.append(pose_stamped)
            marker = Marker()
            marker.header.frame_id = self.frame_id_graph_reference
            marker.header.stamp = stamp
            marker.ns = ""
            marker.id = index
            marker.points = [
                Point(
                    x=frames[edge_id.from_waypoint].position.x,
                    y=frames[edge_id.from_waypoint].position.y,
                    z=frames[edge_id.from_waypoint].position.z,
                ),
                Point(
                    x=frames[edge_id.to_waypoint].position.x,
                    y=frames[edge_id.to_waypoint].position.y,
                    z=frames[edge_id.to_waypoint].position.z,
                ),
            ]
            marker.type = Marker.ARROW
            marker.action = Marker.ADD
            marker.pose.orientation.w = 1.0
            marker.scale.x = 0.1
            marker.scale.y = 0.2
            marker.scale.z = 0.5
            marker.color.a = 1.0
            marker.color.r = 0.0
            marker.color.g = 1.0
            marker.color.b = 0.0
            msg_marker_array.markers.append(marker)
            #
            pose_stamped = PoseStamped()
            pose_stamped.header = msg_path.header
            pose_stamped.pose.position.x = frames[edge_id.to_waypoint].position.x
            pose_stamped.pose.position.y = frames[edge_id.to_waypoint].position.y
            pose_stamped.pose.position.z = frames[edge_id.to_waypoint].position.z
            pose_stamped.pose.orientation.x = frames[edge_id.to_waypoint].orientation.x
            pose_stamped.pose.orientation.y = frames[edge_id.to_waypoint].orientation.y
            pose_stamped.pose.orientation.z = frames[edge_id.to_waypoint].orientation.z
            pose_stamped.pose.orientation.w = frames[edge_id.to_waypoint].orientation.w
            msg_path.poses.append(pose_stamped)
        self.pub_markers.publish(msg_marker_array)
        self.pub_path.publish(msg_path)


if __name__ == "__main__":
    rospy.init_node("spot_remaining_route_visualizer")
    node = RouteVisualizer()
    rospy.spin()
