from libs.core.Log import Log
from libs.Exceptions import DeviceNotFound


class TopologyManager:

    topology = {'total': 0, 'devices': [], 'domains': []}
    cluster = 3

    @staticmethod
    def exists_device(name=None):
        """
        Checks whether a given device exists
        :param name: name of device
        :return: boolean
        """
        for dev in TopologyManager.topology['devices']:
            if dev['name'] == name:
                return True

        return False

    @staticmethod
    def add_device(name=None, domain=0, device=None):
        """
        Adds an deice to the device list
        :param name: name of the device
        :param domain: corresponding domain, default-domain 0
        :param device: device, e.g. Host or Switch object
        :return: void
        """
        if not TopologyManager.exists_device(name):
            TopologyManager.topology['devices'].append({'name': name, 'domain': [domain], 'device': device})

        TopologyManager.topology['total'] = len(TopologyManager.topology['devices'])

    @staticmethod
    def get_device(name=None):
        """
        Get device by name
        :param name: name of the device
        :return: device
        """
        for dev in TopologyManager.topology['devices']:
            if dev['name'] == name:
                return dev['device']

        raise DeviceNotFound(name)

    @staticmethod
    def get_device_by_ip(ip=None):
        """
        Return device with given ip
        :param ip: ip of device
        :return:
        """
        for dev in TopologyManager.topology['devices']:
            device = dev['device']

            if device.get_ip() == ip:
                return device

        raise DeviceNotFound(ip)
