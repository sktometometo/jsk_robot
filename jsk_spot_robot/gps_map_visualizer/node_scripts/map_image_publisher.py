#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from typing import Optional, Tuple

import numpy as np
import rospy
import staticmap
import tf2_ros
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import MapMetaData, OccupancyGrid

from gps_map_visualizer import (
    calc_geographic_coords_from_cartesian_difference,
    calc_meters_per_pixel,
)


class MapImagePublisher:

    def __init__(self):

        self.anchor_frame = rospy.get_param("~anchor_world_frame")
        self.anchor_latitude = rospy.get_param("~anchor_latitude")
        self.anchor_longitude = rospy.get_param("~anchor_longitude")

        self.target_frame = rospy.get_param("~target_frame")
        self.map_image_frame = rospy.get_param("~map_image_frame", "map_image_frame")

        self.map_size = rospy.get_param("~map_size", 1000)  # pixel
        self.zoom_level = rospy.get_param("~zoom_level", 16)  # level

        self.map_type = rospy.get_param("~map_type", "osm")  # 'osm' or 'gsi_jp'

        self.transform_anchor_to_static = TransformStamped()
        self.transform_anchor_to_static.header.frame_id = self.anchor_frame
        self.transform_anchor_to_static.child_frame_id = self.map_image_frame
        self.transform_anchor_to_static.transform.rotation.w = 1.0

        if self.map_type == "osm":
            self.map_image = staticmap.StaticMap(
                self.map_size,
                self.map_size,
                url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            )
        elif self.map_type == "gsi_jp":
            self.map_image = staticmap.StaticMap(
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
            rate.sleep()
            transform = self.get_transform_from_anchor_to_map_image_frame()
            if transform is None:
                continue
            self.publish_tf(transform)
            #
            center_longitude, center_latitude = (
                self.get_geographic_coords_from_transform(
                    transform,
                    self.anchor_longitude,
                    self.anchor_latitude,
                )
            )

            map_meta_data, occ_grid = self.render_map_to_rosmsg(
                center_longitude, center_latitude, self.zoom_level, self.map_size
            )
            self.publish_map(map_meta_data, occ_grid)

    def get_geographic_coords_from_transform(
        self,
        transform_from_anchor_to_map_image: TransformStamped,
        anchor_longitude: float,
        anchor_latitude: float,
    ) -> Tuple[float, float]:
        """Calculate the longitude and latitude from the reference point and the difference in meters

        Args:
            transform_from_anchor_to_map_image (TransformStamped): transform from anchor to map image
            anchor_longitude (float): longitude of the reference point
            anchor_latitude (float): latitude of the reference point

        Returns:
            Tuple[float, float]: (longitude, latitude)

        """
        diff_x_meter = transform_from_anchor_to_map_image.transform.translation.x
        diff_y_meter = transform_from_anchor_to_map_image.transform.translation.y
        return calc_geographic_coords_from_cartesian_difference(
            reference_longitude=anchor_longitude,
            reference_latitude=anchor_latitude,
            diff_x=diff_x_meter,
            diff_y=diff_y_meter,
        )

    def get_transform_from_anchor_to_map_image_frame(
        self,
    ) -> Optional[TransformStamped]:

        try:
            transform_from_anchor_to_target = self.tf_buffer.lookup_transform(
                self.anchor_frame,
                self.target_frame,
                rospy.Time(0),
            )
        except (
            tf2_ros.LookupException,
            tf2_ros.ConnectivityException,
            tf2_ros.ExtrapolationException,
        ):
            rospy.logerr("Failed to lookup transform from anchor to target")
            return None
        transform = TransformStamped()
        transform.header.frame_id = self.anchor_frame
        transform.child_frame_id = self.map_image_frame
        transform.transform.rotation.w = 1.0
        transform.transform.translation = (
            transform_from_anchor_to_target.transform.translation
        )

        return transform

    def render_map_to_rosmsg(
        self,
        center_longitude: float,
        center_latitude: float,
        zoom_level: int,
        map_size: int = 1000,
    ) -> Tuple[MapMetaData, OccupancyGrid]:
        map_resolution = calc_meters_per_pixel(center_latitude, zoom_level)
        rospy.logdebug("map resolution is {}".format(map_resolution))
        rospy.logdebug(
            "rendering map with parameter zoom : {}, center: {}".format(
                zoom_level, (center_longitude, center_latitude)
            )
        )
        try:
            image = self.map_image.render(
                zoom=zoom_level,
                center=(center_longitude, center_latitude),
            )
        except RuntimeError:
            rospy.logerr("Failed to download map images")
            msg_map_meta_data = MapMetaData()
            msg_occupancy_grid = OccupancyGrid()
            return msg_map_meta_data, msg_occupancy_grid

        msg_map_meta_data = MapMetaData()
        msg_map_meta_data.map_load_time = rospy.Time.now()
        msg_map_meta_data.resolution = map_resolution
        msg_map_meta_data.width = map_size
        msg_map_meta_data.height = map_size
        msg_map_meta_data.origin.position.x = -map_size * map_resolution / 2
        msg_map_meta_data.origin.position.y = map_size * map_resolution / 2
        msg_map_meta_data.origin.position.z = 0
        msg_map_meta_data.origin.orientation.x = 1.0
        msg_map_meta_data.origin.orientation.y = 0.0
        msg_map_meta_data.origin.orientation.z = 0.0
        msg_map_meta_data.origin.orientation.w = 0.0

        msg_occupancy_grid = OccupancyGrid()
        msg_occupancy_grid.header.frame_id = self.map_image_frame
        msg_occupancy_grid.header.stamp = rospy.Time.now()
        msg_occupancy_grid.info = msg_map_meta_data

        image_array = np.array(image.convert("L")) / 2
        msg_occupancy_grid.data = image_array.astype(np.uint8).flatten().tolist()
        return msg_map_meta_data, msg_occupancy_grid

    def publish_map(
        self, msg_map_meta_data: MapMetaData, msg_occupancy_grid: OccupancyGrid
    ):
        self.pub_map_meta_data.publish(msg_map_meta_data)
        self.pub_occupancy_grid.publish(msg_occupancy_grid)

    def publish_tf(self, transform: TransformStamped):
        self.tf_br.sendTransform(transform)


if __name__ == "__main__":
    rospy.init_node("map_image_publisher")
    node = MapImagePublisher()
    node.spin()
