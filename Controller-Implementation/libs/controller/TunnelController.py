"""
This module implements an TunnelController
Set encap/decap rules for ipv4/bier
"""
from libs.core.Log import Log
from libs.core.CLI import CLI
from libs.controller.BierController import BierComputation
from libs.GroupManager import GroupManager
from libs.core.Event import Event
from operator import ior
from libs.controller.TopologyController import TopologyController
from libs.TopologyManager import TopologyManager
from libs.Configuration import Configuration
from libs.TableEntryManager import TableEntryManager, TableEntry
from networkx import NodeNotFound


class TunnelController(object):
    def __init__(self, base):
        """
        Init Tunnelcontroller with base controller and add cli commands
        :param base: basecontroller
        :param type: Sets bier or bier-te type
        """
        self._baseController = base
        Event.on("group_update", self.update_based_on_group)
        Event.on("topology_change", self.update_based_on_topology)

        # add decap rules for devices
        Event.on("switch_connected", self.add_ipv4_decap_rule)

        self.table_manager = TableEntryManager(controller=base, name="TunnelController")
        self.table_manager.init_table("ingress.tunnel_c.decap_bier")
        self.table_manager.init_table("ingress.tunnel_c.decap_ipv4")
        self.table_manager.init_table("egress.tunnel_c.encap_ipv4")

    ##########################################################
    #                                                        #
    #               BIER encap /vdecap section               #
    #                                                        #
    ##########################################################

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
                type = 0xBB00

                entry = TableEntry(switch=switch,
                                   match_fields={
                                       "hdr.ipv4.dstAddr": mc_addr,
                                   },
                                   action_name="egress.tunnel_c.add_bier",
                                   action_params={
                                       "bs": bitstring,
                                       "etherType": type,
                                       "domain": domain
                                   })

                if TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                        table_name="egress.tunnel_c.encap_ipv4",
                                                        table_entry=entry):
                    Log.async_debug("Installed encap ipv4 rule for", switch, mc_addr, bitstring)

                valid_entries.append(entry.match_fields)

        self.table_manager.remove_invalid_entries(switch=switch,
                                                  table_name="egress.tunnel_c.encap_ipv4",
                                                  valid_entries=valid_entries)

    def update_bier_decap_rule(self, switch=None):
        """
        Updates the bier decap rules based on the current topology
        :param switch: switch where decap rules should be installed
        :return:
        """
        valid_entries = []

        # bier decap rules
        for domain in TopologyManager.get_domain_for_device(switch):
            domain = int(domain)
            bfr_id = BierComputation.id_to_bitstring(TopologyManager.get_device(switch).get_bfr_id(domain))

            entry = TableEntry(switch=switch,
                               match_fields={
                                   "hdr.bier[0].BitString": (bfr_id, bfr_id),
                                   "hdr.bier[0].Domain": domain
                               },
                               action_name="ingress.tunnel_c.bier_decap",
                               action_params={
                                   "decapBit": bfr_id
                               },
                               priority=1)

            if TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                    table_name="ingress.tunnel_c.decap_bier",
                                                    table_entry=entry):
                Log.async_debug("BIER decap rule updated on", switch, "for domain", domain)

            valid_entries.append(entry.match_fields)

        self.table_manager.remove_invalid_entries(switch=switch,
                                                  table_name="ingress.tunnel_c.decap_bier",
                                                  valid_entries=valid_entries)


    #############################################################
    #                   Event Listener                          #
    #############################################################

    def add_ipv4_decap_rule(self, *args, **kwargs):
        """
        Adds an ipv4 decap rule for the switch
        This event is triggered when a switch is arbitrated
        :return:
        """
        device = TopologyManager.get_device(kwargs.get('name'))
        entry = TableEntry(switch=device.get_name(),
                           match_fields={"hdr.ipv4.dstAddr": device.get_ip()},
                           action_name="ingress.tunnel_c.ipv4_decap")

        if TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                table_name="ingress.tunnel_c.decap_ipv4",
                                                table_entry=entry):
            Log.async_debug("Ipv4 decap rule installed for", kwargs.get('name'))



    def update_based_on_topology(self, *args, **kwargs):
        """
        Run an update based on a topology change
        In this casae the bier decap rules have to be adjusted
        because a switch may now be in a different domain
        :return:
        """
        for bfr in Configuration.get("switches"):
            switch = bfr["name"]

            self.update_bier_decap_rule(switch=switch)

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
