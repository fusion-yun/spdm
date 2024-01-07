"""
定义一个property, 要求其所在的class必须有一个_as_child方法，用于将其转换为type_hint 指定的类型。
    ```python
        class Foo(Dict):
            pass

        class Doo(Dict):

            f0 = SpProperty(type_hint=Foo)      # 优先级最高, 不兼容IDE的类型提示

            f1: Foo = SpProperty()              # 推荐，可以兼容IDE的类型提示

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
import pprint
import inspect
import typing
import collections.abc
from copy import deepcopy, copy
from _thread import RLock
from enum import Enum
from typing_extensions import Self

from .Entry import Entry
from .AoS import AoS
from .HTree import HTree, Dict, List, HTreeNode
from .Path import update_tree, merge_tree, Path
from .Expression import Expression
from ..utils.envs import SP_DEBUG
from ..utils.logger import logger, deprecated
from ..utils.tags import _not_found_


class SpTree(Dict[HTreeNode]):
    """支持 sp_property 的 Dict"""

    def __get_property__(self, _name: str, *args, **kwargs) -> SpTree:
        return self._find(_name, *args, **kwargs)

    def __set_property__(self, _name: str, value: typing.Any = None, *args, **kwargs) -> None:
        self._update(_name, value, *args, **kwargs)

    def __del_property__(self, _name: str, *args, **kwargs):
        self._remove(_name, *args, **kwargs)

    def __serialize__(self, dumper: typing.Callable[...] | bool = True) -> typing.Dict[str, typing.Any]:
        data = {}
        for k, prop in inspect.getmembers(self.__class__, lambda c: is_sp_property(c)):
            if prop.getter is not None:
                continue
            value = getattr(self, k, _not_found_)
            if value is _not_found_:
                continue
            # elif isinstance(value, Expression):
            #     value = value.__array__()

            data[k] = value

        return super()._do_serialize(data, dumper)

    def fetch(self, *args, _parent=_not_found_, **kwargs) -> Self:
        cache = {}

        for k, value in inspect.getmembers(self.__class__, lambda c: isinstance(c, SpProperty)):
            if getattr(value, "getter", None) is None:
                if (value := getattr(self, k, _not_found_)) is not _not_found_:
                    cache[k] = HTreeNode._do_fetch(value, *args, _parent=None, **kwargs)

        return self.__duplicate__(cache, _parent=_parent)


class PropertyTree(SpTree):
    def __getattr__(self, key: str, *args, **kwargs) -> PropertyTree | AoS:
        if key.startswith("_"):
            return super().__getattribute__(key)
        else:
            res = self.__get_property__(key, *args, _type_hint=None, **kwargs)
            if isinstance(res, dict):
                return PropertyTree(res, _parent=self)
            elif isinstance(res, list) and (len(res) == 0 or isinstance(res[0], (dict, HTree))):
                return AoS[PropertyTree](res, _parent=self)
            else:
                return res

    def __getitem__(self, *args, **kwargs):
        return self.__get_property__(*args, _type_hint=PropertyTree | None, **kwargs)

    def __setitem__(self, *args, **kwargs):
        return self.__set_property__(*args, **kwargs)

    def __delitem__(self, key: str):
        return self.__del_property__(key)

    def __iter__(self) -> typing.Generator[_T, None, None]:
        """遍历 children"""
        for v in self.children():
            yield v

    def dump(self, entry: Entry | None = None, force=False, quiet=True) -> Entry:
        if entry is None:
            return deepcopy(self._cache)
        else:
            entry.update(self._cache)
            return entry


_T = typing.TypeVar("_T")
_TR = typing.TypeVar("_TR")

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
            从Node的_cache或entry获得名为 'phi' 的值，将其转换为 type_hint 指定的类型 Profile[float]。
    """


class SpProperty:
    def __init__(
        self,
        getter: typing.Callable[[typing.Any], typing.Any] = None,
        setter=None,
        deleter=None,
        default_value: typing.Any = _not_found_,
        # type_hint: typing.Type = None,
        doc: str = None,
        strict: bool = False,
        **kwargs,
    ):
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
        self.default_value = default_value
        self.doc = doc or ""
        self.property_name: str = None
        self.strict = strict
        self.metadata = kwargs
        self.type_hint = None

    def __call__(self, func: typing.Callable[..., _TR]) -> _TR:
        """用于定义属性的getter操作，与@property.getter类似"""
        if self.getter is not None:
            raise RuntimeError(f"Can not reset getter!")
        self.getter = func
        return self

    def __set_name__(self, owner_cls, name: str):
        # TODO：
        #    若 owner 是继承自具有属性name的父类，则默认延用父类sp_property的设置
        self.property_name = name

        tp = None
        if callable(self.getter):
            tp = typing.get_type_hints(self.getter).get("return", None)

        if tp is None:
            try:
                tp = typing.get_type_hints(owner_cls).get(name, None)
            except Exception as error:
                logger.exception(owner_cls)
                raise error
            
        if tp is not None:
            self.type_hint = tp

        metadata = [
            getattr(getattr(base_cls, name, _not_found_), "metadata", _not_found_) for base_cls in owner_cls.__bases__
        ]

        self.metadata = merge_tree(*metadata, self.metadata)

        self.metadata["name"] = name

        if self.getter is not None:
            self.doc += self.getter.__doc__ or ""

        for base_cls in owner_cls.__bases__:
            prop = getattr(base_cls, name, _not_found_)
            if isinstance(prop, SpProperty):
                self.doc += prop.doc

            elif prop is not _not_found_:
                self.default_value = update_tree(self.default_value, prop)

        if self.doc == "":
            self.doc = f"{owner_cls.__name__}.{self.property_name}"

    def __set__(self, instance: SpTree, value: typing.Any) -> None:
        assert instance is not None

        if (alias := self.metadata.get("alias", _not_found_)) is not _not_found_:
            logger.warning(f"set proptery alias {self.property_name} => {alias}!")

        if self.property_name is None:
            logger.error("Can not use sp_property instance without calling __set_name__ on it.")

        with self.lock:
            instance.__set_property__(self.property_name, value, setter=self.setter)

    def __get__(self, instance: SpTree, owner_cls=None) -> _T:
        if instance is None:
            # 当调用 getter(cls, <name>) 时执行
            return self
        elif not isinstance(instance, SpTree):
            raise TypeError(f"Class '{instance.__class__.__name__}' must be a subclass of 'SpTree'.")

        with self.lock:
            if (alias := self.metadata.get("alias", _not_found_)) is not _not_found_:
                value = instance.__get_property__(
                    self.property_name,
                    _type_hint=self.type_hint,
                    _getter=self.getter,
                    default_value=_not_found_,
                    **self.metadata,
                )
                if value is not _not_found_:
                    value = instance.__get_property__(
                        alias,
                        _type_hint=self.type_hint,
                        _getter=self.getter,
                        default_value=self.default_value,
                        **self.metadata,
                    )
            else:
                value = instance.__get_property__(
                    self.property_name,
                    _type_hint=self.type_hint,
                    _getter=self.getter,
                    default_value=self.default_value,
                    **self.metadata,
                )

            if self.strict and value is _not_found_:
                raise AttributeError(
                    f"The value of property '{owner_cls.__name__ if owner_cls is not None else 'none'}.{self.property_name}' is not assigned!"
                )

        return value

    def __delete__(self, instance: SpTree) -> None:
        with self.lock:
            instance.__del_property__(self.property_name, deleter=self.deleter)


def sp_property(getter: typing.Callable[..., _T] | None = None, **kwargs) -> _T:
    if getter is None:
        return SpProperty(**kwargs)
    else:
        return SpProperty(getter=getter, **kwargs)


def is_sp_property(obj) -> bool:
    return isinstance(obj, SpProperty)


def _process_sptree(cls, **kwargs) -> typing.Type[SpTree]:
    if not inspect.isclass(cls):
        raise TypeError(f"Not a class {cls}")

    type_hints = typing.get_type_hints(cls)

    if not issubclass(cls, HTree):
        n_cls = type(cls.__name__, (cls, SpTree), {})
        n_cls.__module__ = cls.__module__
    else:
        n_cls = cls

    for _name, _type_hint in type_hints.items():
        prop = getattr(cls, _name, _not_found_)

        if isinstance(prop, property):
            continue
        elif isinstance(prop, SpProperty):
            if not (_name in cls.__dict__ and n_cls is cls):
                prop = SpProperty(getter=prop.getter, setter=prop.setter, deleter=prop.deleter, **prop.metadata)
        else:
            prop = SpProperty(default_value=prop)

        prop.type_hint = _type_hint

        setattr(n_cls, _name, prop)

        prop.__set_name__(n_cls, _name)

    setattr(n_cls, "_metadata", merge_tree(getattr(cls, "_metadata", {}), kwargs))

    return n_cls


def sp_tree(cls: _T = None, /, **kwargs) -> _T:
    # 装饰器，将一个类转换为 SpTree 类

    def wrap(_cls, _kwargs=kwargs):
        return _process_sptree(_cls, **_kwargs)

    if cls is None:
        return wrap
    else:
        return wrap(cls)
