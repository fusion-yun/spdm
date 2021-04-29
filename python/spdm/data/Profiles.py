import collections

import numpy as np
from spdm.data.AttributeTree import AttributeTree
from spdm.data.Function import Function
from spdm.data.Node import Dict, Node
from spdm.util.logger import logger


class Profiles(AttributeTree):
    __slots__ = ("_axis",)

    def __init__(self,   *args, axis=None, default_factory=None, ** kwargs):
        if axis is None:
            axis = np.linspace(0, 1.0, 128)
        elif isinstance(axis, np.ndarray):
            axis = axis.view(np.ndarray)
        else:
            raise TypeError(type(axis))

        if default_factory is None:
            def default_factory(value, *_args, axis=axis, **_kwargs):
                if isinstance(value, Function):
                    if value.x is not axis:
                        value = Function(axis, value.viewe(np.ndarray))
                elif isinstance(value, (int, float)) or callable(value):
                    value = Function(self._axis, value)
                elif isinstance(value, np.ndarray):
                    if value.shape != axis.shape:
                        raise ValueError(f"The shape of arrays dismatch! {value.shape} !={axis.shape} ")
                    value = Function(axis, value)
                return value
        self._axis = axis
        super().__init__(*args, default_factory=default_factory, **kwargs)

    @property
    def axis(self):
        return self._axis