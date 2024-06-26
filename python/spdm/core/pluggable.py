import inspect
import typing

from abc import ABC, abstractmethod

from ..utils.logger import logger
from ..utils.sp_export import sp_load_module, walk_namespace_modules


class Pluggable:
    """Factory class to create objects from a registry."""

    _plugin_registry = {}

    @classmethod
    def _complete_path(cls, plugin_name) -> str | None:
        """Return the complete name of the plugin."""
        return getattr(cls, "_plugin_prefix", cls.__module__) + f".{plugin_name}" if plugin_name is not None else None

    @classmethod
    def register(cls, plugin_name: str | list | None = None, plugin_cls=None):
        """
        Decorator to register a class to the registry.
        """
        if plugin_cls is not None:
            if not isinstance(plugin_name, list):
                plugin_name = [plugin_name]

            for name in plugin_name:
                if not isinstance(name, str):
                    continue
                cls._plugin_registry[cls._complete_path(name)] = plugin_cls

        else:

            def decorator(o_cls):
                cls.register(plugin_name, o_cls)
                return o_cls

            return decorator

    def __new__(cls, plugin_name=None) -> typing.Type[typing.Self]:
        if plugin_name is None:
            # default __new__
            return super().__new__(cls)

        elif cls is Pluggable:
            # Can not create instance of Pluggable
            raise RuntimeError(f"Can not create instance of Pluggable!")

        elif not issubclass(cls, Pluggable):
            # Not pluggable
            logger.error(f"{cls.__name__} is not pluggable!")
            raise RuntimeError(f"{cls.__name__} is not pluggable!")

        # Check if the plugin path is provided
        plugin_path = cls._complete_path(plugin_name)

        if plugin_path is None or plugin_path == cls.__module__ or plugin_path == getattr(cls, "_plugin_prefix", None):
            # No plugin path provided, return the class itself
            return super(Pluggable, cls).__new__(cls)

        # Check if the plugin is already registered
        n_cls = cls._plugin_registry.get(plugin_path, None)

        if n_cls is None:
            # Plugin not found in the registry
            # 尝试从 PYTHON_PATH 中查找 module, 如果找到，将其注册到 _plugin_registry
            path = plugin_path.split(".")
            path = path[0:1] + ["plugins"] + path[1:]

            sp_load_module(".".join(path))

            # 重新检查
            n_cls = cls._plugin_registry.get(plugin_path, None)

        if not (inspect.isclass(n_cls) and issubclass(n_cls, cls)):
            # Plugin not found in the registry
            raise ModuleNotFoundError(f"Can not find module '{plugin_path}' as subclass of '{cls.__name__}'! [{n_cls}]")

        # Return the plugin class
        return super(Pluggable, cls).__new__(n_cls)

    @classmethod
    def _find_plugins(cls) -> typing.Generator[None, None, str]:
        """Find all plugins in the Python path."""
        yield from cls._plugin_registry.keys()
        for p in walk_namespace_modules(cls._complete_path()):
            if p not in cls._plugin_registry:
                yield p
