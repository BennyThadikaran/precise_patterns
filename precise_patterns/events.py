from pyee.base import EventEmitter

"""
This module provides a shared application-wide event emitter.

It exposes a single :class:`pyee.base.EventEmitter` instance
named :data:`event_bus`, which can be used to register and emit events
throughout the application.
"""
event_bus = EventEmitter()
