#!/usr/bin/env python
import argparse
import sys
import socket
import random
import struct

from scapy.all import sendp, send, get_if_list, get_if_hwaddr
from scapy.all import Packet
from scapy.all import Ether, IP, UDP, TCP
from header.TopologyDiscoveryPacket import *
import time


def get_if():
    ifs=get_if_list()
    iface=None # "h1-eth0"
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break;
    if not iface:
        print "Cannot find eth0 interface"
        exit(1)
    return iface

def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]

def main():

    while True:
        try:
            iface = get_if()

            print(type(get_if_addr(iface)))

            pkt =  Ether(src=get_if_hwaddr(iface), dst='00:00:00:00:00:00')
            pkt =  pkt / TopologyDiscovery(identifier=int(get_if_addr(iface).split(".")[3]), port=1, ip=get_if_addr(iface), mac=get_if_hwaddr(iface)) / "host"
            pkt.show2()
            sendp(pkt, iface=iface, verbose=False)
        except Exception as e:
            pass

        time.sleep(2)


if __name__ == '__main__':
    main()
