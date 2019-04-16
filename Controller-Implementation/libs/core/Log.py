"""
This module enables log functionality inside the CLI
"""

import datetime
from libs.core.Event import Event
from libs.Configuration import Configuration
import os

class Log:
    """
    Define simple info, debug and error output
    """
    log_file = "logs/event.log"
    log_dir = "logs"

    @staticmethod
    def info(*args):
        Log.echo('[I]' + ' ' + ' '.join(map(str, args)))

    @staticmethod
    def async_info(*args):
        Event.trigger('log_to_output', str=('[I]' + ' ' + ' '.join(map(str, args))))

    @staticmethod
    def debug(*args):
        if Configuation.get("debug"):
            Log.echo('[D]' + ' ' + ' '.join(map(str, args)))

    @staticmethod
    def async_debug(*args):
        if Configuration.get("debug"):
            Event.trigger('log_to_output', str=('[D]' + ' ' + ' '.join(map(str, args))))

    @staticmethod
    def event(*args):
        if not os.path.exists(Log.log_dir):
            os.makedirs(Log.log_dir)
        f = open(Log.log_file, "a")
        f.write(str(datetime.datetime.now()) + ' ' + ' '.join(map(str, args)) + "\r\n")

    @staticmethod
    def error(*args):
        Log.echo('[E]' + ' ' + ' '.join(map(str, args)))

    @staticmethod
    def echo(msg):
        Event.trigger('log_to_input', str=(str(msg)))
