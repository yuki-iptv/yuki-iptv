from typing import Optional
from abc import ABC
import logging

from pydbus.generic import signal

from .base import NAME, INTERFACE as MPRIS_INTERFACE


logger = logging.getLogger(__name__)

TRACE_LOG_LEVEL = 5


class MprisInterface(ABC):
    INTERFACE = MPRIS_INTERFACE

    PropertiesChanged = signal()

    def __init__(
      self,
      name: str = NAME,
      adapter: Optional['MprisAdapter'] = None
    ):
        self.name = name
        self.adapter = adapter

    def log_trace(self, *args, **kwargs):
        logger.log(TRACE_LOG_LEVEL, *args, **kwargs)
