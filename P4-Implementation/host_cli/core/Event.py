"""
Simple event system
"""

from collections import defaultdict
#from core.Log import Log
import traceback


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


class Event:

    events = defaultdict(list)
    activated = False

    @staticmethod
    def activate():
        """
        Activate event system
        No event will be triggered before system is activated
        :return:
        """
        #Log.info("Event-System activated")
        Event.activated = True

    @staticmethod
    def deactivate():
        """
        Deactivate event system
        No event will be triggered afterwards
        :return:
        """
        #Log.info("Event-System deactivated")
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

        for cb in callbacks:
            try:
                cb(*args, **kw)
            except TypeError as e:
                cb(*args)
            except Exception as e:
                Event.trigger('log_to_output', str=str((traceback.format_exc())))


        return True


