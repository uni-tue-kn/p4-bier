#!/usr/bin/env python2

import argparse
import os
import threading
from libs.core.BaseController import BaseController
from libs.controller.IPv4Controller import IPv4Controller
from libs.controller.TunnelController import *
from libs.GroupManager import GroupManager
from libs.core.CLI import CLI
from libs.core.Log import Log
from libs.core.Event import Event
from libs.TopologyManager import TopologyManager
from libs.Configuration import Configuration
from libs.controller.TopologyController import TopologyController
from libs.controller.BierController import BierController
from libs.core.GRPCServer import GRPCServer


def connect_to_switches(controller=None):
    """
    Connect to switches and set forwarding pipeline
    :param controller: base controller who handles connections
    :param topology_controller: topology controller, who will send topology packets
    :return:
    """
    controller.connect()
    Configuration.set('system_done', True)

def load_static_rules(*args):
    Log.async_info("Write static rules...")

    for arg in args:
        arg.load_static_rules()

def main():
    Configuration.set('system_done', False)

    # without this line, no events would be fired, no topology discovered and no entries computed
    Event.activate()

    # register event for new switch connections, this will add switches to device list
    Event.on('new_switch_connection', TopologyManager.add_device)

    # base controller
    controller = BaseController()

    # register events for static classes
    Event.on("igmp_packet_in", GroupManager.handle_packet_in)  # handles (un-)sub requests
    Event.on("port_message", TopologyManager.react_to_port_change)
    Event.on("topology_change", TopologyManager.build_domain)

    topology = TopologyController(controller)

    # Create instances of sub controller for CLI
    ipv4 = IPv4Controller(controller)
    bier = BierController(controller)
    #tunnel = TunnelController(controller)

    # add some cli commands for static classes without init
    CLI.add_command("plot_topology", TopologyManager.plot, "Plot topology")
    CLI.add_command("describe_topology", TopologyManager.describe, "Describe topology")
    CLI.add_command("describe_groups", GroupManager.describe, "Describe groups")
    CLI.add_command("show_configuration", Configuration.show_all, "Show all configurations")
    CLI.add_command("table_manager", TableEntryManager.handle_cli_command, "show_tables <controller name>")

    CLI.add_command("load_static_rules", load_static_rules, "Load static rules", ipv4)

    # start global grpc control server
    GRPCServer(listen_port=Configuration.get('listen_port')).start()

    # start connection procedure in thread, so that cli will get initialized and logs can be printed
    threading.Timer(2, connect_to_switches, kwargs={'controller': controller}).start()

    CLI.start_cli()




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')

    parser.add_argument('--config', help='path to config file',
                        type=str, action="store", required=True,
                        default='config.json')


    args = parser.parse_args()

    # write all command line arguments to configuration
    Configuration.init(args)

    main()
