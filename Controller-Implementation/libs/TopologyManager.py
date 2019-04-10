from libs.core.Log import Log
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import networkx as nx
import numpy as np
from sklearn.cluster import spectral_clustering
from prettytable import PrettyTable
from libs.Topology import Topology, LinkNotFound
from libs.Exceptions import DeviceNotFound, DomainNotFound, NextHopNotFound
from libs.core.Event import Event
from libs.Configuration import Configuration


class TopologyManager:

    topology = {'total': 0, 'devices': [], 'domains': []}

    @staticmethod
    def react_to_port_change(message=None):
        """
        This method react to the port down event
        """

        if message.status == 1:
            return

        device = TopologyManager.get_device(name=message.switch)

        if device.get_neighbor_by_port(port=message.port) is None:
            return

        neighbor = TopologyManager.get_device(name=device.get_neighbor_by_port(port=message.port))

        device.remove_port(port=message.port)
        neighbor.remove_port(port=neighbor.get_device_to_port(device.get_name()))
        Event.trigger("topology_change", port_update=True, sleep=Configuration.get("delay"))


    @staticmethod
    def exists_device(name=None):
        """
        Checks whether a given device exists
        :param name: name of device
        :return: boolean
        """
        for dev in TopologyManager.topology['devices']:
            if dev['name'] == name:
                return True

        return False

    @staticmethod
    def add_device(name=None, domain=0, device=None):
        """
        Adds an device to the device list
        :param name: name of the device
        :param domain: corresponding domain, default-domain 0
        :param device: device, e.g. Host or Switch object
        :return: void
        """
        if not TopologyManager.exists_device(name):
            TopologyManager.topology['devices'].append({'name': name, 'domain': [domain], 'device': device})

        TopologyManager.topology['total'] = len(TopologyManager.topology['devices'])

    @staticmethod
    def get_device(name=None):
        """
        Get device by name
        :param name: name of the device
        :return: device
        """
        for dev in TopologyManager.topology['devices']:
            if dev['name'] == name:
                return dev['device']

        raise DeviceNotFound(name)

    @staticmethod
    def get_device_by_ip(ip=None):
        """
        Return device with given ip
        :param ip: ip of device
        :return:
        """
        for dev in TopologyManager.topology['devices']:
            device = dev['device']

            if device.get_ip() == ip:
                return device

        raise DeviceNotFound(ip)

    @staticmethod
    def get_devices():
        """
        Return all devices
        :return: all devices
        """
        return TopologyManager.topology['devices']

    @staticmethod
    def get_domain_for_device(name=None):
        """
        Get domains in which given device is in
        :param name: name of device
        :return: domain list
        """
        for dev in TopologyManager.topology['devices']:
            if dev['name'] == name:
                return dev['domain']

        raise DeviceNotFound(name)

    @staticmethod
    def get_domain(domain_id=1):
        """
        Get domain with given domain_id
        :param domain_id: domain_id
        :return:
        """
        for domain in TopologyManager.topology['domains']:
            if domain['id'] == domain_id:
                return domain

        raise DomainNotFound(domain_id)

    @staticmethod
    def get_domains():
        """
        Return all domains
        :return: domains
        """
        return TopologyManager.topology['domains']

    @staticmethod
    def get_tunnel_node(domain=1):
        """
        Get tunnel node for given domain
        :param domain: domain identifier
        :return: tunnel node name
        """
        topology = TopologyManager.get_domain(domain)

        return topology['tunnel_node']

    @staticmethod
    def get_next_hop(start_node=None, destination_node=None, domain_id=0):
        """
        Get the next hop from start_node to destination_node on given domain
        :param start_node: node where path starts
        :param destination_node: node where path ends
        :param domain_id: domain in which the path should be used
        :return:
        """
        paths = TopologyManager.get_topology(id=domain_id).get_shortest_paths()

        if not paths.get(start_node, False):
            raise NextHopNotFound(start_node, destination_node, domain_id)

        if not paths.get(start_node).get(destination_node, False):
            raise NextHopNotFound(start_node, destination_node, domain_id)

        if len(paths.get(start_node).get(destination_node)) < 2:
            raise NextHopNotFound(start_node, destination_node, domain_id)

        return TopologyManager.get_device(paths.get(start_node).get(destination_node)[1])

    @staticmethod
    def get_topology(id=0):
        """
        Returns the domain with the given id
        :param id: id of domain
        :return: domain
        """
        for domain in TopologyManager.topology['domains']:
            if domain['id'] == id:
                return domain['topology']

        raise DomainNotFound(id)

    @staticmethod
    def link_to_number(link_name=None, domain=0):
        """
        Get the link number of the link_name inside the domain
        :param link_name: name of the link
        :param domain: domain id
        """
        top = TopologyManager.get_topology(id=domain)
        link_number = top.links.get(link_name, None)

        if link_number is None:
            raise LinkNotFound(link_name, domain)

        number_of_switches = len(top.get_switch_graph().nodes())

        return link_number + number_of_switches

    @staticmethod
    def get_device_by_domain_and_id(domain=0, id=0):
        for device in TopologyManager.topology['devices']:
            if TopologyManager.get_device(device['name']).get_bfr_id(domain) == id:
                return device['name']

        raise DeviceNotFound(id)

    @staticmethod
    def add_device_to_domain(device_name=None, domain_id=None):
        """
        Adds the given device to the specified domain
        :param device_name: device name
        :param domain_id: domain where it should be added
        :return:
        """
        for device in TopologyManager.topology['devices']:
            if device['name'] == device_name:
                if domain_id not in device['domain']:
                    device['domain'].append(domain_id)

                return

    @staticmethod
    def set_topology(domain_id=0, topology=None):
        """
        Set topology for domain with domain_id
        :param domain_id: domain id
        :param topology: topology which will be set
        :return:
        """
        for domain in TopologyManager.topology['domains']:
            if domain['id'] == domain_id:
                domain['topology'] = topology
                return

        TopologyManager.topology['domains'].append({'id': domain_id, 'topology': topology, 'tunnel_node': None})

    @staticmethod
    def build_domain(domain=0, **kwargs):
        """
        Generate topology for given domain
        :param domain: domain id
        :return:
        """
        top = Topology(domain)

        for device in TopologyManager.topology['devices']:
            if domain not in device['domain']:
                continue

            mapping = device['device'].get_device_to_port_mapping().keys()

            top.add_node(device['name'])

            # add edges inside domain
            for neighbor in mapping:
                # neighbor is in same domain, so add edge
                if domain in TopologyManager.get_domain_for_device(neighbor):
                    top.add_edge(device['name'], neighbor)

        TopologyManager.set_topology(domain_id=domain, topology=top)

    @staticmethod
    def get_paths(domain_id=0):
        """
        Return paths for given domain
        :param domain_id: domain-identifier
        :return:
        """
        TopologyManager.build_domain(domain_id)

        return TopologyManager.get_topology(domain_id).get_shortest_paths()

    @staticmethod
    def describe():
        """
        Describe topology
        """
        TopologyManager.overview()
        Log.echo(" ")
        TopologyManager.describe_nodes()
        Log.echo(" ")
        TopologyManager.describe_hosts()
        Log.echo(" ")

    @staticmethod
    def overview():
        data = PrettyTable()

        data.field_names = ["Domain id", "Nodes", "Tunnel Node"]

        for domain in TopologyManager.topology['domains']:
            data.add_row([domain['id'], domain['topology'].get_nodes(), domain['tunnel_node']])

        Log.echo(data)

    @staticmethod
    def describe_nodes():
        data = PrettyTable()

        data.field_names = ["Node", "Domains", "IP", "MAC", "BFR-ID per domain"]

        for device in TopologyManager.topology['devices']:
            if device['device'].get_type() == "Switch":
                data.add_row([device['name'], device['domain'], device['device'].get_ip(), device['device'].get_mac(),
                              device['device'].get_bfr_mapping()])

        Log.echo(data)

    @staticmethod
    def describe_hosts():
        data = PrettyTable()

        data.field_names = ["Host", "IP", "MAC", "Connected to"]

        for device in TopologyManager.topology['devices']:
            if device['device'].get_type() == "Host":
                connections = TopologyManager.get_device(device['name']).get_device_to_port_mapping().keys()
                data.add_row([device['name'], device['device'].get_ip(), device['device'].get_mac(), connections])

        Log.echo(data)

    @staticmethod
    def plot():
        """
        Plot topology including sub-domains
        :return:
        """

        if len(TopologyManager.topology['domains']) < 1:
            Log.error("Not yet clustered")
            return

        number_of_domains = len(TopologyManager.topology['domains']) - 1

        if number_of_domains == 0:
            number_of_domains = 1

        # plot whole topology
        graph = TopologyManager.get_topology(0).get_graph()

        gs = gridspec.GridSpec(2, number_of_domains)

        plt.figure("Topology")
        ax = plt.subplot(gs[0, :])
        plt.title("Domain: 0")

        pos = nx.kamada_kawai_layout(graph)

        nx.draw(graph, pos, node_color="#e74c3c", font_size=10, with_labels=True, ax=ax)


        plt.show()
