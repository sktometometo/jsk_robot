# jsk_spot_behaviors

These packages enable for Spot to execute locomotoion behaviors to reach a desired position.

## Concept

In this framework, knowledge about positions and transtion behaviors between them are represented as a digraph like below.

Each node represents specified positions and each edge represents a behavior to transition between them.

![example_graph](https://user-images.githubusercontent.com/9410362/124147589-cc8ce700-dac9-11eb-930f-1c00c2a4777e.png)

A graph is defined by a yaml file ( e.g. [map.yaml in spot_behavior_manager_demo](https://github.com/sktometometo/jsk_robot/blob/feature/spot/add-spot-behaviors/jsk_spot_robot/jsk_spot_behaviors/spot_behavior_manager_demo/config/map.yaml) )
Please see nodes and edges format section below.

Knowledge representation and execution process of behaviors are separated from actual behavior implementation.
The iplementation of former is in spot_behavior_manager and spot_behavior_manager_demo, but actual behaviors like walk and elevator are in spot_basic_behaviors.
behavior_manager_demo node will dynamically load each behaviors defined in map.yaml so you can easilly add your behavior without editing these core implementation.
Please see spot_basic_behaviors package for behavior examples.

## How to use it

To run demo, please make Spot stand in front of the fiducial in 73B2 and run

```bash
roslaunch spot_behavior_manager_demo demo.launch
```

```bash
$ rostopic pub -1 /spot_behavior_manager_demo/lead_person/goal spot_behavior_manager_msgs/LeadPersonActionGoal "header:
  seq: 0
  stamp:
    secs: 0
    nsecs: 0
  frame_id: ''
goal_id:
  stamp:
    secs: 0
    nsecs: 0
  id: ''
goal:
  target_node_id: 'eng8_Piloti_Center'" 
```

Then Spot will go to the Piloti of building 8 by walk behavior and elevator behavior implemented in spot_basic_behaviors packages.

## map yaml file

TODO
