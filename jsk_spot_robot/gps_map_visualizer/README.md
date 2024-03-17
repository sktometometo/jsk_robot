# gps_map_visualizer

## Reference:

- https://www.ros.org/reps/rep-0105.html

> Map Conventions
>
> Map coordinate frames can either be referenced globally or to an application specific position. A example of an application specific positioning might be Mean Sea Level [3] according to EGM1996 [4] such that the z position in the map frame is equivalent to meters above sea level. Whatever the choice is the most important part is that the choice of reference position is clearly documented for users to avoid confusion.
> 
> When defining coordinate frames with respect to a global reference like the earth:
> The default should be to align the x-axis east, y-axis north, and the z-axis up at the origin of the coordinate frame.
> If there is no other reference the default position of the z-axis should be zero at the height of the WGS84 ellipsoid.
> In the case that there are application specific requirements for which the above cannot be satistfied as many as possible should still be met.
> 
> An example of an application which cannot meet the above requirements is a robot starting up without an external reference device such as a GPS, compass, nor altimeter. But if the robot still has an accelerometer it can intialize the map at its current location with the z axis upward.
> 
> If the robot has a compass heading as startup it can then also initialize x east, y north.
> 
> And if the robot has an altimeter estimate at startup it can initialize the height at MSL.
> 
> The conventions above are strongly recommended for unstructured environments.

