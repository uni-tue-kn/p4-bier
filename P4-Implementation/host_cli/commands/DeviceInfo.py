from core.Network import Network
from core.Log import Log

class DeviceInfo:

    @staticmethod
    def info():
        ip = Network.get_ip_address()
        mac = Network.get_mac_address()

        Log.info("IP:", ip, "MAC:", mac)

