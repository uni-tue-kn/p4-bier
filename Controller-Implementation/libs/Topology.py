from random import choice
import networkx as nx
from libs.Exceptions import LinkNotFound
from libs.Configuration import Configuration


class Topology:
    def __init__(self, identifier=None):
        """
        Init (sub-)topology with identifier
        :param identifier: sub-domain identifier, int
        """
        self._identifier = identifier
        self._graph = nx.DiGraph()
        self._switch_graph = nx.DiGraph()
        self._lastId = 0
        self._linkNumber = 1
        self.links = {}

    def add_edge(self, n1, n2):
        """
        Add adge between nodes n1 and n2
        :param n1: first node
        :param n2: second node
        :return:
        """
        if not self._graph.has_edge(n1, n2):
            self._graph.add_edge(n1, n2)

            if not (n1.startswith('h') or n2.startswith('h')):
                self._switch_graph.add_edge(n1, n2)
                self.links[str(n1) + "-" + str(n2)] = self._linkNumber
                self._linkNumber += 1

    def add_node(self, n):
        """
        Add node to graph
        :param n:
        :return:
        """
        self._graph.add_node(n)

        # if this node is a switch, add it to the switch graph
        for switch in Configuration.get("switches"):
            if switch["name"] == n:
                self._switch_graph.add_node(n)
                return

    def get_identifier(self):
        """
        Returns the domain identifier
        :return: domain identifier, int
        """
        return self._identifier

    def get_graph(self):
        """
        Returns the nx graph
        :return: nx.Graph
        """
        return self._graph

    def get_switch_graph(self):
        """
        Return the graph containing only switches
        :return:
        """
        return self._switch_graph

    def get_shortest_paths(self):
        """
        Get shortest paths for given topology
        :return: shorteste paths, dict
        """
        return dict(nx.all_pairs_shortest_path(self._graph))

    def get_shortest_path(self, start=None, destination=None):
        """
        Get shortest path from start to destination
        :return: list of path including start and destination
        """
        return nx.shortest_path(self._graph, source=start, target=destination)

    def get_tunnel_node(self):
        """
        Get tunnel node
        Choice is random
        :return:
        """
        return choice(list(self._graph.nodes()))

    def get_incoming_adjacencies(self, node=None):
        """
        Returns a list of incoming adjacencies for the given node
        :param node: Node where list of incoming adjacencies should be returned
        :return: list of incoming adjacencies
        """
        adjacencies = []
        for edge in self._switch_graph.edges:
            if edge[1] == node:
                adjacencies.append(str(edge[0]) + "-" + str(edge[1]))
        return adjacencies


    def get_nodes(self):
        return list(self._graph.nodes())

    def get_last_id(self):
        return self._lastId

    def increment_last_id(self):
        self._lastId += 1

    def reset_last_id(self):
        self._lastId = 0
