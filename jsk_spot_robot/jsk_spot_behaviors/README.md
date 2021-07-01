# jsk_spot_behaviors

These packages enable for Spot to execute locomotoion behaviors to reach a desired position.

In this framework, knowledge about positions and transtion behaviors between them are represented as a digraph like below.

Each node represents specified positions and each edge represents a behavior to transition between them.

![example_graph](https://user-images.githubusercontent.com/9410362/124147589-cc8ce700-dac9-11eb-930f-1c00c2a4777e.png)

A graph is defined by a yaml file ( e.g. [map.yaml in spot_behavior_manager_demo](https://github.com/sktometometo/jsk_robot/blob/feature/spot/add-spot-behaviors/jsk_spot_robot/jsk_spot_behaviors/spot_behavior_manager_demo/config/map.yaml) )
Please see nodes and edges format section below.

Knowledge representation and execution process of behaviors are separated from actual behavior implementation.
The iplementation of former is in spot_behavior_manager and spot_behavior_manager_demo, but actual behaviors like walk and elevator are in spot_basic_behaviors.
behavior_manager_demo node will dynamically load each behaviors defined in map.yaml so you can easilly add your behavior without editing these core implementation.
Please see spot_basic_behaviors package for behavior examples.

## map yaml file

TODO
