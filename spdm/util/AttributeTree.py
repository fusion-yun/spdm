from collections.abc import Mapping
import pprint
import copy


class _NEXT_TAG_:
    pass


_next_ = _NEXT_TAG_()
_last_ = -1


class AttributeTree:
    def __init__(self, data=None, *args,  default_factory=None, **kwargs):
        super().__init__()
        # collections.defaultdict(default_factory or self.__class__)
        self.__dict__['__data__'] = data if data is not None else NotImplemented
        self.__dict__['__default_factory__'] = default_factory or AttributeTree

    def __missing__(self, key):
        return self.__data__.setdefault(key, self.__default_factory__())

    def __repr__(self):
        #     return f"<{self.__class__.__name__}>"

        # def __str__(self):
        if isinstance(self.__data__, list):
            return pprint.pformat(self.__data__)
        else:
            return pprint.pformat({k: v for k, v in self.__data__.items()})

    def __copy__(self):
        return AttributeTree(copy.copy(self.__data__))

    def __deepcopy__(self, memo=None):
        return AttributeTree(copy.deepcopy(self.__data__, memo))

    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
        else:
            self.__setitem__(key, value)

    def __getattr__(self, key):
        # res = getattr(self, key)
        if key.startswith('_'):
            res = self.__dict__[key]
        else:
            res = self.__getitem__(key)
        return res

    def __delattr__(self, key):
        return self.__data__.__delitem__(key)

    def __getitem__(self, key):
        if isinstance(key, str):
            res = self.__as_object__().__getitem__(key)
        elif key is _next_:
            res = self.__push_back__()
        elif type(key) in (int, slice, tuple):
            res = self.__as_array__()[key]

        return res if res is not NotImplemented else self.__missing__(key)

    def __setitem__(self, key, value):
        if isinstance(value, Mapping):
            self.__delitem__(key)
            self.__getitem__(key).__update__(value)
        elif isinstance(key, str):
            self.__as_object__().__setitem__(key, value)
        elif type(key) in (int, slice, tuple):
            self.__as_array__()[key] = value
        elif key is _next_:
            self.__push_back__(value)
        else:
            raise TypeError(f"Illegal key type! {type(key)}")

    def __delitem__(self, key):
        try:
            del self.__data__[key]
        except KeyError:
            pass

    def __contain__(self, key):
        if isinstance(key, str):
            return key in self.__data__
        elif type(key) is int:
            return key < len(self.__data__)
        else:
            raise KeyError(key)

    def __len__(self):
        return len(self.__data__)

    def __iter__(self):
        if isinstance(self.__data__,  Mapping):
            for k, v in self.__data__.items():
                yield k, v
        else:
            for v in self.__data__:
                yield v

    def __as_object__(self):
        if isinstance(self.__data__, collections.abc.Mapping):
            pass
        elif self.__data__ is NotImplemented:
            self.__data__ = self.__default_factory__()
        else:
            raise TypeError(f"Can not create 'object': node is not empty! ")

        return self.__data__

    def __as_array__(self):
        if isinstance(self.__data__, list):
            pass
        elif self.__data__ is NotImplemented:
            self.__dict__['__data__'] = list()
        else:
            raise TypeError(f"Can not create 'list': node is not empty! ")

        return self.__data__

    def __push_back__(self, value=None):
        self.__as_array__().append(value or self.__default_factory__())
        idx = len(self.__data__)-1
        return idx, self.__data__[idx]

    def __pop_back__(self):
        if not isinstance(self.__data__, list):
            raise IndexError(f"Can push data to 'Object' ")
        self.__data__.pop()

    def __update__(self, other):
        if not isinstance(self.__data__, Mapping) or not isinstance(other, Mapping):
            raise TypeError(f"Not supported operator! update({type(self.__data__)},{type(other)})")
        else:
            obj = self.__as_object__()
            for k, v in other.items():
                if k in obj and isinstance(obj[k], AttributeTree):
                    obj[k].__update__(v)
                elif v is not None:
                    obj[k] = v

    def __or__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        new = self.__class__(self)
        new.__update__(other)
        return new

    def __ror__(self, other):
        if not isinstance(other, dict):
            return NotImplemented
        new = self.__class__(self)
        new.__update__(self)
        return new

    def __ior__(self, other):
        self.__update__(other)
        return self


class Foo(AttributeTree):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.foo(*args, **kwargs)

    def foo(self, *args, **kwargs):
        print(self.__data__)


if __name__ == "__main__":
    a = Foo()
    a.b.c.d = 5
    # pprint.pprint(a)

    # pprint.pprint(a.b.f)
    a.foo()

    _, d = a.b.f.__push_back__()
    d.text = "hellow world"
    a.b.f.__push_back__(5)

    a.g.h = {"b": 1, "z": {"t": 1}}
    # pprint.pprint(a)

    pprint.pprint(a.g.h)

    a.g.h |= {"y": 5, "z": {"x": 6}}

    pprint.pprint(a.g.h)

    pprint.pprint(a)
    pprint.pprint(len(a.b.f))

    # @property
    # def entry(self):
    #     return LazyProxy(self)
    # class __lazy_proxy__:
    #     @staticmethod
    #     def put(obj, path, value, *args, **kwargs):
    #         if len(path) == 0:
    #             raise KeyError("Empty path")
    #         for idx, p in enumerate(path[:-1]):
    #             if isinstance(obj, AttributeTree):
    #                 obj = obj.setdefault(p, AttributeTree())
    #             elif not isinstance(p, str) and isinstance(obj, list):
    #                 obj = obj[p]
    #             else:
    #                 raise KeyError(".".join(path[:idx+1]))
    #         if hasattr(obj, path[-1]):
    #             setattr(obj, path[-1], value)
    #         else:
    #             obj[path[-1]] = value

    #         # if len(path) > 0:
    #         #     raise path

    #         return None

    #     @staticmethod
    #     def get(obj, path,  *args, **kwargs):
    #         if len(path) == 0:
    #             return obj

    #         for idx, p in enumerate(path):
    #             if isinstance(obj, AttributeTree):
    #                 obj = obj.get(p, None)
    #             elif isinstance(obj, list):
    #                 try:
    #                     obj = obj[p]
    #                 except IndexError:
    #                     obj = None
    #             else:
    #                 obj = getattr(obj, p, None)

    #             if obj is None:
    #                 raise KeyError(f"Illegal path '{'.'.join(path[:idx+1])}'! ")

    #         return obj

    #     @staticmethod
    #     def get_value(data, path, *args, **kwargs):
    #         return AttributeTree.__lazy_proxy__.get(data, path, *args, **kwargs)

    #     @staticmethod
    #     def delete(data,  path, *args, **kwargs):
    #         if len(path) > 1:
    #             obj = AttributeTree.__lazy_proxy__.get(data, path[:-1], *args, **kwargs)
    #         else:
    #             obj = data
    #         if hasattr(obj, path[-1]):
    #             delattr(obj, path[-1])
    #         else:
    #             del obj[path[-1]]

    #     @staticmethod
    #     def push_back(data,  path, value, *args, **kwargs):
    #         # if len(path) == 0:
    #         #     data.push_back(value)
    #         # else:
    #         # data.get(path).setdefault(path[-1], []).append(value)
    #         if len(path) > 0:
    #             obj = AttributeTree.__lazy_proxy__.get(data, path[:-1]).setdefault(path[-1], [])
    #         else:
    #             obj = data

    #         obj.append(value or AttributeTree())
    #         return path+[len(obj)-1]

    #     @staticmethod
    #     def count(data,  path, *args, **kwargs):
    #         obj = AttributeTree.__lazy_proxy__.get(data, path, *args, **kwargs)
    #         return len(obj)

    #     @staticmethod
    #     def contains(data,  path, v, *args, **kwargs):
    #         obj = AttributeTree.__lazy_proxy__.get(data, path, *args, **kwargs)
    #         return v in obj

    #     @staticmethod
    #     def iter(data,  path, *args, **kwargs):
    #         for obj in AttributeTree.__lazy_proxy__.get(data, path, *args, **kwargs):
    #             if type(obj) in (int, float, str):
    #                 yield obj
    #             else:
    #                 yield LazyProxy(obj)

    #     @staticmethod
    #     def call(data, path, *args, **kwargs):
    #         obj = AttributeTree.__lazy_proxy__.get(data, path)
    #         if callable(obj):
    #             return obj(*args, **kwargs)
    #         elif len(args)+len(kwargs) == 0:
    #             return obj
    #         else:
    #             raise TypeError(f"{obj.__class__.__name__} is not callable")
