#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import numpy as np
import rospy
import staticmap
import tf2_ros
from dynamic_reconfigure.server import Server
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import MapMetaData, OccupancyGrid

from gps_map_visualizer import (calc_meters_per_pixel,
                                calc_transform_from_lon_lat)


class StaticMapPublisher:

    def __init__(self):

        self.center_latitude = None
        self.center_longitude = None
        self.zoom_level = None

        self.anchor_frame = rospy.get_param("~anchor_frame")
        self.anchor_latitude = rospy.get_param("~anchor_latitude")
        self.anchor_longitude = rospy.get_param("~anchor_longitude")
        self.anchor_direction = rospy.get_param("~anchor_direction")

        self.target_frame = rospy.get_param("~target_frame")

        self.map_size = rospy.get_param("~map_size", 1000)
        self.map_type = rospy.get_param("~map_type", "osm")  # 'osm' or 'gsi_jp'
        self.static_map_frame = rospy.get_param("~static_map_frame", "static_map_frame")

        self.transform_anchor_to_static = TransformStamped()
        self.transform_anchor_to_static.header.frame_id = self.anchor_frame
        self.transform_anchor_to_static.child_frame_id = self.static_map_frame
        self.transform_anchor_to_static.transform.rotation.w = 1.0

        if self.map_type == "osm":
            self.static_map = staticmap.StaticMap(
                self.map_size,
                self.map_size,
                url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            )
        elif self.map_type == "gsi_jp":
            self.static_map = staticmap.StaticMap(
                self.map_size,
                self.map_size,
                url_template="https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png",
            )

        self.msg_map_meta_data = MapMetaData()
        self.msg_occupancy_grid = OccupancyGrid()

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        self.tf_br = tf2_ros.TransformBroadcaster()

        self.pub_map_meta_data = rospy.Publisher(
            "/map_meta_data", MapMetaData, queue_size=1, latch=True
        )
        self.pub_occupancy_grid = rospy.Publisher(
            "/map", OccupancyGrid, queue_size=1, latch=True
        )

        rospy.logwarn("Initialized")

    def spin(self):
        rate = rospy.Rate(0.1)
        while not rospy.is_shutdown():
            transform = self.calc_transform()
            self.publish_tf(transform)
            rate.sleep()

    def calc_transform_from_anchor_to_static_map_frame(self) -> TransformStamped:

        try:
            transform_from_anchor_to_target = self.tf_buffer.lookup_transform(
                self.target_frame,
                self.anchor_frame,
                rospy.Time(0),
            )
        except (
            tf2_ros.LookupException,
            tf2_ros.ConnectivityException,
            tf2_ros.ExtrapolationException,
        ):
            rospy.logerr("Failed to lookup transform from anchor to target")
            return
        
        transform = TransformStamped()
        transform.header.frame_id = self.anchor_frame
        transform.child_frame_id = self.static_map_frame
        transform.transform.rotation.w = 1.0
        transform.transform.translation = transform_from_anchor_to_target.transform.translation

        return transform

    def render_map(self, center_longitude: float, center_latitude: float, zoom_level: int, map_size: int = 1000):
        map_resolution = calc_meters_per_pixel(center_latitude, zoom_level)
        rospy.logdebug("map resolution is {}".format(map_resolution))
        rospy.logdebug(
            "rendering map with parameter zoom : {}, center: {}".format(
                self.zoom_level, (center_longitude, center_latitude)
            )
        )
        try:
            image = self.static_map.render(
                zoom=zoom_level,
                center=(center_longitude, center_latitude),
            )
        except RuntimeError:
            rospy.logerr("Failed to download map images")
            self.msg_map_meta_data = MapMetaData()
            self.msg_occupancy_grid = OccupancyGrid()
            return

        self.msg_map_meta_data = MapMetaData()
        self.msg_map_meta_data.map_load_time = rospy.Time.now()
        self.msg_map_meta_data.resolution = map_resolution
        self.msg_map_meta_data.width = map_size
        self.msg_map_meta_data.height = map_size
        self.msg_map_meta_data.origin.position.x = -map_size * map_resolution / 2
        self.msg_map_meta_data.origin.position.y = map_size * map_resolution / 2
        self.msg_map_meta_data.origin.position.z = 0
        self.msg_map_meta_data.origin.orientation.x = 1.0
        self.msg_map_meta_data.origin.orientation.y = 0.0
        self.msg_map_meta_data.origin.orientation.z = 0.0
        self.msg_map_meta_data.origin.orientation.w = 0.0

        self.msg_occupancy_grid = OccupancyGrid()
        self.msg_occupancy_grid.header.frame_id = self.static_map_frame
        self.msg_occupancy_grid.header.stamp = rospy.Time.now()
        self.msg_occupancy_grid.info = self.msg_map_meta_data

        image_array = np.array(image.convert("L")) / 2
        self.msg_occupancy_grid.data = image_array.astype(np.uint8).flatten().tolist()

    def publish_map(self):
        self.pub_map_meta_data.publish(self.msg_map_meta_data)
        self.pub_occupancy_grid.publish(self.msg_occupancy_grid)

    def publish_tf(self, transform: TransformStamped):
        self.tf_br.sendTransform(transform)


if __name__ == "__main__":
    rospy.init_node("static_map_publisher")
    node = StaticMapPublisher()
    node.spin()
