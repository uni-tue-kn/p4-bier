"""
This module manages the native IPMC multicast groups on the P4 switch
"""
from libs.core.Event import Event
from libs.core.Log import Log
from libs.TopologyManager import TopologyManager
from libs.TableEntryManager import TableEntryManager, TableEntry
from libs.Configuration import Configuration

import subprocess
from subprocess import Popen, PIPE, STDOUT
from collections import defaultdict

class GroupController(object):

    def __init__(self, thrift_port=9090, base=None):
        self.thrift_port = thrift_port
        self.cli = "simple_switch_CLI"

        self.max_port = 8

        self.mcgrp_to_port = defaultdict(list)

        Event.on("igmp_packet_to_controller", self.update_igmp)

        self.table_manager = TableEntryManager(controller=base, name="GroupController")
        self.table_manager.init_table("ingress.ipv4_c.ipv4_mc")

    def add_flood_node(self):
        """
        Add mc mc nodes
        """

        p = Popen([self.cli, '--thrift-port', str(self.thrift_port)], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        out, err = p.communicate(input="mc_node_create 0 " + " ".join(map(str, list(range(self.max_port)))))

        if err:
            Log.error(err)


    def init_flood_group(self):
        """
        This method initializes the multicast group that is responsible for flooding
        """
        p = Popen([self.cli, '--thrift-port', str(self.thrift_port)], stdout=PIPE, stdin=PIPE, stderr=STDOUT)

        # multicast group 1 is flood group
        out, err = p.communicate(input="mc_mgrp_create 1")

        if err:
            Log.error(err)

        p = Popen([self.cli, '--thrift-port', str(self.thrift_port)], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        out, err = p.communicate(input="mc_node_associate 1 0")
        if err:
            Log.error(err)

        Log.info("Initialize flood group")


    def update_mc_group(self, id=2, ports=None):

        ################################################################################
        # destory old mc grp
        ################################################################################
        p = Popen([self.cli, '--thrift-port', str(self.thrift_port)], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        out, err = p.communicate(input="mc_mgrp_destroy " + str(id))

        ################################################################################
        # create new mc grp
        ################################################################################
        p = Popen([self.cli, '--thrift-port', str(self.thrift_port)], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        out, err = p.communicate(input="mc_mgrp_create " + str(id))


        ################################################################################
        # destroy node associated with ports
        ################################################################################
        p = Popen([self.cli, '--thrift-port', str(self.thrift_port)], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        out, err = p.communicate(input="mc_node_destroy " + str(id))

        ################################################################################
        # create node associated with ports
        ################################################################################
        p = Popen([self.cli, '--thrift-port', str(self.thrift_port)], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        out, err = p.communicate(input="mc_node_create " + str(id) + " " + " ".join(map(str, ports)))

        ################################################################################
        # associate node and grp
        ################################################################################
        p = Popen([self.cli, '--thrift-port', str(self.thrift_port)], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
        out, err = p.communicate(input="mc_node_associate " + str(id) + " " + str(id))

    def update_igmp(self, pkt):
        """
        Update port information on ipmc groups
        """
        switch = TopologyManager.get_device(name=Configuration.get('name'))
        mc_addr = pkt.mc_address.encode('utf-8')
        src_ip = pkt.src_ip.encode('utf-8')

        port = switch.get_device_to_port(TopologyManager.get_device_by_ip(ip=src_ip).get_name())

        if pkt.type == 0x16:
            if port not in self.mcgrp_to_port[mc_addr]:
                self.mcgrp_to_port[mc_addr].append(port)
        elif pkt.type == 0x17:
            if port in self.mcgrp_to_port[mc_addr]:
                self.mcgrp_to_port[mc_addr].remove(port)


        self.update_mc_table()


    def update_mc_table(self):
        valid_entries = []
        id = 2

        for mcgrp in self.mcgrp_to_port:
            if self.mcgrp_to_port[mcgrp]:
                self.update_mc_group(id=id, ports=self.mcgrp_to_port[mcgrp])

                entry = TableEntry(match_fields={"hdr.ipv4.dstAddr": mcgrp},
                                   action_name="ingress.ipv4_c.set_mc_grp",
                                   action_params={"grp": id
                                                  })

                id += 1

                TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                     table_name="ingress.ipv4_c.ipv4_mc",
                                                     table_entry=entry)

                valid_entries.append(entry.match_fields)

        self.table_manager.remove_invalid_entries(table_name="ingress.ipv4_c.ipv4_mc", valid_entries=valid_entries)
