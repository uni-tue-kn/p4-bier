from scapy.all import *
import sys, os

TYPE_BIER = 0xBB00
TYPE_IPV4 = 0x0800

class BIER(Packet):
    name = "BIER"
    fields_desc = [
        LongField("BitString", 0),
        XShortField("Proto", 0)
    ]

    def mysummary(self):
        return self.sprintf("BitString=%BitString%, Proto=%Proto%")

bind_layers(Ether, BIER, type=TYPE_BIER)
bind_layers(IP, BIER, proto=0x8F)
bind_layers(BIER, IP, Proto=TYPE_IPV4)