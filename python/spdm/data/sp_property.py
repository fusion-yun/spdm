"""
定义一个property, 要求其所在的class必须有一个_as_child方法，用于将其转换为type_hint 指定的类型。
    ```python
        class Foo(Dict):
            pass

        class Doo(Dict):

            f0 = sp_property(type_hint=Foo)      # 优先级最高, 不兼容IDE的类型提示

            f1: Foo = sp_property()              # 推荐，可以兼容IDE的类型提示

            ######################################################
            @sp_property
            def f3(self) -> Foo:                 # 用于定义f3的getter操作，与@property.getter类似
                'This is  f3!'
                return self.get("f3", {})

            @f3.setter
            def f3(self,value)->None:            # 功能与@property.setter  类似, NOT IMPLEMENTED YET!!
                self._entry.put("f3",value)

            @f3.deleter
            def f3(self)->None:                  # 功能与@property.deleter 类似, NOT IMPLEMENTED YET!!
                self._entry.child("f3").erase()
            ######################################################
                                                 # 完整版本
            def get_f4(self,default={})->Foo:
                return self.get("f4", default)

            def set_f4(self,value)->None:
                return self.set("f4", value)

            def del_f4(self,value)->None:
                return self.set("f4", value)

            f4 = sp_property(get_f4,set_f4,del_f4,"I'm f4",type_hint=Foo)
        ```

"""

from __future__ import annotations

import collections.abc
import inspect
import typing
from _thread import RLock
from spdm.data.Entry import Entry

from .Entry import open_entry
from .HTree import HTree
from ..utils.tags import _not_found_
from ..utils.logger import logger
from ..utils.tags import _not_found_
from ..utils.typing import PrimaryType
from ..utils.tree_utils import merge_tree_recursive
from .HTree import Dict

_T = typing.TypeVar("_T")


class SpDict(Dict[_T]):
    """  支持 sp_property 的 Dict  """

    def __init__(self, cache: typing.Any = None, /, entry: Entry | None = None, parent: HTree | None = None, **kwargs) -> None:

        if isinstance(cache, dict):
            pass
        elif cache is None or cache is _not_found_:
            cache = {}
        elif entry is None and isinstance(cache, Entry):
            entry = cache
            cache = {}
        elif entry is None:
            entry = open_entry(cache)
            cache = {}
        else:
            raise ValueError(f"Invalid arguments! cache={(cache)} entry={entry}")

        attrs = vars(self.__class__)

        for k in [*kwargs.keys()]:
            if k in attrs:
                cache[k] = merge_tree_recursive(cache.get(k, None), kwargs.pop(k))

        super().__init__(cache, entry=entry, parent=parent, **kwargs)

    def __get_property__(self, key: str, *args, **kwargs) -> HTree[_T] | _T | PrimaryType:
        return self._get(key, *args, **kwargs)

        # if value is _not_found_:
        #     raise KeyError(f"Can not find property \"{key}\" of {self.__class__.__name__}")
        # return value

    def __set_property__(self, key: str,  value: typing.Any = None, **kwargs) -> None: self.update(key, value)

    def __del_property__(self, key: str, **kwargs): self._remove(key)


class sp_property(typing.Generic[_T]):
    """
    用于为 SpPropertyClass 类（及其子类）定义一个property, 并确保其类型为type_hint 指定的类型。

    例如：
    ``` python
        class Foo(SpPropertyClass):
            # 方法一
            @sp_property
            def a(self) -> float: return 128

            # 方法二
            @sp_property(coordinate1="../psi")
            def dphi_dpsi(self) -> Profile[float]: return self.a*2

            # 方法三
            phi: Profile[float] = sp_property(coordinate1="../psi")

    ```
    方法二、三中参数 coordinate1="../psi"，会在构建 Profile时传递给构造函数  Profile.__init__。

    方法三 会在创建class 是调用 __set_name__,
           会在读写property phi 时调用 __set__,__get__ 方法，
           从Node的_cache或_entry获得名为 'phi' 的值，将其转换为 type_hint 指定的类型 Profile[float]。

    """

    def __init__(self,
                 getter: typing.Callable[[typing.Any], typing.Any] = None,
                 setter=None,
                 deleter=None,
                 type_hint: typing.Type = None,
                 doc: typing.Optional[str] = None,
                 strict: bool = False,
                 default_value=_not_found_,
                 ** metadata):
        """
            Parameters
            ----------
            getter : typing.Callable[[typing.Any], typing.Any]
                用于定义属性的getter操作，与@property.getter类似
            setter : typing.Callable[[typing.Any, typing.Any], None]
                用于定义属性的setter操作，与@property.setter类似
            deleter : typing.Callable[[typing.Any], None]
                用于定义属性的deleter操作，与@property.deleter类似
            type_hint : typing.Type
                用于指定属性的类型
            doc : typing.Optional[str]
                用于指定属性的文档字符串
            strict : bool
                用于指定是否严格检查属性的值是否已经被赋值
            metadata : typing.Any
                用于传递给构建  Node.__init__ 的参数


        """

        self.lock = RLock()

        self.getter = getter
        self.setter = setter
        self.deleter = deleter
        if doc is not None:
            self.__doc__ = doc

        self.property_cache_key: str = getter if isinstance(getter, str) else None
        self.property_name: str = None
        self.type_hint = type_hint
        self.strict = strict
        self.default_value = default_value
        self.metadata = metadata

    def __call__(self, func) -> sp_property[_T]:
        """ 用于定义属性的getter操作，与@property.getter类似 """
        self.getter = func
        return self

    def __set_name__(self, owner, name):
        # TODO：
        #    若 owner 是继承自具有属性name的父类，则默认延用父类sp_property的设置

        self.property_name = name
        self.metadata.setdefault("name", name)
        if self.__doc__ is not None:
            pass
        elif callable(self.getter):
            self.__doc__ = self.getter.__doc__
        else:
            self.__doc__ = f"sp_roperty:{self.property_name}"

        if self.property_cache_key is None:
            self.property_cache_key = name

        if self.property_name != self.property_cache_key:
            logger.warning(
                f"The property name '{self.property_name}' is different from the cache '{self.property_cache_key}''.")

    def _get_desc(self, owner_cls, name: str = None, metadata: dict = None):

        if self.type_hint is not None:
            return self.type_hint, self.metadata

        type_hint = None

        if inspect.isfunction(self.getter):
            type_hint = self.getter.__annotations__.get("return", None)
        else:
            t_hints = typing.get_type_hints(owner_cls)
            type_hint = t_hints.get(name, None)

        if type_hint is None:
            #  @ref: https://stackoverflow.com/questions/48572831/how-to-access-the-type-arguments-of-typing-generic?noredirect=1
            orig_class = getattr(self, "__orig_class__", None)
            if orig_class is not None:
                child_cls = typing.get_args(self.__orig_class__)
                if child_cls is not None and len(child_cls) > 0 and inspect.isclass(child_cls[0]):
                    type_hint = child_cls[0]

        self.type_hint = type_hint

        if metadata is None:
            metadata = self.metadata

        for base in owner_cls.__bases__:
            attr = getattr(base, name, None)
            if isinstance(attr, sp_property):
                metadata.update(attr.metadata)

        self.metadata = metadata

        return self.type_hint, self.metadata

    def __set__(self, instance:  SpDict[_T], value: typing.Any):
        assert (instance is not None)

        type_hint, metadata = self._get_desc(instance.__class__, self.property_name, self.metadata)

        if self.property_name is None or self.property_cache_key is None:
            logger.warning("Cannot use sp_property instance without calling __set_name__ on it.")

        with self.lock:
            instance.__set_property__(
                self.property_cache_key,
                value=value,
                setter=self.setter)

    def __get__(self, instance:  SpDict[_T] | None, owner=None) -> _T | sp_property[_T]:
        if instance is None:
            # 当调用 getter(cls, <name>) 时执行
            return self
        elif not isinstance(instance, SpDict):
            raise TypeError(f"Class '{instance.__class__.__name__}' must be a subclass of 'SpPropertyClass'.")

        # 当调用 getter(obj, <name>) 时执行

        type_hint, metadata = self._get_desc(owner, self.property_name, self.metadata)

        if self.property_name is None or self.property_cache_key is None:
            logger.warning("Cannot use sp_property instance without calling __set_name__ on it.")

        with self.lock:

            value = instance.__get_property__(self.property_cache_key,
                                              type_hint=type_hint,
                                              getter=self.getter,
                                              default_value=self.default_value,
                                              metadata=metadata,
                                              strict=self.strict,)

            if self.strict and value is _not_found_:
                raise AttributeError(
                    f"The value of property '{owner.__name__ if owner is not None else 'none'}.{self.property_name}' is not assigned!")

        return value

    def __delete__(self, instance: SpDict[_T]) -> None:
        with self.lock:
            instance.__del_property__(self.property_cache_key, deleter=self.deleter)
