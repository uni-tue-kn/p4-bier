#!/usr/bin/env python
import argparse
import sys
import socket
import random
import struct

from scapy.all import sendp, send, get_if_list, get_if_hwaddr
from scapy.all import Packet
from scapy.all import Ether, IP, UDP, TCP
from scapy.contrib.igmp import IGMP

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

def get_default_gateway_linux():
    """Read the default gateway directly from /proc."""
    with open("/proc/net/route") as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                continue

            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))

def main():

    addr = socket.gethostbyname(get_default_gateway_linux())
    mc_addr = socket.gethostbyname(sys.argv[2])
    iface = get_if()

    if sys.argv[1] == "subscribe":
        igmp_type = 0x16
    else:
        igmp_type = 0x17

    #print "sending on interface %s to %s" % (iface, str(addr))
    pkt =  Ether(src=get_if_hwaddr(iface), dst='00:00:00:00:01:01')
    pkt = pkt / IP(dst=addr) / IGMP(type=igmp_type, gaddr=mc_addr)

    sendp(pkt, iface=iface, verbose=False)
    
    if igmp_type == 0x16:
        print "Subscribed to " + str(mc_addr)

    if igmp_type == 0x17:
        print "Unsubscribed from " + str(mc_addr)
    


if __name__ == '__main__':
    main()
