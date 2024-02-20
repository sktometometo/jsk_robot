import rospy

from jsk_spot_behavior_manager.behavior_graph import BehaviorGraph
from jsk_spot_behavior_msgs.msg import Graph, GraphEdge, GraphNode


class BehaviorGraphNode(object):
    def __init__(self):
        raw_edges = rospy.get_param("~map/edges", default=[])
        raw_nodes = rospy.get_param("~map/nodes", default={})
        self.graph = BehaviorGraph(raw_edges, raw_nodes)

        self.pub_graph = rospy.Publisher("~graph", Graph, queue_size=1)

        self.srv_add_node = rospy.Service()

    def handler_add_node(self, req):
        pass

    def publish_graph(self):
        graph_msg = Graph()
        graph_msg.nodes = [node for node in self.graph.nodes.values()]
        graph_msg.edges = [edge for edge in self.graph.edges.values()]
        self.pub_graph.publish(graph_msg)
