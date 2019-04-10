"""
This class is used to distinguish between switches and hosts
"""

from libs.core.Device import Device


class Host(Device):

    def __init__(self, name=None, ip=None, mac=None):
        super(self.__class__, self).__init__(name=name, ip=ip, mac=mac)

    def get_type(self):
        return "Host"

