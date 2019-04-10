"""
Simple Configuration system for save controller options
"""
import json
from prettytable import PrettyTable
from libs.Exceptions import ConfigurationNotFound
from libs.core.Event import Event


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
        Configuration.load_config(vars(args).get("config"))

    @staticmethod
    def load(config):
        """
        Load configuration from configuration json
        """
        with open(config) as d_file:
            data = json.load(d_file)

        return data

    @staticmethod
    def load_config(config):
        """
        Load configuration from configuration json
        """
        with open(config) as d_file:
            data = json.load(d_file)

        for key in data:
            Configuration.set(key, data[key])

    @staticmethod
    def show_all():
        """
        Show current configuration
        :return:
        """
        data = PrettyTable()

        data.field_names = ["Name", "Value"]

        for key, value in Configuration.settings.iteritems():
            if key == "switches":
                value = "Switch-Array - Omitted due to length"
            data.add_row([key, value])

        Event.trigger('log_to_input', str=(str(data)))
