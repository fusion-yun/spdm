from __future__ import annotations

import collections
import collections.abc
import pathlib
import typing

from ..utils.sp_export import sp_load_module
from ..utils.uri_utils import URITuple, uri_split
from .Connection import Connection
from .Entry import Entry
from ..utils.Plugin import Pluggable


class File(Connection):
    """
        File like object
    """

    @classmethod
    def _guess_plugin_name(cls, path, *args, **kwargs) -> typing.List[str]:

        n_cls_name = ''
        if "format" in kwargs:
            n_cls_name = kwargs.get("format")
        elif isinstance(path, collections.abc.Mapping):
            n_cls_name = path.get("$class", None)
        elif isinstance(path,   pathlib.PosixPath):
            n_cls_name = path.suffix[1:].upper()
        elif isinstance(path, (str, URITuple)):
            uri = uri_split(path)
            if isinstance(uri.format, str):
                n_cls_name = uri.format
            else:
                n_cls_name = pathlib.PosixPath(uri.path).suffix[1:].upper()
        if n_cls_name == ".":
            n_cls_name = ".text"

        #  f"{cls._plugin_prefix}{n_cls_name}#{n_cls_name}{cls.__name__}"

        return [f"spdm.plugins.data.Plugin{n_cls_name}#{n_cls_name}File"]

    def __init__(self,  *args,  ** kwargs): 
        if self.__class__ is File:
            Pluggable.__init__(self, *args, **kwargs)
            return
                      
        super().__init__(*args, **kwargs)

    @property
    def mode_str(self) -> str:
        return File.MOD_MAP.get(self.mode, "r")

    @property
    def entry(self) -> Entry:
        if self.is_readable:
            return self.read()
        else:
            return self.write()

    def read(self, lazy=False) -> Entry:
        if self._holder is None:
            self.open()
        return self._holder.read(lazy=lazy)

    def write(self, *args, **kwargs):
        if not self.is_open:
            self.open()
        self._holder.write(*args, **kwargs)

    def __enter__(self) -> File:
        return super().__enter__()

    def read(self, lazy=False) -> Entry:
        raise NotImplementedError()

    def write(self, data, lazy=False) -> Entry:
        raise NotImplementedError()


__SP_EXPORT__ = File
