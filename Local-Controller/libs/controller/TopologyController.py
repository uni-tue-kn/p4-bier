"""
This module implements an TopologyController
Sends topology packets, receives topology packets and build topology
"""

from scapy.all import *
from libs.packet_header.TopologyPacket import TopologyDiscovery
from libs.core.Log import Log
from libs.core.Event import Event
from libs.core.Host import Host
from libs.TopologyManager import TopologyManager
from libs.Configuration import Configuration
import proto.connection_pb2
import threading


class TopologyController:

    def __init__(self, controller):
        self.__baseController = controller
        Event.on("topology_packet_in", self.handle_topology_answer)

    def send_topology_packets(self):
        """
        Send topology packet for given switch
        :return:
        """

        sw = Configuration.get('name')
        # get bfr id off switch for identification in top packet
        switch = TopologyManager.get_device(sw)
        pkt = Ether(src='00:00:00:00:00:00', dst='ff:ff:ff:ff:ff:ff')

        pkt = pkt / TopologyDiscovery(identifier=switch.get_bfr_id(0),
                                      port=1,
                                      ip=str(switch.get_ip()),
                                      mac=str(switch.get_mac()))

        self.__baseController.get_connection().send_packet_out(str(pkt))

        Log.debug("Send topology packet to switch", sw)

        # send topology packet periodically
        threading.Timer(2, self.send_topology_packets).start()

    def handle_topology_answer(self, *args, **kwargs):
        """
        Handle topology packet
        :param args: contains the topology packet
        :return:
        """
        packet = kwargs.get('packet')
        switch = kwargs.get('switch')

        pkt = packet.payload

        if str(pkt.payload) != 'host':
            name = "s" + str(pkt.identifier)
            TopologyManager.add_device(name=name, device=Host(name=name, ip=pkt.ip, mac=pkt.mac))
        else:  # its a host
            name = "h" + str(pkt.identifier)
            TopologyManager.add_device(name=name, device=Host(name=name, ip=pkt.ip, mac=pkt.mac))

        if TopologyManager.get_device(name=switch).add_device_to_port(device=name, port=int(pkt.port)):
            Event.trigger("topology_change", src_device=switch, dst_device=name, port=int(pkt.port))

        topology_packet = proto.connection_pb2.TopologyPacket(ip=pkt.ip, mac=pkt.mac, port=pkt.port, name=name, switch=Configuration.get('name'))

        Event.trigger("topology_to_controller", pkt=topology_packet)
