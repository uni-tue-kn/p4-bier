import socket
from scapy.all import sendp, get_if_hwaddr
from scapy.all import Ether, IP, UDP, TCP
from scapy.contrib.igmp import IGMP
from core.Log import Log
from core.Network import Network


class Subscribe(object):

    @staticmethod
    def sub(m_addr):
        addr = socket.gethostbyname(Network.get_default_gateway_linux())
        mc_addr = socket.gethostbyname(m_addr)
        iface = Network.get_if()

        # print "sending on interface %s to %s" % (iface, str(addr))
        pkt = Ether(src=get_if_hwaddr(iface), dst='00:00:00:00:01:01')
        pkt = pkt / IP(dst=addr) / IGMP(type=0x16, gaddr=mc_addr)

        sendp(pkt, iface=iface, verbose=False)

        Log.info("Subscribed to", str(mc_addr))



