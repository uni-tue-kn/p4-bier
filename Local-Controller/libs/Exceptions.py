"""
This module defines all thrown Exceptions
"""


class DeviceNotFound(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Device {} not found".format(self.name)


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
