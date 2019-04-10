"""
This module implements an MacController
Set rewrite rules for layer 2
"""

from libs.core.Log import Log
from libs.TableEntryManager import TableEntryManager, TableEntry
from libs.core.Event import Event
from libs.TopologyManager import TopologyManager
from libs.Configuration import Configuration


class MacController(object):

    def __init__(self, base):
        """
        Init Maccontroller with base controller
        :param base:
        """

        # table manager
        self.table_manager = TableEntryManager(controller=base, name="MacController")
        self.table_manager.init_table("egress.mac_c.adjust_mac")

        Event.on("topology_change", self.update)

    def update_mac_entry(self):
        """
        Add mac rewriting rule for switch->dst_dev via port
        :param switch: switch where rule will be installed
        :param dst_dev: next_hop
        :param port: port which is used towards next_hop
        :return:
        """
        valid_entries = []

        device = TopologyManager.get_device(Configuration.get('name'))

        for device_name in device.get_device_to_port_mapping():
            dev = TopologyManager.get_device(device_name)
            port = device.get_device_to_port(device_name)
            Log.debug("Mac:", Configuration.get('name'), "->", device_name, "via", port)

            entry = TableEntry(match_fields={"standard_metadata.egress_port": int(port)},
                               action_name="egress.mac_c.set_mac",
                               action_params={"srcAddr": device.get_mac(),
                                              "dstAddr": dev.get_mac()
                                              })

            TableEntryManager.handle_table_entry(manager=self.table_manager,
                                                 table_name="egress.mac_c.adjust_mac",
                                                 table_entry=entry)

            valid_entries.append(entry.match_fields)

        Log.debug("Installed Mac rewriting rule for", Configuration.get('name'))

        # remove possible old entries
        self.table_manager.remove_invalid_entries(table_name="egress.mac_c.adjust_mac", valid_entries=valid_entries)

    #############################################################
    #                   Event Listener                          #
    #############################################################

    def update(self, *args, **kwargs):
        """
        Update mac entries
        triggered by event
        :return:
        """

        self.update_mac_entry()
