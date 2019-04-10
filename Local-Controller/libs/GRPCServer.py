import grpc
import proto.connection_pb2_grpc
import proto.connection_pb2

from concurrent import futures
from libs.core.Log import Log
from libs.core.Event import Event
from libs.TopologyManager import TopologyManager
from libs.core.BaseController import BaseController
from libs.Configuration import Configuration
import time
import pickle


class GlobalConnection:
    global_connection = None

    def __init__(self, ip=None, port=0):
        self.channel = grpc.insecure_channel(ip + ":" + str(port))
        self.stub = proto.connection_pb2_grpc.GlobalServerStub(self.channel)

        reponse = self.stub.CheckConnection(proto.connection_pb2.Empty())
        Log.info("Global connection to", ip + ":" + str(port))

        # remove possible old connection when a new global connection is initialized
        Event.on('global_connection', self.close)

    def close(self):
        Log.info("Global connection removed")
        Event.off('global_connection', self.close)
        self.channel.close()

    @staticmethod
    def send_topology_packet(pkt=None):
        if GlobalConnection.global_connection is not None:
            try:
                response = GlobalConnection.global_connection.stub.TopologyMessage(pkt)
            except Exception as e:
                pass

    @staticmethod
    def send_group_packet(pkt=None):
        if GlobalConnection.global_connection is not None:
            try:
                response = GlobalConnection.global_connection.stub.GroupMessage(pkt)
            except Exception as e:
                pass

    @staticmethod
    def send_port_info(info=None):
        if GlobalConnection.global_connection is not None:
            try:
                response = GlobalConnection.global_connection.stub.PortMessage(info)
            except Exception as e:
                pass


class LocalServer(proto.connection_pb2_grpc.LocalServerServicer):
    group_messages = []
    topology_messages = []
    controller = None

    def AddEntry(self, request, context):
        """
        Add a table entry to the switch
        """

        if LocalServer.controller.add_entry(entry=request):
            if Configuration.get("name") == "s1":
                Log.log_to_file(round((time.time() * 1000) % 1000000), request.table_name, "\r\n", file="logs/entry_info.txt")
            return proto.connection_pb2.Status(code=1, message="all good")

    def RemoveEntry(self, request, context):
        """
        Remove a table entry from the switch
        """
        if LocalServer.controller.remove_entry(entry=request):
            return proto.connection_pb2.Status(code=1, message="all good")

        return proto.connection_pb2.Status(code=0, message="error")

    def Hello(self, request, context):
        Event.trigger('global_connection')

        GlobalConnection.global_connection = GlobalConnection(ip=request.ip, port=request.port)

        device = TopologyManager.get_device(Configuration.get('name'))

        return proto.connection_pb2.SwitchInfo(name=Configuration.get('name'),
                                               ip=device.get_ip(),
                                               mac=device.get_mac(),
                                               bfr_id=device.get_bfr_id(0))


class GRPCServer:

    def __init__(self, listen_port=0):
        self.listen_port = listen_port
        self.running = True
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    def start(self):
        """
        Start grpc server
        This grpc server will be used for the direction global-controller ----> local-controller
        """
        proto.connection_pb2_grpc.add_LocalServerServicer_to_server(LocalServer(), self.server)
        self.server.add_insecure_port('[::]:' + str(self.listen_port))
        Log.info("Start GRPC Server on port", self.listen_port)
        self.server.start()

    def stop(self):
        """
        Stop the grpc server
        """
        self.server.stop(1)
