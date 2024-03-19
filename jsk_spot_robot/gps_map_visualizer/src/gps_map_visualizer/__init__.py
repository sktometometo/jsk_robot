# -*- encoding: utf-8 -*-
import math
from typing import Tuple

from geopy import distance
from geopy.point import Point


# See https://wiki.openstreetmap.org/wiki/Zoom_levels
def calc_meters_per_pixel(latitude, zoom_level, earth_radius=6378137.000):
    earth_circumference = 2 * math.pi * earth_radius
    return (
        earth_circumference * math.cos(math.radians(latitude)) / 2 ** (zoom_level + 8)
    )


def calc_transform_from_geographic_coords(
    reference_longitude: float,
    reference_latitude: float,
    target_longitude: float,
    target_latitude: float,
) -> Tuple[float, float]:
    """
    Calculate the difference in meters from the reference point to the target point

    Args:
        reference_longitude (float): longitude of the reference point
        reference_latitude (float): latitude of the reference point
        target_longitude (float): longitude of the target point
        target_latitude (float): latitude of the target point

    Returns:
        Tuple[float, float]: (diff_x, diff_y)
            diff_x: difference in meters in x direction (East is positive)
            diff_y: difference in meters in y direction (North is positive)
    """
    distance_x_meter = distance.great_circle(
        Point(longitude=reference_longitude, latitude=reference_latitude),
        Point(longitude=target_longitude, latitude=reference_latitude),
    ).meters
    distance_y_meter = distance.great_circle(
        Point(longitude=reference_longitude, latitude=reference_latitude),
        Point(longitude=reference_longitude, latitude=target_latitude),
    ).meters
    diff_x_meter = (
        distance_x_meter
        if target_longitude >= reference_longitude
        else -distance_x_meter
    )
    diff_y_meter = (
        distance_y_meter if target_latitude >= reference_latitude else -distance_y_meter
    )
    return diff_x_meter, diff_y_meter


def calc_geographic_coords_from_cartesian_difference(
    reference_longitude: float, reference_latitude: float, diff_x: float, diff_y: float
) -> Tuple[float, float]:
    """
    Calculate the longitude and latitude from the reference point and the difference in meters

    Args:
        reference_longitude (float): longitude of the reference point
        reference_latitude (float): latitude of the reference point
        diff_x (float): difference in meters in x direction (East is positive)
        diff_y (float): difference in meters in y direction (North is positive)

    Returns:
        Tuple[float, float]: (longitude, latitude)
    """
    initial_point = Point(longitude=reference_longitude, latitude=reference_latitude)
    d = distance.distance(meters=math.sqrt(diff_x**2 + diff_y**2))
    bearing = math.degrees(math.atan2(diff_x, diff_y))
    destination = d.destination(initial_point, bearing=bearing)
    return destination.longitude, destination.latitude
