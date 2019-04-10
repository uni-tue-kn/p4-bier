import sys
import socket
import random

from scapy.all import sendp, send, get_if_list, get_if_hwaddr
from scapy.all import Packet
from scapy.all import Ether, IP, UDP, TCP

from core.Log import Log
from core.Network import Network

class Send:

    @staticmethod
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

    @staticmethod
    def main(to, text):

        addr = socket.gethostbyname(to)
        next_hop = Network.get_default_gateway_linux()


        iface = Send.get_if()

        #print "sending on interface %s to %s" % (iface, str(addr))
        pkt =  Ether(src=get_if_hwaddr(iface), dst='33:33:33:33:33:33')
        pkt = pkt /IP(dst=addr) / TCP(dport=1234, sport=random.randint(49152,65535)) / str(text)
        #pkt.show2()
        sendp(pkt, iface=iface, verbose=False)

        Log.info("Send packet with payload", str(text), "to ip", str(addr))


