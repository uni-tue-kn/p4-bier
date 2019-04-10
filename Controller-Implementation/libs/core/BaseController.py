"""
This module builds the basis for each used controller
"""

import grpc
import threading
import os
import pickle
import proto.connection_pb2_grpc
import proto.connection_pb2
from libs.core.Switch import Switch
from libs.core.Event import Event
from libs.core.Log import Log
from libs.core.SwitchConnection import SwitchConnection
from libs.core.CLI import CLI
from libs.Configuration import Configuration
from libs.Exceptions import SwitchConnectionFailed


class BaseController(object):

    def __init__(self):
        self.__connections = {}
        self.__startPort = 30050
        self.connected = True

    def get_connections(self):
        """
        Returns all switch connections
        :return: Bmv2SwitchConnection
        """
        return self.__connections

    def get_connection(self, name):
        """
        Returns a specific switch with a given name
        :param name: Switch name
        :return: Bmv2SwitchConnection
        """
        return self._connections[name]

    def connect(self):
        """
        All switches grpc addresses are in ascending order.
        Connect until a connection can't be established
        :return:
        """

        for switch in Configuration.get("switches"):
            try:
                self.__connections[switch["name"]] = SwitchConnection(grpc_address='127.0.0.1:{0}'.format(switch["local_controller_port"]))
                Log.async_debug("Connected to controller on port", switch["local_controller_port"])
                Event.trigger('switch_connected', name=switch["name"])
            except grpc.RpcError as e:
                raise SwitchConnectionFailed(switch["name"], switch["local_controller_port"])

        Log.async_info("Connected to", len(self.__connections), "controller")
        Configuration.set('connected', True)

    def delete_table_entry(self, switch=None, table_name=None, table_entry=None):
        """
        Deletes an table entry on the switch which matches the table name and match_fields
        :param switch:
        :param table_name:
        :param match_fields:
        :return:
        """
        entry = proto.connection_pb2.TableEntry(
                    table_name=table_name,
                    table_entry=pickle.dumps(table_entry))

        self.__connections.get(switch).removeTableEntry(tableEntry=entry)



    def add_table_entry(self, switch=None, table_name=None, table_entry=None):
        """
        Adds an table entry and locks write request to prevent threading problems
        :param switch:
        :param table_name:
        :param match_fields:
        :param action_name:
        :param action_params:
        :return:
        """

        entry = proto.connection_pb2.TableEntry(
                                        table_name=table_name,
                                        table_entry=pickle.dumps(table_entry))

        self.__connections.get(switch).addTableEntry(tableEntry=entry)
