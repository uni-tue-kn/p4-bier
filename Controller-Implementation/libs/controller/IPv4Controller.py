"""
This module implements an IPv4 controller and sets the ipv4 forwarding entries
including multicast forwarding entries
"""

from libs.core.Log import Log
from libs.core.CLI import CLI
from libs.GroupManager import GroupManager
from libs.core.Event import Event
from libs.TopologyManager import TopologyManager, DeviceNotFound
from libs.TableEntryManager import TableEntryManager, TableEntry
from libs.controller.BierController import BierComputation
import networkx as nx
import time
from libs.Exceptions import ConfigurationNotFound
from libs.Configuration import Configuration
from collections import defaultdict


class IPv4Controller(object):

    def __init__(self, base):
        """
        Init IPv4Controller with base controller and add IPv4 cli commands
        :param base:
        """
        self._baseController = base

        self.table_manager = TableEntryManager(controller=base, name="IPv4Controller")
        self.table_manager.init_table("ingress.ipv4_c.ipv4")
        self.table_manager.init_table("ingress.ipv4_c.encap_ipv4")

        Event.on("group_update", self.update_based_on_group)

        Event.on("topology_change", self.update_ipv4_rules)


    def update_ipv4_entries(self, switch=None):
        """
        Update ipv4 entries based on shortest path on switch
        :param switch: switch where ipv4 entries will be installed
        :return:
        """

        paths = TopologyManager.get_paths(domain_id=0)
        valid_entries = []

        cur_dev = TopologyManager.get_device(switch)

        for dst in [d for d in paths.get(switch, {}) if d != switch]:  # don't check path from i->i
            # get the next_hop towards the destination along the shortest path
            dst_dev = TopologyManager.get_device(dst)
            next_hop = TopologyManager.get_next_hop(start_node=switch,
                                                    destination_node=dst,
                                                    domain_id=0)

            port = cur_dev.get_device_to_port(next_hop.get_name())

            entry = TableEntry(switch=switch,
                               match_fields={"hdr.ipv4.dstAddr": (str(dst_dev.get_ip()), 32),
                                             "meta.ports.status": (BierComputation.id_to_bitstring(id=int(port)), BierComputation.id_to_bitstring(id=int(port)))},
                               action_name="ingress.ipv4_c.forward",
                               action_params={"port": int(port)},
                               priority=1)

            if TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                    table_name="ingress.ipv4_c.ipv4",
                                                    table_entry=entry):
                Log.async_debug("Installed IPv4 forwarding rule for", switch, "->", dst)

            valid_entries.append(entry.match_fields)


        # Add decap entry
        entry = TableEntry(switch=cur_dev.get_name(),
                           match_fields={"hdr.ipv4.dstAddr": (str(cur_dev.get_ip()), 32)},
                           action_name="ingress.ipv4_c.decap",
                           priority=1)


        if TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                table_name="ingress.ipv4_c.ipv4",
                                                table_entry=entry):
            Log.async_debug("Installed IPv4 decap rule for", switch)

        valid_entries.append(entry.match_fields)

        return valid_entries


    def update_bier_encap_entry(self, switch=None):
        """
        Add bier encap entry for given prefix
        :param switch: switch where rules should be installed
        :return:
        """

        valid_entries = []

        for mc_addr in GroupManager.get_mc_addresses():
            for domain in GroupManager.get_domains_for_mc_addr(mc_addr):
                domain = int(domain)
                bitstring = BierComputation.compute_bier_header(mc_addr=mc_addr, domain=domain)

                entry = TableEntry(switch=switch,
                                   match_fields={
                                       "hdr.ipv4.dstAddr": mc_addr,
                                   },
                                   action_name="ingress.ipv4_c.add_bier",
                                   action_params={
                                       "bs": bitstring
                                   })

                if TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                        table_name="ingress.ipv4_c.encap_ipv4",
                                                        table_entry=entry):
                    Log.async_debug("Installed encap ipv4 rule for", switch, mc_addr, bitstring)

                valid_entries.append(entry.match_fields)

        self.table_manager.remove_invalid_entries(switch=switch,
                                                  table_name="ingress.ipv4_c.encap_ipv4",
                                                  valid_entries=valid_entries)


    def load_static_rules(self):
        """
        Load static rules from json file specified in config
        """

        valid_entries = defaultdict(list)

        for switch in Configuration.get('switches'):
            if "static_rules" in switch and Configuration.get('static_rules') == True:
                data = Configuration.load(switch['static_rules'])["entries"]

                for entry in data:
                    if entry['table'] != "ingress.ipv4_c.ipv4":
                        continue

                    e = TableEntry(switch=entry["switch"],
                                   match_fields={"hdr.ipv4.dstAddr": (str(entry["match_fields"][0]), int(entry["match_fields"][1])),
                                                  "meta.ports.status": (BierComputation.id_to_bitstring(id=int(entry["match_fields"][2])), int(entry["match_fields"][3]))},
                                   action_name=entry["action_name"],
                                   action_params={"port": int(entry["action_params"])},
                                   priority=1
                                  )


                    TableEntryManager.handle_table_entry(self.table_manager,
                                                         table_name=entry["table"],
                                                         table_entry=e)

                    valid_entries[entry["switch"]].append(e.match_fields)

                Log.async_info("Static rules for IPv4 loaded.")

        return valid_entries







    #############################################################
    #                   Event Listener                          #
    #############################################################

    def update_based_on_group(self, *args, **kwargs):
        """
        Updates tunnel rules
        :return:
        """
        for bfr in Configuration.get("switches"):
            # only update BFIRs
            if not bfr["ingress"]:
                continue

            self.update_bier_encap_entry(switch=bfr["name"])

    def update_ipv4_rules(self, *args, **kwargs):
        """
        Update ipv4 forwarding entries
        triggered by event
        :return:
        """

        if "port_update" in kwargs:
            try:
                d = Configuration.get('update')

                if "ipv4" not in d:
                    return

                if "sleep" in kwargs:
                    time.sleep(kwargs.get("sleep"))

            except ConfigurationNotFound:
                pass

        entries = defaultdict(list)

        for switch in self._baseController.get_connections():
            entries[switch].extend(self.update_ipv4_entries(switch=switch))

        static_rules = self.load_static_rules()

        for switch in entries:
            v_entries = entries.get(switch)
            v_entries.extend(static_rules[switch])
            self.table_manager.remove_invalid_entries(switch=switch, table_name="ingress.ipv4_c.ipv4", valid_entries=v_entries)

        Log.async_info("IP rules update.")
