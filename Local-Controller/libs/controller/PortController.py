"""
This module monitors the port status of the switch.
"""

from __future__ import print_function
import nnpy
import struct
from libs.core.Log import Log
from operator import ior
from libs.TableEntryManager import TableEntryManager, TableEntry
from libs.Configuration import Configuration
from libs.TopologyManager import TopologyManager
from libs.core.Event import Event
from collections import defaultdict
import proto.connection_pb2
from libs.core.Log import Log
import time
import datetime


class PortController:
    def __init__(self, controller=None, notification_socket=None):
        """
        Initialize PortController with base controller and notification_socket
        :param controller: BaseController which manages SwitchConnection
        :param notification_socket: notification_socket for nanomsg
        """
        # this may be removed later when registers are used
        self.table_manager = TableEntryManager(controller=controller, name="PortController")

        self.table_manager.init_table(table_name="ingress.port_c.port_status")

        # save port status received by nanomsg message, default up
        self.port_status = defaultdict(lambda: 1)

        self.sub = nnpy.Socket(nnpy.AF_SP, nnpy.SUB)
        self.sub.connect(notification_socket)
        self.sub.setsockopt(nnpy.SUB, nnpy.SUB_SUBSCRIBE, '')

        Event.on("topology_change", self.update)

    def monitor_messages(self):
        """
        Wait for port status message
        """
        Log.info("Start port monitor")
        while True:
            msg = self.sub.recv()
            msg_type = struct.unpack('4s', msg[:4])
            if msg_type[0] == 'PRT|':
                switch_id = struct.unpack('Q', msg[4:12])
                num_statuses = struct.unpack('I', msg[16:20])
                # wir betrachten immer nur den ersten Status
                port, status = struct.unpack('ii', msg[32:40])

                self.port_status[port] = status

                if status == 0:
                    # save port status time
                    # timestamp type, type 2 is port info

                    Log.log_to_file(round((time.time() * 1000) % 1000000), 2, "\r\n", file="logs/port_info.txt")
                    device = TopologyManager.get_device(Configuration.get('name'))
                    device.remove_port(port=port)
                    Event.trigger("topology_change")

                bool_stat = (status == 1)
                Event.trigger("port_msg_to_controller", info=proto.connection_pb2.PortInfo(switch=Configuration.get('name'), port=port, status=bool_stat))

    def write_port_entry(self, port_string=None):
        entry = TableEntry(action_name="ingress.port_c.set_port_status",
                           action_params={"livePorts": port_string})

        TableEntryManager.handle_table_entry(manager=self.table_manager,
                                             table_name="ingress.port_c.port_status",
                                             table_entry=entry)

    def update(self, **kwargs):
        device = TopologyManager.get_device(Configuration.get('name'))
        live_ports = filter(lambda x: self.port_status[x] == 1, device.get_device_to_port_mapping().values())

        port_ids = map(lambda x: int(2**(x-1)), live_ports)

        # this prevents an empty sequence and forces liveport bitstring of 0
        port_ids.append(0)
        port_string = reduce(ior, port_ids)

        self.write_port_entry(port_string=port_string)
