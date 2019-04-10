"""
This module enables log functionality inside the CLI
"""

from termcolor import colored
import datetime
from prompt_toolkit.document import Document
from core.Event import Event
from prompt_toolkit import print_formatted_text
from filelock import Timeout, FileLock


class Log:
    """
    Define simple info, debug and error output
    """

    log_level = 3
    log_kat = "all"
    log_file = "logs/event.log"

    @staticmethod
    def info(*args):
        if Log.log_level > 1:
            Log.echo('[I]' + ' ' + ' '.join(map(str, args)))

    @staticmethod
    def async_info(*args):
        if Log.log_level > 1:
            Event.trigger('log_to_output', str=("\n" + ' '.join(map(str, args))))

    @staticmethod
    def debug(*args):
        if Log.log_level > 2:
            Log.echo('[D]' + ' ' + ' '.join(map(str, args)))

    @staticmethod
    def event(*args):
        f = open(Log.log_file, "a")
        f.write(str(datetime.datetime.now()) + ' ' + ' '.join(map(str, args)) + "\r\n")

    @staticmethod
    def error(*args):
        Log.echo('[E]' + ' ' + ' '.join(map(str, args)))

    @staticmethod
    def echo(msg):
        Event.trigger('log_to_input', str=(str(msg)))

    @staticmethod
    def log_to_file(*args, **kwargs):
        file = kwargs.get('file', "log_file.txt")
        lock = FileLock(str(file) + ".lock")

        with lock:
            open(file, "a").write(' '.join(map(str, args)))
