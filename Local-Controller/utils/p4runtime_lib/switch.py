# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from Queue import Queue
from abc import abstractmethod
from datetime import datetime

import grpc
from p4.v1 import p4runtime_pb2
from p4.tmp import p4config_pb2
from libs.core.Log import Log
import threading
import time
from libs.core.Event import Event

MSG_LOG_MAX_LEN = 1024

# List of all active connections
connections = []

def ShutdownAllSwitchConnections():
    for c in connections:
        Log.async_info("Shutting down connection", c.name)
        c.shutdown()


def RemoveConnection(c):
    connections.remove(c)


class SwitchConnection(object):

    def __init__(self, name=None, address='127.0.0.1:50051', device_id=0,
                 proto_dump_file=None):
        self.name = name
        self.address = address
        self.device_id = device_id
        self.p4info = None
        self.channel = grpc.insecure_channel(self.address)
        if proto_dump_file is not None:
            interceptor = GrpcRequestLogger(proto_dump_file)
            self.channel = grpc.intercept_channel(self.channel, interceptor)

        self.client_stub = p4runtime_pb2.P4RuntimeStub(self.channel)

        self.proto_dump_file = proto_dump_file
        self.stream_out_q = IterableQueue()
        self.stream_in_q = IterableQueue()

        self.stream = self.client_stub.StreamChannel(self.stream_req_iterator())
        self.stream_recv_thread = threading.Thread(
            target=self.stream_recv, args=(self.stream,))

        self.active = True

        connections.append(self)

    def start_thread(self):
        self.stream_recv_thread.start()

    def stop_thread(self):
        self.stream_recv_thread.join()

    def stream_req_iterator(self):
        while True:
            p = self.stream_out_q.get()

            if p is None:
                break

            yield p

    def stream_recv(self, stream):
        try:
            for p in stream:
                self.stream_in_q.put(p)
                Event.trigger("packet_in", packet=p, switch=self.name)


        except grpc.RpcError as e:
            pass  # arbitration end



    @abstractmethod
    def buildDeviceConfig(self, **kwargs):
        return p4config_pb2.P4DeviceConfig()

    def shutdown(self):
        self.active = False
        self.stream_out_q.put(None)
        self.stream_recv_thread.join()

    def MasterArbitrationUpdate(self):
        request = p4runtime_pb2.StreamMessageRequest()
        request.arbitration.device_id = self.device_id
        request.arbitration.election_id.high = 0
        request.arbitration.election_id.low = 1

        self.stream_out_q.put(request)

        rep = self.get_stream_packet("arbitration", timeout=5)

        if rep is None:
            return False
        else:
            return True

    def SetForwardingPipelineConfig(self, p4info, dry_run=False, **kwargs):
        device_config = self.buildDeviceConfig(**kwargs)
        request = p4runtime_pb2.SetForwardingPipelineConfigRequest()
        request.election_id.low = 1
        request.device_id = self.device_id
        config = request.config
        config.p4info.CopyFrom(p4info)
        config.p4_device_config = device_config.SerializeToString()

        request.action = p4runtime_pb2.SetForwardingPipelineConfigRequest.VERIFY_AND_COMMIT
        if dry_run:
            print("P4Runtime SetForwardingPipelineConfig:", request)
        else:
            self.client_stub.SetForwardingPipelineConfig(request)

    def WriteTableEntry(self, table_entry, dry_run=False):

        if not self.active:
            return

        request = p4runtime_pb2.WriteRequest()
        request.device_id = self.device_id
        request.election_id.low = 1
        request.election_id.high = 0
        update = request.updates.add()
        update.type = p4runtime_pb2.Update.INSERT
        update.entity.table_entry.CopyFrom(table_entry)

        if dry_run:
            print("P4Runtime Write:", request)
        else:
            self.client_stub.Write(request)



    def DeleteTableEntry(self, table_entry, dry_run=False):

        if not self.active:
            return

        request = p4runtime_pb2.WriteRequest()
        request.device_id = self.device_id

        # nur master duerfen writes vornehmen
        request.election_id.low = 1
        request.election_id.high = 0

        update = request.updates.add()
        update.type = p4runtime_pb2.Update.DELETE
        update.entity.table_entry.CopyFrom(table_entry)
        if dry_run:
            print("P4 Runtime Write:", request)
        else:
            self.client_stub.Write(request)


    def WritePacketOut(self, payload):
        if not self.active:
            return

        request = p4runtime_pb2.StreamMessageRequest()
        request.packet.payload = payload

        self.stream_out_q.put(request)

    def ReadTableEntries(self, table_id=None, dry_run=False):
        request = p4runtime_pb2.ReadRequest()
        request.device_id = self.device_id
        entity = request.entities.add()
        table_entry = entity.table_entry
        if table_id is not None:
            table_entry.table_id = table_id
        else:
            table_entry.table_id = 0
        if dry_run:
            print("P4Runtime Read:", request)
        else:
            for response in self.client_stub.Read(request):
                yield response

    def ReadCounters(self, counter_id=None, index=None, dry_run=False):
        request = p4runtime_pb2.ReadRequest()
        request.device_id = self.device_id
        entity = request.entities.add()
        counter_entry = entity.counter_entry
        if counter_id is not None:
            counter_entry.counter_id = counter_id
        else:
            counter_entry.counter_id = 0
        if index is not None:
            counter_entry.index.index = index
        if dry_run:
            print("P4Runtime Read:", request)
        else:
            for response in self.client_stub.Read(request):
                yield response

    def send_packet_out(self, payload):
        self.WritePacketOut(payload)

    def stream_iterator(self):
        while True:
            try:
                p = self.stream_requests.get()
            except Exception as e:
                Log.error("Error in stream_iterator", e)

            if p is None:
                break
            yield p

    def stream_receive(self, stream):
        for p in stream:
            self.stream_in_q.put(p)

    def get_stream_packet(self, type_, timeout=1):
        start = time.time()
        try:
            while True:
                remaining = timeout - (time.time() - start)
                if remaining < 0:
                    break
                msg = self.stream_in_q.get(timeout=remaining)
                if not msg.HasField(type_):
                    continue
                return msg
        except:  # timeout expired
            pass
        return None


class GrpcRequestLogger(grpc.UnaryUnaryClientInterceptor,
                        grpc.UnaryStreamClientInterceptor):
    """Implementation of a gRPC interceptor that logs request to a file"""

    def __init__(self, log_file):
        self.log_file = log_file
        with open(self.log_file, 'w') as f:
            # Clear content if it exists.
            f.write("")

    def log_message(self, method_name, body):
        with open(self.log_file, 'a') as f:
            ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            msg = str(body)
            f.write("\n[%s] %s\n---\n" % (ts, method_name))
            if len(msg) < MSG_LOG_MAX_LEN:
                f.write(str(body))
            else:
                f.write("Message too long (%d bytes)! Skipping log...\n" % len(msg))
            f.write('---\n')

    def intercept_unary_unary(self, continuation, client_call_details, request):
        self.log_message(client_call_details.method, request)
        return continuation(client_call_details, request)

    def intercept_unary_stream(self, continuation, client_call_details, request):
        self.log_message(client_call_details.method, request)
        return continuation(client_call_details, request)


class IterableQueue(Queue):
    _sentinel = object()

    def __iter__(self):
        return iter(self.get, self._sentinel)

    def close(self):
        self.put(self._sentinel)
