# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Dict, List, Tuple

import networkx as nx

import jsk_spot_behavior_msgs.msg


@dataclass
class GraphEdge:
    node_id_from: str
    node_id_to: str
    behavior_type: str
    cost: int
    properties: Dict

    @classmethod
    def from_config(cls, config: Dict):
        return cls(
            config["from"],
            config["to"],
            config["behavior_type"],
            int(config["cost"]) if "cost" in config else 1,
            config["args"] if "args" in config else {},
        )

    @classmethod
    def from_rosmsg(cls, msg: jsk_spot_behavior_msgs.msg.GraphEdge):
        try:
            args = eval(msg.args)
        except Exception:
            args = {}
        return cls(
            msg.node_id_from,
            msg.node_id_to,
            msg.behavior_type,
            msg.cost,
            args,
        )

    def to_config(self):
        return {
            "from": self.node_id_from,
            "to": self.node_id_to,
            "behavior_type": self.behavior_type,
            "cost": self.cost,
            "args": self.properties,
        }

    def to_rosmsg(self):
        return jsk_spot_behavior_msgs.msg.GraphEdge(
            node_id_from=self.node_id_from,
            node_id_to=self.node_id_to,
            behavior_type=self.behavior_type,
            cost=self.cost,
            args=str(self.properties),
        )


@dataclass
class GraphNode:
    node_id: str
    properties: Dict


class BehaviorGraph:
    # 現在の BehaviorGraph の仕様
    #   重み付きの有向グラフ
    #   あるノードからあるノードまでのエッジの数は 0 or 1

    def __init__(self, raw_edges: List[Dict] = [], raw_nodes: Dict[str, Dict] = {}):
        self.edges: Dict[Tuple[str, str], GraphEdge] = {}
        self.nodes: Dict[str, GraphNode] = {}
        self.network = nx.DiGraph()

        for raw_edge in raw_edges:
            self.add_edge(GraphEdge.from_config(raw_edge))

        for key, raw_node in raw_nodes.items():
            self.add_node(GraphNode(key, raw_node))

    def calc_path(self, node_id_from: str, node_id_to: str):
        try:
            node_id_list = nx.shortest_path(self.network, node_id_from, node_id_to)
        except nx.NetworkXNoPath:
            return None
        path = []
        for index in range(len(node_id_list) - 1):
            path.append(self.edges[node_id_list[index], node_id_list[index + 1]])
        return path

    def add_node(self, node: GraphNode):
        self.nodes[node.node_id] = node

    def remove_node(self, node_id: str):
        del self.nodes[node_id:str]

    def add_edge(self, edge: GraphEdge):
        self.edges[edge.node_id_from, edge.node_id_to] = edge
        self.network.add_edge(edge.node_id_from, edge.node_id_to, weight=edge.cost)

    def remove_edge(self, node_id_from: str, node_id_to: str):
        del self.edges[node_id_from, node_id_to]
        self.network.remove_edge(node_id_from, node_id_to)

    def get_node(self, node_id) -> GraphNode:
        return self.nodes[node_id]

    def get_edge(self, node_id_from: str, node_id_to: str) -> GraphEdge:
        return self.edges[node_id_from, node_id_to]
