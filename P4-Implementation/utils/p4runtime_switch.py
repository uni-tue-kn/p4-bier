# Copyright 2017-present Barefoot Networks, Inc.
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

import sys, os, tempfile, socket
from time import sleep

from mininet.node import Switch
from mininet.moduledeps import pathCheck
from mininet.log import info, error, debug

from p4_mininet import P4Switch, SWITCH_START_TIMEOUT
from netstat import check_listening_on_port

class P4RuntimeSwitch(P4Switch):
    "BMv2 switch with gRPC support"
    next_grpc_port = 50051
    next_local_controller_port = 30051
    next_thrift_port = 9090

    def __init__(self, name, sw_path = None, json_path = None,
                 grpc_port = None,
                 local_controller_port = None,
                 thrift_port = None,
                 pcap_dump = False,
                 log_console = False,
                 verbose = False,
                 device_id = None,
                 enable_debugger = False,
                 cpu_port = 16,
                 log_file = None,
                 **kwargs):
        Switch.__init__(self, name, **kwargs)
        assert (sw_path)
        self.sw_path = sw_path
        # make sure that the provided sw_path is valid
        pathCheck(sw_path)

        if json_path is not None:
            # make sure that the provided JSON file exists
            if not os.path.isfile(json_path):
                error("Invalid JSON file.\n")
                exit(1)
            self.json_path = json_path
        else:
            self.json_path = None

        if grpc_port is not None:
            self.grpc_port = grpc_port
        else:
            self.grpc_port = P4RuntimeSwitch.next_grpc_port
            P4RuntimeSwitch.next_grpc_port += 1

        if local_controller_port is not None:
            self.local_controller_port = local_controller_port
        else:
            self.local_controller_port = P4RuntimeSwitch.next_local_controller_port
            P4RuntimeSwitch.next_local_controller_port += 1

        if thrift_port is not None:
            self.thrift_port = thrift_port
        else:
            self.thrift_port = P4RuntimeSwitch.next_thrift_port
            P4RuntimeSwitch.next_thrift_port += 1

        if check_listening_on_port(self.grpc_port):
            error('%s cannot bind port %d because it is bound by another process\n' % (self.name, self.grpc_port))
            exit(1)

        self.verbose = verbose
        logfile = "/tmp/p4s.{}.log".format(self.name)
        self.output = open(logfile, 'w')
        self.pcap_dump = pcap_dump
        self.enable_debugger = enable_debugger
        self.cpu_port = cpu_port
        self.log_console = log_console
        if log_file is not None:
            self.log_file = log_file
        else:
            self.log_file = "/tmp/p4s.{}.log".format(self.name)
        if device_id is not None:
            self.device_id = device_id
            P4Switch.device_id = max(P4Switch.device_id, device_id)
        else:
            self.device_id = P4Switch.device_id
            P4Switch.device_id += 1
        self.nanomsg = "ipc:///tmp/bm-{}-log.ipc".format(self.device_id)



    def check_switch_started(self, pid):
        for _ in range(SWITCH_START_TIMEOUT * 2):
            if not os.path.exists(os.path.join("/proc", str(pid))):
                return False
            if check_listening_on_port(self.grpc_port):
                return True
            sleep(0.5)

    def start_controller(self, controller=None):
        self.cmd("python " + controller + " --grpc-port " + str(self.grpc_port) + " --device-id " + str(self.device_id) + " --logfile " + str(self.log_file) + "_controller" + " --listen-port " + str(self.local_controller_port) + " --notification-socket ipc:///tmp/bmv2-" + str(self.device_id) + "-notifications.ipc --thrift-port " + str(self.thrift_port) + " > /dev/null &")
        print("Local controller (" + controller + ") for " + self.name + " (" + str(self.device_id) + ") started on port " + str(self.local_controller_port))
        print("python " + controller + " --grpc-port " + str(self.grpc_port) + " --device-id " + str(self.device_id) + " --logfile " + str(self.log_file) + "_controller" + " --listen-port " + str(self.local_controller_port) + " --notification-socket ipc:///tmp/bmv2-" + str(self.device_id) + "-notifications.ipc --thrift-port " + str(self.thrift_port))
        #print("python " + controller + " --grpc-port " + str(self.grpc_port) + " --device-id " + str(self.device_id) + " --logfile " + str(self.log_file) + "_controller" + " --listen-port " + str(self.local_controller_port) + " --notification-socket ipc:///tmp/bmv2-" + str(self.device_id) + "-notifications.ipc --thrift-port " + str(self.thrift_port) + "> /dev/null &")

    def start(self, controllers):
        info("Starting P4 grpc switch {}.\n".format(self.name))
        args = [self.sw_path]
        for port, intf in self.intfs.items():
            if not intf.IP():
                args.extend(['-i', str(port) + "@" + intf.name])
        if self.pcap_dump:
            args.append("--pcap %s" % self.pcap_dump)
        if self.nanomsg:
            args.extend(['--nanolog', self.nanomsg])
            #args.extend(['--nanolog', "ipc:///tmp/bmv2-" + str(self.device_id) + "-notifications.ipc"])

        args.extend(['--device-id', str(self.device_id)])
        P4Switch.device_id += 1
        if self.json_path:
            args.append(self.json_path)
        else:
            args.append("--no-p4")
        if self.enable_debugger:
            args.append("--debugger")
        if self.log_console:
            args.append("--log-console")
        args.extend(['--log-level', 'trace'])

        if self.thrift_port:
            args.extend(['--thrift-port', str(self.thrift_port)])

        if self.grpc_port:
            args.append("-- --grpc-server-addr 0.0.0.0:" + str(self.grpc_port))

        if self.cpu_port:
            args.extend(['--cpu-port', str(self.cpu_port)])

        #args.extend(['--notifications-addr', "ipc:///tmp/bmv2-" + str(self.device_id) + "-notifications.ipc"])


        cmd = ' '.join(args)
        info(cmd + "\n")

        logfile = "logs/p4s.{}.log".format(self.name)
        pid = None

        with tempfile.NamedTemporaryFile() as f:
            self.cmd("nice -n 20 " + cmd + ' >' + self.log_file + ' 2>&1 & echo $! >> ' + f.name)
            print("nice -n 20 " + cmd)
            pid = int(f.read())

        info("P4 switch {} PID is {}.\n".format(self.name, pid))

        if not self.check_switch_started(pid):
            error("P4 switch {} did not start correctly.\n".format(self.name))
            error(cmd + "\n")
            exit(1)
        else:
            print("switch {} has been started.".format(self.name))
