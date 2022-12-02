import collections.abc
import pathlib
from copy import deepcopy
from enum import Flag, auto
from typing import Mapping, TypeVar, Union, Any
import functools
from ..util.logger import logger
from .Entry import Entry
from .SpObject import SpObject
from ..util.uri_utils import URITuple, uri_merge, uri_split

_TConnection = TypeVar('_TConnection', bound='Connection')


class Connection(SpObject):

    class Mode(Flag):
        read = auto()       # open for reading (default)
        write = auto()      # open for writing, truncating the file first
        create = auto()     # open for exclusive creation, failing if the file already exists
        append = auto()     # open for writing, appending to the end of the file if it exists
        temporary = auto()  # is temporary

    class Status(Flag):
        opened = auto()
        closed = auto()

    def __init__(self, uri, *args, mode=Mode.read, **kwargs):
        super().__init__()
        self._uri = uri_split(uri)
        self._mode = Connection.Mode(mode) if not isinstance(mode, Connection.Mode) else mode
        self._is_open = False

    def __del__(self):
        if self.is_open:
            self.close()

    def __repr__(self):
        return f"<{self.__class__.__name__} path={self.uri.path} protocol={self.uri.protocol} format={self.uri.format}>"

    @property
    def uri(self) -> URITuple:
        return self._uri

    @property
    def path(self) -> Any:
        return self.uri.path

    @property
    def mode(self) -> Mode:
        return self._mode

    @property
    def mode_str(self) -> str:
        return ''.join([(m.name[0]) for m in list(Connection.Mode) if m & self._mode])

    @property
    def is_readable(self) -> bool:
        return bool(self._mode & Connection.Mode.read)

    @property
    def is_writable(self) -> bool:
        return bool(self._mode & Connection.Mode.write)

    @property
    def is_temporary(self) -> bool:
        return bool(self._mode & Connection.Mode.temporary)

    @property
    def is_open(self) -> bool:
        return self._is_open

    def open(self) -> _TConnection:
        self._is_open = True
        return self

    def close(self) -> None:
        self._is_open = False
        return

    @property
    def entry(self) -> Entry:
        raise NotImplementedError()

    def __enter__(self) -> _TConnection:
        return self.open()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
