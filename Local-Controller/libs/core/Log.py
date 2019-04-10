"""
This module enables log functionality inside the CLI
"""

from termcolor import colored
import datetime
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
            print(colored('[I]', 'green') + ' ' + ' '.join(map(str, args)))
            f = open(Log.log_file, "a")
            f.write(str(datetime.datetime.now()) + ' [I] ' + ' '.join(map(str, args)) + "\r\n")

    @staticmethod
    def debug(*args):
        if Log.log_level > 2:
            print(colored('[D]', 'yellow') + ' ' + ' '.join(map(str, args)))
            f = open(Log.log_file, "a")
            f.write(str(datetime.datetime.now()) + ' [D] ' + ' '.join(map(str, args)) + "\r\n")

    @staticmethod
    def event(*args):
        f = open(Log.log_file, "a")
        f.write(str(datetime.datetime.now()) + ' [Event] ' + ' '.join(map(str, args)) + "\r\n")

    @staticmethod
    def error(*args):
        print(colored('[E]', 'red') + ' ' + ' '.join(map(str, args)))
        f = open(Log.log_file, "a")
        f.write(str(datetime.datetime.now()) + ' [E] ' + ' '.join(map(str, args)) + "\r\n")

    @staticmethod
    def log_to_file(*args, **kwargs):
        file = kwargs.get('file', "log_file.txt")
        lock = FileLock(str(file) + ".lock")

        with lock:
            open(file, "a").write(' '.join(map(str, args)))
