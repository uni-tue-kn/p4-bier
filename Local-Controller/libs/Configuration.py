"""
Simple Configuration system for save controller options
"""
from prettytable import PrettyTable
from libs.core.Log import Log
from libs.Exceptions import ConfigurationNotFound


class Configuration:
    """
    This class implements a simple configuration system
    using a key value storage
    """
    settings = {}

    @staticmethod
    def get(name):
        """
        Get configuration with given name
        If name is not a valid configuration name, a
        ConfigurationNotFound exception will be raised
        :param name: configuration name
        :return:
        """
        value = Configuration.settings.get(name, None)

        if value is None:
            raise ConfigurationNotFound(name)

        return value

    @staticmethod
    def set(name, value):
        """
        Set a configuration with name and value
        :param name: name of the configuration
        :param value: value of the configuration
        :return:
        """
        Configuration.settings[name] = value

    @staticmethod
    def init(args):
        """
        Initialize configuration based on command line arguments
        :param args: command line arguments
        :return:
        """
        for arg in vars(args):
            Configuration.set(arg, vars(args).get(arg))
