"""
This module defines all thrown Exceptions
"""


class LinkNotFound(Exception):
    """
    Links are associated with names and numbers
    """
    def __init__(self, name, id):
        self.name = name
        self.id = id

    def __str__(self):
        return "Link {} in domain {} not found".format(self.name, self.id)


class DeviceNotFound(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Device {} not found".format(self.name)


class DomainNotFound(Exception):
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return "Domain {} not found".format(self.id)


class NextHopNotFound(Exception):
    def __init__(self, start, dest, domain):
        self.start = start
        self.dest = dest
        self.domain = domain

    def __str__(self):
        return "NextHop from {} to {} not found for domain {}. Maybe the path is not yet learned or there is no path inside this domain".format(start, dest, domain)


class EntryNotFound(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Table entry {} not found".format(self.name)


class TableNotFound(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Table {} not found. Did you initialize it?".format(self.name)


class TableManagerNotFound(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "TableManager {} not found.".format(self.name)


class ConfigurationNotFound(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Configuration {} not found".format(self.name)


class EventNotFound(Exception):

    def __init__(self, event):
        self.event = event

    def __str__(self):
        return "Event {} not found".format(self.event)


class HandlerNotFound(Exception):

    def __init__(self, event, handler):
        self.event = event
        self.handler = handler

    def __str__(self):
        return "Event {} does not have a handler {}".format(self.event, self.handler)


class SwitchConnectionFailed(Exception):

    def __init__(self, name, port):
        self.name = name
        self.port = port

    def __str__(self):
        return "Connection to switch {} on port {} was not successful. \n Try restarting the switches and check the configuration.".format(self.name, self.port)
