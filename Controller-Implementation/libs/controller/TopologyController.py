"""
This module implements an TopologyController
Sends topology packets, receives topology packets and build topology
"""

from scapy.all import *
from libs.core.Log import Log
from libs.core.CLI import CLI
from libs.core.Event import Event
from libs.core.Host import Host
from libs.TopologyManager import TopologyManager
from libs.TopologyManager import DeviceNotFound
from libs.Configuration import Configuration


class TopologyController:

    def __init__(self, controller):
        self._baseController = controller
        Event.on("topology_packet_in", self.handle_topology_answer)

    def handle_topology_answer(self, pkt=None):
        """
        Handle topology packet
        :param pkt: contains the topology packet
        :return:
        """

        # if the controller is not yet connected to all local controllers
        # don't handle topology packets
        if not Configuration.get('system_done'):
            return

        ip = pkt.ip.encode('utf-8')
        mac = pkt.mac.encode('utf-8')
        name = pkt.name.encode('utf-8')
        port = pkt.port
        switch = pkt.switch.encode('utf-8')

        if name.startswith('h'):  # it's a host
            TopologyManager.add_device(name=name, device=Host(name=name, ip=ip, mac=mac))
            TopologyManager.get_device(name=name).add_device_to_port(device=switch, port=1)

        Log.event("topology packet with identifier", name, "from switch", switch, "on port", port, "with ip", ip)

        if TopologyManager.get_device(name=switch).add_device_to_port(device=name, port=int(port)):
            Event.trigger("topology_change", src_device=switch, dst_device=name, port=int(port))
