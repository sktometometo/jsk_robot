# -*- coding: utf-8 -*-

from dataclasses import dataclass
from token import OP
from typing import Dict, List, Optional, Tuple

import networkx as nx
import yaml

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
        properties = config.get("properties", config.get("args", {}))
        return cls(
            config["from"],
            config["to"],
            config["behavior_type"],
            int(config["cost"]) if "cost" in config else 1,
            properties,
        )

    @classmethod
    def from_rosmsg(cls, msg: jsk_spot_behavior_msgs.msg.GraphEdge):
        try:
            properties = eval(msg.properties)
        except Exception:
            properties = {}
        return cls(
            msg.node_id_from,
            msg.node_id_to,
            msg.behavior_type,
            msg.cost,
            properties,
        )

    def to_config(self):
        return {
            "from": self.node_id_from,
            "to": self.node_id_to,
            "behavior_type": self.behavior_type,
            "cost": self.cost,
            "properties": self.properties,
        }

    def to_rosmsg(self):
        return jsk_spot_behavior_msgs.msg.GraphEdge(
            node_id_from=self.node_id_from,
            node_id_to=self.node_id_to,
            behavior_type=self.behavior_type,
            cost=self.cost,
            properties=str(self.properties),
        )


@dataclass
class GraphNode:
    node_id: str
    properties: Dict

    @classmethod
    def from_rosmsg(cls, msg: jsk_spot_behavior_msgs.msg.GraphNode):
        try:
            properties = eval(msg.properties)
        except Exception:
            properties = {}
        return cls(msg.node_id, properties)

    def to_rosmsg(self):
        return jsk_spot_behavior_msgs.msg.GraphNode(
            node_id=self.node_id, properties=str(self.properties)
        )


class BehaviorGraphBase:
    def calc_path(self, node_id_from: str, node_id_to: str) -> Optional[str]:
        raise NotImplementedError

    def add_node(self, node: GraphNode):
        raise NotImplementedError

    def remove_node(self, node_id: str):
        raise NotImplementedError

    def add_edge(self, edge: GraphEdge):
        raise NotImplementedError

    def remove_edge(self, node_id_from: str, node_id_to: str):
        raise NotImplementedError

    def get_node(self, node_id) -> Optional[GraphNode]:
        raise NotImplementedError

    def get_edge(self, node_id_from: str, node_id_to: str) -> Optional[GraphEdge]:
        raise NotImplementedError

    def list_nodes(self) -> List[GraphNode]:
        raise NotImplementedError


class BehaviorGraph(BehaviorGraphBase):
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
            self.add_node(GraphNode(node_id=key, properties=raw_node))

    def clear_graph(self):
        self.edges = {}
        self.nodes = {}
        self.network = nx.DiGraph()

    def load_graph(self, nodes: List[GraphNode], edges: List[GraphEdge]):
        for node in nodes:
            self.add_node(node)
        for edge in edges:
            self.add_edge(edge)

    def save_graph(self, filename: str):
        data = {"nodes": {}, "edges": []}
        for node in self.nodes.values():
            data["nodes"][node.node_id] = node.properties
        for edge in self.edges.values():
            data["edges"].append(edge.to_config())
        with open(filename, "w") as f:
            yaml.dump(data, f)

    def calc_path(self, node_id_from: str, node_id_to: str):
        try:
            node_id_list = nx.shortest_path(self.network, node_id_from, node_id_to)
        except nx.NetworkXNoPath:
            return None
        path = []
        path.append(node_id_from)
        for index in range(len(node_id_list) - 1):
            path.append(
                self.edges[node_id_list[index], node_id_list[index + 1]].node_id_to
            )
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

    def get_node(self, node_id) -> Optional[GraphNode]:
        try:
            return self.nodes[node_id]
        except KeyError:
            return None

    def get_edge(self, node_id_from: str, node_id_to: str) -> Optional[GraphEdge]:
        try:
            return self.edges[node_id_from, node_id_to]
        except KeyError:
            return None

    def list_nodes(self) -> List[GraphNode]:
        return list(self.nodes.values())
