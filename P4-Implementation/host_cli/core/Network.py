from scapy.all import get_if_list, get_if_hwaddr, get_if_addr
import socket
import struct


class Network:
    @staticmethod
    def get_if():
        ifs = get_if_list()
        iface = None  # "h1-eth0"
        for i in get_if_list():
            if "eth0" in i:
                iface = i
                break;
        if not iface:
            print "Cannot find eth0 interface"
            exit(1)
        return iface

    @staticmethod
    def get_default_gateway_linux():
        """Read the default gateway directly from /proc."""
        with open("/proc/net/route") as fh:
            for line in fh:
                fields = line.strip().split()
                if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                    continue

                return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))

    @staticmethod
    def get_ip_address():
        iface = Network.get_if()

        return get_if_addr(iface)

    @staticmethod
    def get_mac_address():
        iface = Network.get_if()

        return get_if_hwaddr(iface)