#!/usr/bin/env python2

import argparse
import os
import sys
import threading
import time
import proto.connection_pb2
from libs.core.BaseController import BaseController
from libs.controller.MacController import MacController
from libs.controller.PortController import PortController
from libs.core.Log import Log
from libs.MessageInHandler import MessageInHandler
from libs.core.Event import Event
from libs.Configuration import Configuration
from libs.controller.TopologyController import TopologyController
from libs.TopologyManager import TopologyManager
from libs.GRPCServer import GRPCServer, LocalServer, GlobalConnection
from libs.controller.GroupController import GroupController


def init_switches(controller=None, topology_controller=None, group_controller=None):
    """
    Connect to switches and set forwarding pipeline
    :param controller: base controller who handles connections
    :param topology_controller: topology controller, who will send topology packets
    :return:
    """
    controller.connect_and_arbitrate(grpc_port=Configuration.get('grpc_port'), device_id=Configuration.get('device_id'))
    controller.set_forwarding_pipeline_config()

    Configuration.set('system_done', True)

    group_controller.add_flood_node()
    group_controller.init_flood_group()

    topology_controller.send_topology_packets()


def main():

    # without this line, no events would be fired, no topology discovered and no entries computed
    Event.activate()

    # base controller
    controller = BaseController(Configuration.get('p4info'), Configuration.get('bmv2_json'))

    # register event for new switch connections, this will add switches to device list
    Event.on('new_switch_connection', TopologyManager.add_device)

    # register events for static classes
    Event.on("packet_in", MessageInHandler.message_in)  # handles generic packet in
    Event.on("topology_to_controller", GlobalConnection.send_topology_packet)  # triggers the send routine to server
    Event.on("igmp_packet_to_controller", GlobalConnection.send_group_packet)  # triggers the send routine to server
    Event.on("port_msg_to_controller", GlobalConnection.send_port_info) # triggers the send routine to server


    topology = TopologyController(controller)

    # Create instances of sub controller
    mac = MacController(controller)
    port = PortController(controller=controller, notification_socket=Configuration.get('notification_socket'))
    group = GroupController(thrift_port=Configuration.get('thrift_port'), base=controller)

    # start connection procedure
    init_switches(controller=controller, topology_controller=topology, group_controller=group)

    # start grpc server for connection to main controller
    grpc_server = GRPCServer(listen_port=Configuration.get('listen_port'))

    # set controller in local server for table entry
    LocalServer.controller = controller

    # start grpc server
    grpc_server.start()

    # start port monitor
    threading.Thread(target=port.monitor_messages()).start()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')

    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='../P4-Implementation/build/sdn-bfr.p4info')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='../P4-Implementation/build/sdn-bfr.json')
    parser.add_argument('--grpc-port', help='GRPC port of switch',
                        type=int, action="store", required=True,
                        default=50051)
    parser.add_argument('--device-id', help='Device id of switch',
                        type=int, action="store", required=True,
                        default=1)
    parser.add_argument('--logfile', help='Name of the log file',
                        type=str, action="store", required=True,
                        default="log.txt")
    parser.add_argument('--loglevel', help='Log level',
                        type=int, action="store", required=False,
                        default=2)
    parser.add_argument('--listen-port', help='listen port',
                        type=int, action="store", required=True,
                        default=30001)
    parser.add_argument('--thrift-port', help='thrift port',
                        type=int, action="store", required=True,
                        default=9090)
    parser.add_argument('--notification-socket', help='Log level',
                        type=str, action="store", required=True,
                        default='ipc:///tmp/bmv2-0-notifications.ipc')

    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print("\np4info file not found: %s\nHave you run 'make'?" % args.p4info)
        parser.exit(1)

    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print("\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json)
        parser.exit(1)

    # write all command line arguments to configuration
    Configuration.init(args)

    Log.log_file = Configuration.get('logfile')
    Log.log_level = Configuration.get('loglevel')

    main()
