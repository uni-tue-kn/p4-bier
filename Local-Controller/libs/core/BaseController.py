"""
This module builds the basis for each used controller
"""

import utils.p4runtime_lib.bmv2
import utils.p4runtime_lib.helper
from libs.core.Log import Log
import grpc
import pickle
from libs.core.Switch import Switch
from utils.p4runtime_lib.switch import  ShutdownAllSwitchConnections, RemoveConnection
from libs.core.Event import Event
from libs.Configuration import Configuration
from libs.TableEntryManager import TableEntry
import threading


class BaseController(object):

    def __init__(self, p4info_file_path=None, bmv2_path=None):
        self.__p4info_helper = utils.p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
        self.__bmv2_file_path = bmv2_path
        self.__connection = None

        """
        This list is used to purge all current table entries when the
        main controller reconnects to the local controller
        """
        self.entries = []

        Event.on('exit', self.shutdown)
        Event.on('add_entry', self.add_entry)
        Event.on('global_connection', self.purge)  # purge all entries when a new global connection is established

    def get_connection(self):
        """
        Returns all switch connections
        :return: Bmv2SwitchConnection
        """
        return self.__connection

    def __add_switch_connection(self, name=None, address=None, device_id=None):
        """
        Connect to switch with given address and do
        master arbitration
        :param name: Name of the switch
        :param address: Address of grpc connection
        :param dID: Device id
        :return: Bmv2SwitchConnection
        """
        switch = utils.p4runtime_lib.bmv2.Bmv2SwitchConnection(name=name,
                                                               address=address,
                                                               device_id=device_id,
                                                               proto_dump_file="logs/log.txt")

        return switch

    def set_forwarding_pipeline_config(self):
        """
        Set forwarding pipeline on the switch based on p4info file
        :return:
        """
        try:
            self.__connection.SetForwardingPipelineConfig(p4info=self.__p4info_helper.p4info,
                                                          bmv2_json_file_path=self.__bmv2_file_path.encode())
            Event.trigger("switch_arbitrated")
        except Exception as e:
                Log.error("Error in forwarding pipeline", e)

        Log.info("Forwarding pipeline set.")

    def connect_and_arbitrate(self, grpc_port=0, device_id=0):
        """
        Connect and arbitrate to the switch
        :param grpc_port: grpc port of the p4 switch
        :param device_id: device id of the p4 switch
        :return:
        """

        i = device_id + 1
        try:
            # add connection to switch
            self.__connection = self.__add_switch_connection(name='s{0}'.format(i),
                                                             address='127.0.0.1:{0}'.format(grpc_port),
                                                             device_id=device_id)

            # start packet in thread
            self.__connection.start_thread()

            if self.__connection.MasterArbitrationUpdate():
                base_mac = int('20:00:00:00:00:00'.translate(None, ":,-"), 16)
                real_mac = format(base_mac + i, 'x')
                mac = ":".join(real_mac[i:i + 2] for i in range(0, len(real_mac), 2))

                Configuration.set('name', 's{0}'.format(i).encode('utf-8'))

                Event.trigger("new_switch_connection", name='s{0}'.format(i),
                              device=Switch(name='s{0}'.format(i).encode('utf-8'), ip='20.0.{0}.0'.format(i).encode('utf-8'),
                                            mac=mac.encode('utf-8'), bfr_id=i))

                Log.info("Arbitration done. Connected to swtich")
                Event.trigger("arbitration_done")
            else:
                Log.error("Master arbitration failed")

        except Exception as e:
            Log.error(e)

    def delete_table_entry(self, table_name=None, entry=None):
        """
        Deletes an table entry on the switch
        :param table_name: table name
        :param entry: table entry
        :return:
        """

        try:
            table_entry = self.__p4info_helper.buildTableEntry(
                table_name=table_name,
                match_fields=entry.match_fields,
                priority=entry.priority)

            self.__connection.DeleteTableEntry(table_entry)

            Log.info("Remove entry:", table_name, entry.match_fields)

            return True
        except Exception as e:
            Log.error("Error in table delete", table_name, entry.match_fields, entry.priority, e)
            return False

    def add_entry(self, entry=None):
        """
        Adds an table entry and locks write request to prevent threading problems
        :param switch:
        :param table_name:
        :param match_fields:
        :param action_name:
        :param action_params:
        :return:
        """

        e = pickle.loads(entry.table_entry)

        # a table entry is identified by match fields and priority
        self.entries.append((entry.table_name.encode('utf-8'),
                            TableEntry(match_fields=e.match_fields, priority=e.priority)))

        return self.add_table_entry(table_name=entry.table_name.encode('utf-8'), entry=e)

    def remove_entry(self, entry=None):
        """
        Adds an table entry and locks write request to prevent threading problems
        :param entry: TableEntry serialized as pickle string
        :return:
        """

        e = pickle.loads(entry.table_entry)

        # a table entry is identified by match fields and priority
        self.entries.remove((entry.table_name.encode('utf-8'), TableEntry(match_fields=e.match_fields, priority=e.priority)))

        return self.delete_table_entry(table_name=entry.table_name.encode('utf-8'), entry=e)

    def add_table_entry(self, table_name=None, entry=None):
        """
        Adds an table entry and locks write request to prevent threading problems
        :param table_name: table name
        :param entry: Table entry
        :return:
        """
        try:
            table_entry = self.__p4info_helper.buildTableEntry(
                table_name=table_name,
                match_fields=entry.match_fields,
                action_name=entry.action_name,
                action_params=entry.action_params,
                priority=entry.priority)

            self.__connection.WriteTableEntry(table_entry)

            Log.info("Add entry:", table_name, entry)

            return True
        except Exception as e:
            Log.error(e, "for", table_name, entry.match_fields, entry.action_name, entry.action_params, entry.priority)
            return False

    def purge(self):
        """
        Delete all current table entries
        """
        [self.delete_table_entry(table_name=e[0], entry=e[1]) for e in self.entries]
        Log.info("Entries purged")
        self.entries = []

    def shutdown(self):
        ShutdownAllSwitchConnections()
