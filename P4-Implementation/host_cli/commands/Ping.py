import sys
import socket
import random
import time
from scapy.all import sendp, send, get_if_list, get_if_hwaddr
from scapy.all import Packet
from scapy.all import Ether, IP, UDP, TCP
from scapy.config import conf

from core.Log import Log
from core.Network import Network

class Ping:

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
    def main(to, to_sec, text, count):

        addr = socket.gethostbyname(to)
        addr_2 = socket.gethostbyname(to_sec)
        next_hop = Network.get_default_gateway_linux()


        iface = Ping.get_if()

        s = conf.L2socket(iface=iface)

        #print "sending on interface %s to %s" % (iface, str(addr))
        pkt1 =  Ether(src=get_if_hwaddr(iface), dst='33:33:33:33:33:33')
        pkt1 = pkt1 /IP(dst=addr) / UDP(dport=1234, sport=random.randint(49152,65535)) / str(text)
        pkt2 =  Ether(src=get_if_hwaddr(iface), dst='33:33:33:33:33:33')
        pkt2 = pkt2 /IP(dst=addr_2) / UDP(dport=1234, sport=random.randint(49152,65535)) / str(text)
        #pkt.show2()

        for i in range(int(count)):
            s.send(pkt1)
            time.sleep(0.03)
            s.send(pkt2)
            time.sleep(0.03)
            #Log.log_to_file(round((time.time() * 1000) % 1000000), 1, "\r\n", file="logs/host_2.txt")


        Log.info("Send ping with payload", str(text), "to ip", str(addr))
