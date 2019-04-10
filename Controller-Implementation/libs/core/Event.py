"""
Simple event system
"""

from collections import defaultdict
import traceback
import threading
from libs.Exceptions import EventNotFound, HandlerNotFound


class Event:

    events = defaultdict(list)
    activated = False

    # use RLock instead of Lock to allow Events that trigger Events
    lock = threading.RLock()

    @staticmethod
    def activate():
        """
        Activate event system
        No event will be triggered before system is activated
        :return:
        """
        Event.activated = True

    @staticmethod
    def deactivate():
        """
        Deactivate event system
        No event will be triggered afterwards
        :return:
        """
        Event.activated = False
        Event.events = defaultdict(list)

    @staticmethod
    def on(event = None, *handlers):
        """
        Add new event handler
        :param event: event name
        :param handlers: handlers to be executed when event gets triggered
        :return:
        """
        Event.events[event].extend(handlers)

    @staticmethod
    def off(event=None, *handlers):
        """
        Remove handlers from event
        :param event:
        :param handlers:
        :return:
        """
        if not event:
            Event.events.clear()
            return

        if event not in Event.events:
            raise EventNotFound(event)

        if not handlers:
            Event.events.pop(event)
            return

        for cb in handlers:
            if cb not in Event.events.get(event):
                raise HandlerNotFound(event, cb)
            while cb in Event.events.get(event):
                Event.events.get(event).remove(cb)

    @staticmethod
    def async_trigger(event, *args, **kw):
        Event.trigger(event, *args, **kw)

    @staticmethod
    def trigger(event, *args, **kw):
        """
        Trigger an event. The corresponding handlers will be executed
        :param event: event name
        :param args: arguments without key
        :param kw: arguments with key
        :return:
        """

        if not Event.activated:
            return

        callbacks = list(Event.events.get(event, []))

        if not callbacks:
            return False

        # lock this method in order to prevent writing issues
        Event.lock.acquire()
        for cb in callbacks:
            try:
                cb(*args, **kw)
            except TypeError as e:
                Event.trigger('log_to_input', str=str((traceback.format_exc())))
            except Exception as e:
                Event.trigger('log_to_input', str=str((traceback.format_exc())))

        # release this method
        Event.lock.release()
        return True
