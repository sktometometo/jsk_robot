from threading import Lock
from typing import Dict, List, Optional, Tuple

import rospy

from jsk_spot_behavior_manager.behavior_graph import (
    BehaviorGraph,
    BehaviorGraphBase,
    GraphEdge,
    GraphNode,
)
from jsk_spot_behavior_msgs.msg import Graph
from jsk_spot_behavior_msgs.srv import (
    CalcPath,
    CalcPathRequest,
    CalcPathResponse,
    SaveGraph,
    SaveGraphResponse,
)


class BehaviorGraphNode(object):
    def __init__(self):
        raw_edges = rospy.get_param("~map/edges", default=[])
        raw_nodes = rospy.get_param("~map/nodes", default={})
        self.graph = BehaviorGraph(raw_edges, raw_nodes)
        self.lock_for_graph = Lock()
        self.pub_graph = rospy.Publisher("/behavior_graph", Graph, queue_size=1)
        self.srv_calc_path = rospy.Service(
            "/behavior_graph_calc_path", CalcPath, self.handler_calc_path
        )
        self.srv_save_graph = rospy.Service(
            "/behavior_graph_save_graph", SaveGraph, self.handler_save_graph
        )

    def publish_graph(self):
        with self.lock_for_graph:
            graph_msg = Graph()
            graph_msg.nodes = [node.to_rosmsg() for node in self.graph.nodes.values()]
            graph_msg.edges = [edge.to_rosmsg() for edge in self.graph.edges.values()]
            self.pub_graph.publish(graph_msg)

    def handler_calc_path(self, req):
        with self.lock_for_graph:
            path = self.graph.calc_path(req.node_id_from, req.node_id_to)
        if path is None:
            return CalcPathResponse(success=False, message="No path found", path=[])
        else:
            return CalcPathResponse(success=True, message="Path found", path=path)

    def handler_save_graph(self, req):
        with self.lock_for_graph:
            try:
                self.graph.save_graph(req.filename)
                return SaveGraphResponse(success=True, message="Graph saved")
            except Exception as e:
                return SaveGraphResponse(success=False, message=str(e))

    def spin(self, publish_rate: float = 5.0):
        rate = rospy.Rate(publish_rate)
        while not rospy.is_shutdown():
            self.publish_graph()
            rate.sleep()


class BehaviorGraphClient(BehaviorGraphBase):
    def __init__(self, timeout: float = 10.0):
        super(BehaviorGraphClient, self).__init__()
        self.graph = BehaviorGraph()
        self.lock_for_graph = Lock()

        rospy.wait_for_message("/behavior_graph", Graph, timeout=timeout)
        rospy.wait_for_service("/behavior_graph_calc_path", timeout=timeout)

        self.sub_graph = rospy.Subscriber(
            "/behavior_graph", Graph, self._callback_graph
        )
        self.calc_path_client = rospy.ServiceProxy(
            "/behavior_graph_calc_path", CalcPath
        )

    def _callback_graph(self, msg):
        with self.lock_for_graph:
            self.graph.clear_graph()
            self.graph.load_graph(
                nodes=[GraphNode.from_rosmsg(node) for node in msg.nodes],
                edges=[GraphEdge.from_rosmsg(edge) for edge in msg.edges],
            )

    def save_graph(self, filename: str):
        with self.lock_for_graph:
            self.graph.save_graph(filename)

    def calc_path(self, node_id_from: str, node_id_to: str) -> Optional[str]:
        req = CalcPathRequest(node_id_from=node_id_from, node_id_to=node_id_to)
        res = self.calc_path_client(req)
        if res.success:
            return res.path
        return None

    def add_node(self, node: GraphNode):
        raise NotImplementedError

    def remove_node(self, node_id: str):
        raise NotImplementedError

    def add_edge(self, edge: GraphEdge):
        raise NotImplementedError

    def remove_edge(self, node_id_from: str, node_id_to: str):
        raise NotImplementedError

    def get_node(self, node_id) -> Optional[GraphNode]:
        with self.lock_for_graph:
            return self.graph.get_node(node_id)

    def get_edge(self, node_id_from: str, node_id_to: str) -> Optional[GraphEdge]:
        with self.lock_for_graph:
            return self.graph.get_edge(node_id_from, node_id_to)

    def list_nodes(self) -> List[GraphNode]:
        with self.lock_for_graph:
            return self.graph.list_nodes()
