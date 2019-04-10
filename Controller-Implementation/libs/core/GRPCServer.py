import grpc
import proto.connection_pb2_grpc
import proto.connection_pb2

from concurrent import futures
from libs.core.Log import Log
from libs.core.Event import Event
import threading


class GlobalServer(proto.connection_pb2_grpc.GlobalServerServicer):
    group_messages = []
    topology_messages = []

    def GroupMessage(self, request, context):
        Event.trigger("igmp_packet_in", pkt=request)

        return proto.connection_pb2.Status(code=1, message="accepted")

    def TopologyMessage(self, request, context):
        Event.trigger("topology_packet_in", pkt=request)

        return proto.connection_pb2.Status(code=1, message="accepted")

    def CheckConnection(self, request, context):
        Log.async_info("Local controller connected to global server")
        return proto.connection_pb2.Status(code=1, message="Connected")

    def PortMessage(self, request, context):
        """
        This method receives a port message
        """
        Log.async_info("Got port message")
        Log.async_debug(request)

        # this event is not catched yet
        # for demonstration purpose, the topology doesn't get updated
        # on a link failure
        Event.trigger("port_message", message=request)

        return proto.connection_pb2.Status(code=1, message="Accepted")


class GRPCServer:

    def __init__(self, listen_port=0):
        self.listen_port = listen_port
        self.running = True
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        Event.on('exit', self.stop)

    def start(self):
        """
        Start grpc server
        This grpc server will be used to connect the local controller with the global
        """
        proto.connection_pb2_grpc.add_GlobalServerServicer_to_server(GlobalServer(), self.server)
        self.server.add_insecure_port('[::]:' + str(self.listen_port))
        Log.async_info("Start GRPC Server on port", self.listen_port)
        self.server.start()

    def stop(self):
        """
        Stop the grpc server
        """
        self.server.stop(1)
