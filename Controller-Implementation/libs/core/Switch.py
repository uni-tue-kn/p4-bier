"""
This module represents a switch.
"""

from libs.core.Device import Device


class Switch(Device):
    def __init__(self, name=None, ip=None, mac=None, bfr_id=None):
        """
        Initialize switch with name, ip, mac and bfr_id
        :param name: name of the swithc
        :param ip: ip of the switch
        :param mac: mac of the switch
        :param bfr_id: bfr_id for domain 0, all other ids in different domains will be set automaticly
        """
        super(self.__class__, self).__init__(name=name, ip=ip, mac=mac)
        self._domain_id_mapping = {0: bfr_id}

    def get_bfr_id(self, domain):
        """
        Get bfr_id for a given domain
        :param domain: domain identifier
        :return: bfr_id
        """
        return self._domain_id_mapping.get(domain, -1)

    def set_bfr_id(self, domain, id):
        """
        Set the bfr id for a given domain
        :param domain: domain for which id should be set
        :param id: bfr id
        :return:
        """
        self._domain_id_mapping[domain] = id

    def get_bfr_mapping(self):
        """
        Get the domain bfr mapping
        :return:
        """
        return self._domain_id_mapping

    def reset_bfr_mapping(self):
        """
        Reset the domain id mapping
        only set default domain id
        :return:
        """
        self._domain_id_mapping = {0: self._domain_id_mapping.get(0)}

    def get_type(self):
        return "Switch"

    def __str__(self):
        return self.get_type() + "(" + self._name + ", " + self._ip + ", " + \
               str(self._mac) + ", " + \
               str(self._device_to_port) + ")" + " " + str(self._domain_id_mapping)
