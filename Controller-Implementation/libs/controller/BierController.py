"""
This module implements an BierController, that installs the bier forwarding rules
Encap rules and bier header computation are done in the tunnel controller
"""

from libs.core.Log import Log
from libs.core.CLI import CLI
from operator import ior
from libs.core.Event import Event
from libs.TopologyManager import TopologyManager
from libs.Configuration import Configuration
from libs.TopologyManager import DeviceNotFound, NextHopNotFound
from libs.TableEntryManager import TableEntryManager, TableEntry
from libs.GroupManager import GroupManager
import time


class BierComputation(object):
    """
    This class calculates birt, fbm and bift for a BFR
    """

    @staticmethod
    def id_to_bitstring(id=0):
        """
        Converts an id to actual bitstring
        e.g. 5 is not 101, but 10000
        :param id: bfr id
        :return: bfr id as bitstring
        """
        return int(2 ** (id - 1))

    @staticmethod
    def build_birt(switch=None, domain=None):
        """
        Build bit index routing table
        :param switch: switch for which the birt should be calculated
        :param domain: domain for which the birt should be build
        :return: birt in format {bfr-id: [dest prefix, nbr prefix]
        """
        # {bfr-id: [dest prefix, nbr prefix]
        birt = {}
        for destination in TopologyManager.get_topology(domain).get_nodes():
            if destination != switch:
                destination_device = TopologyManager.get_device(destination)

                if destination_device.get_type() == "Host": # dont calculate entry for host
                    continue

                try:
                    next_hop = TopologyManager.get_next_hop(switch, destination, domain)
                    birt[destination_device.get_bfr_id(domain)] = [destination_device.get_ip(),
                                                                   next_hop.get_ip()]
                except NextHopNotFound: # maybe a path towards the destination is not yet learned
                    continue

        return birt

    @staticmethod
    def get_fbm(birt=None, next_hop_prefix=None):
        """
        Calculated forwarding bitmask for given birt and next_hop
        :param birt:
        :param next_hop_prefix:
        :return:
        """
        fbm = 0

        for entry in birt:
            if birt.get(entry)[1] == next_hop_prefix:
                fbm |= BierComputation.id_to_bitstring(entry)

        return fbm

    @staticmethod
    def build_bift(switch=None, domain=0):
        """
        Generates the bit index forwarding table
        :param switch: Switch for which the table should be calculated
        :param domain: Domain for which the bift should be build
        :return: bift {bfr-id: [fbm, nextHop]
        """
        birt = BierComputation.build_birt(switch=switch, domain=domain)

        # {bfr-id: [fbm, nextHop]
        bift = {}

        for dest in birt:
            fbm = BierComputation.get_fbm(birt=birt, next_hop_prefix=birt.get(dest)[1])
            destination = TopologyManager.get_device_by_domain_and_id(domain, dest)

            next_hop = TopologyManager.get_next_hop(switch, destination, domain)

            bift[dest] = [fbm, next_hop.get_name()]
        return bift

    @staticmethod
    def compute_bier_header(mc_addr=None, domain=None):
        """
        Compute the bier header for a given mc_addr in a given domain
        :param mc_addr: multicast address
        :param domain: domain identifier
        :return:
        """
        # only use bfrs in given domain
        all_bfrs = filter(lambda x: domain in TopologyManager.get_domain_for_device(x),
                          GroupManager.get_bfr_by_mc_addr(mc_addr))

        # get (domain specific) bfr ids
        bfrs = map(lambda x: TopologyManager.get_device(x).get_bfr_id(domain), all_bfrs)

        bier_header = reduce(ior, map(lambda x: BierComputation.id_to_bitstring(x), bfrs), 0)

        return bier_header


class BierController:
    """
    This class implements an bier controller which sets the
    bier forwarding entries (inside a domain) and the bier domain forwarding entries
    (between domains)
    It does not set the tunnel entry to add the bier header, this is done by the Tunnel Controller
    """

    def __init__(self, base):
        self._baseController = base
        Event.on("topology_change", self.update)  # update bier tables when topology changes

        # this controller manages the following tables
        self.table_manager = TableEntryManager(controller=base, name="BierController")
        self.table_manager.init_table("ingress.bier_c.bift")



    def update_frr_node_protection(self, switch=None, domain=None, port=None, to_id=None, fbm=None, next_hop=None):
        """
        Implements BIER-FRR node protection
        """

        switch_device = TopologyManager.get_device(name=switch)
        remainingBits = BierComputation.id_to_bitstring(id=to_id)

        # get bift for failed nh
        bift_nh = BierComputation.build_bift(switch=next_hop, domain=domain)

        next_hop_device = TopologyManager.get_device(name=next_hop)

        # send a copy of the packet to the broken node in case its only a link failure
        if next_hop_device.get_bfr_id(domain) == to_id:
            bift_nh[to_id] = [BierComputation.id_to_bitstring(to_id), next_hop]

        if to_id not in bift_nh:
            return

        # the backup fbm is the intersection of the old fbm and the fbm of the nh for this entry
        new_fbm = fbm & bift_nh.get(to_id)[0]

        # tunnel node is nh of bift from failed nh for this entry
        tunnel_node = TopologyManager.get_device(name=bift_nh.get(to_id)[1])

        src_ip = switch_device.get_ip()
        dst_ip = tunnel_node.get_ip()

        entry = TableEntry(switch=switch,
                           match_fields={
                               "meta.bier_md.remainingBits": (remainingBits, remainingBits),
                               "meta.ports.status": (0, BierComputation.id_to_bitstring(port))
                           },
                           action_name="ingress.bier_c.forward_encap",
                           action_params={
                               "fbm": new_fbm,
                               "srcAddr": src_ip,
                               "dstAddr": dst_ip
                           },
                           priority=1)


        return entry


    def update_frr_link_protection(self, switch=None, domain=None, port=None, to_id=None, fbm=None, next_hop=None):
        """
        In BIER-FRR link protection, just use an IP tunnel to the NH behind the failed link
        """

        switch_device = TopologyManager.get_device(name=switch)
        src_ip = switch_device.get_ip()
        dst_ip = TopologyManager.get_device(name=next_hop).get_ip()
        remainingBits = BierComputation.id_to_bitstring(to_id)


        entry = TableEntry(switch=switch,
                           match_fields={
                               "meta.bier_md.remainingBits": (remainingBits, remainingBits),
                               "meta.ports.status": (0, BierComputation.id_to_bitstring(port))
                            },
                            action_name="ingress.bier_c.forward_encap",
                            action_params={
                                "fbm": fbm,
                                "srcAddr": src_ip,
                                "dstAddr": dst_ip
                            },
                            priority=1)


        return entry

    def update_bier_forwarding_entries(self, switch=None):
        """
        Adds bier forwarding entry for given switch in specifc domain
        :param switch:
        :param domain: domain identifier
        :return:
        """

        table_name = "ingress.bier_c.bift"

        valid_entries = []

        for domain in TopologyManager.get_domain_for_device(switch):
            domain = int(domain)
            bift = BierComputation.build_bift(switch=switch, domain=domain)

            for entry in bift:
                bit_string = BierComputation.id_to_bitstring(id=entry)


                out_port = TopologyManager.get_device(switch).get_device_to_port(bift.get(entry)[1])

                # generate default bier entry
                e = TableEntry(switch=switch,
                               match_fields={"meta.bier_md.remainingBits": (bit_string, bit_string),
                                             "meta.ports.status": (
                                                    BierComputation.id_to_bitstring(id=out_port),
                                                    BierComputation.id_to_bitstring(id=out_port))
                                            },
                               action_name="ingress.bier_c.forward",
                               action_params={"fbm": bift.get(entry)[0],
                                              "port": out_port
                                             },
                               priority=1)

                if TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                        table_name=table_name, table_entry=e):
                    Log.async_debug("Installed BIER rule for", switch, "to bfr-id", entry)

                valid_entries.append(e.match_fields)

                # generate bier-frr link protection entry for this switch and bfr
                if Configuration.get('protection') == 'Link':
                    frr_entry = self.update_frr_link_protection(switch=switch, domain=domain, port=out_port, to_id=entry, fbm=bift.get(entry)[0], next_hop=bift.get(entry)[1])

                    if TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                            table_name=table_name, table_entry=frr_entry):
                        Log.async_debug("Installed BIER-FRR link protection rule for", switch)

                    valid_entries.append(frr_entry.match_fields)

                # generate bier-frr node protection entry for this switch and bfr
                if Configuration.get('protection') == 'Node':
                    frr_entry = self.update_frr_node_protection(switch=switch, domain=domain, port=out_port, to_id=entry, fbm=bift.get(entry)[0], next_hop=bift.get(entry)[1])

                    if frr_entry:
                        if TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                            table_name=table_name, table_entry=frr_entry):
                            Log.async_debug("Installed BIER-FRR node protection rule for", switch, "to", entry)

                        valid_entries.append(frr_entry.match_fields)


        bfr_id = BierComputation.id_to_bitstring(TopologyManager.get_device(switch).get_bfr_id(0))
        # Add decap entry
        entry = TableEntry(switch=switch,
                           match_fields={
                               "meta.bier_md.remainingBits": (bfr_id, bfr_id)
                           },
                           action_name="ingress.bier_c.decap",
                           action_params={
                               "decapBit": bfr_id
                           },
                           priority=1)

        if TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                table_name=table_name, table_entry=entry):
            Log.async_debug("Installed BIER decap rule for", switch)

        valid_entries.append(entry.match_fields)

        self.table_manager.remove_invalid_entries(switch=switch, table_name=table_name, valid_entries=valid_entries)


    def load_static_rules(self):
        """
        Load static rules from json file specified in config
        """
        pass


    #############################################################
    #                   Event Listener                          #
    #############################################################

    def update(self, *args, **kwargs):
        """
        Update bier tables, bift
        Is called on certain events
        :return:
        """

        if "port_update" in kwargs:
            try:
                d = Configuration.get('update')

                if "bier" not in d:
                    return

                if "sleep" in kwargs:
                    time.sleep(kwargs.get("sleep"))
            except ConfigurationNotFound:
                pass

        srcDevice = kwargs.get('src_device')

        for switch in self._baseController.get_connections():
            self.update_bier_forwarding_entries(switch=switch)

        Log.async_info("Updated BIER entries.")
