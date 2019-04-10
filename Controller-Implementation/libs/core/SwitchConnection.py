import grpc
import threading
import proto.connection_pb2_grpc
from libs.core.Log import Log
from libs.core.Switch import Switch
from libs.core.Event import Event
from libs.Configuration import Configuration


class SwitchConnection:

    def __init__(self, grpc_address=None):
        self.channel = grpc.insecure_channel(grpc_address)
        self.stub = proto.connection_pb2_grpc.LocalServerStub(self.channel)

        response = self.stub.Hello(proto.connection_pb2.HelloMessage(ip="127.0.0.1", port=int(Configuration.get('listen_port'))))
        self.name = response.name.encode('utf-8')

        Event.trigger('new_switch_connection',
                      name=self.name, device=Switch(name=self.name, ip=response.ip.encode('utf-8'), mac=response.mac.encode('utf-8'), bfr_id=response.bfr_id))

    def addTableEntry(self, tableEntry=None):
        """
        Add a table entry to the switch
        """
        response = self.stub.AddEntry(tableEntry)

        if response.code == 0:
            Log.error("Error for entry:", tableEntry, "on switch", self.name)

    def removeTableEntry(self, tableEntry=None):
        """
        Remove a table entry from the switch
        """
        response = self.stub.RemoveEntry(tableEntry)

        if response.code == 0:
            Log.error("Error while removing entry:", tableEntry, "on switch", self.name)
