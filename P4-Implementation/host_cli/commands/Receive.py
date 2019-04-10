from scapy.all import *
import sys,os
from core.Log import Log
from core.Network import Network
import time
import datetime

class Receive(object):
    ifaces = filter(lambda i: 'eth' in i, os.listdir('/sys/class/net/'))

    @staticmethod
    def handle_pkt(pkt):
        iface = Receive.ifaces[0]

        if pkt[Ether].dst != Network.get_mac_address():
            return

        if not IP in pkt:
            return
            
        if str(pkt[IP].dst).startswith("10"):
            type = 1
        else:
            type = 3

        if (TCP in pkt and pkt[TCP].dport == 1234) or (UDP in pkt and pkt[UDP].dport == 1234):
            if TCP in pkt:
                Log.async_info("[" + str(datetime.datetime.now()) +"]", str(pkt[TCP].load))
            else:
                Log.async_info("[" + str(datetime.datetime.now()) +"]", str(pkt[UDP].load))

            id = int(get_if_addr(iface).split(".")[3])

            # type 1: packet in
            Log.log_to_file(round((time.time() * 1000) % 1000000), type, "\r\n", file="logs/host_"+str(id)+".txt")
            sys.stdout.flush()

    @staticmethod
    def main():
        ifaces = filter(lambda i: 'eth' in i, os.listdir('/sys/class/net/'))
        iface = ifaces[0]
        sys.stdout.flush()
        sniff(iface = iface,
              prn = lambda x: Receive.handle_pkt(x))
