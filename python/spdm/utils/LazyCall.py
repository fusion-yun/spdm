from __future__ import annotations

import typing
import collections.abc

_T = typing.TypeVar("_T")

class LazyCall(typing.Generic[]):

    def __init__(self, obj, handler: typing.Callable, path=[]):
        super().__init__()
        self._obj = obj
        self._handler = handler
        self._path = path

    def __append__(self, k) -> LazyCall:
        if isinstance(k, list):
            path = self._path+k
        elif isinstance(k, collections.abc.Sequence) and not isinstance(k, str):
            path = self._path+list(k)
        else:
            path = self._path+[k]

        return LazyCall[_T](self._obj, self._handler,  path)

    def __load__(self) -> _T:
        return self._handler(self._obj, self._path)

    def __getitem__(self, k) -> LazyCall:
        return self.__append__(k)

    def __getattr__(self, k) -> LazyCall:
        return self.__append__(k)

    def __call__(self, *args, **kwargs) -> typing.Any:
        return self.__load__()(*args, **kwargs)