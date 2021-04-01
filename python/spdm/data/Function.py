from functools import cached_property

import numpy as np
from numpy.lib.function_base import piecewise
from scipy import constants
import scipy.interpolate
from scipy.interpolate.interpolate import PPoly

from ..util.logger import logger
from .Quantity import Quantity

# if version.parse(scipy.__version__) <= version.parse("1.4.1"):
#     from scipy.integrate import cumtrapz as cumtrapz
# else:
#     from scipy.integrate import cumulative_trapezoid as cumtrapz

logger.debug(f"Using SciPy Version: {scipy.__version__}")


class PimplFunc(object):
    def __init__(self, *args,    is_periodic=False, ** kwargs) -> None:
        super().__init__()
        self._is_periodic = is_periodic

    @property
    def is_periodic(self):
        return self._is_periodic

    @property
    def x(self) -> np.ndarray:
        return NotImplemented

    @property
    def y(self) -> np.ndarray:
        return self.apply(self.x)

    def apply(self, x=None) -> np.ndarray:
        return NotImplemented

    @cached_property
    def derivative(self):
        return NotImplemented

    @cached_property
    def antiderivative(self):
        return NotImplemented

    def invert(self, x=None):
        x = self.x if x is None else x
        return PimplFunc(self.apply(x), x)

    def pullback(self, *args, **kwargs):
        if len(args) == 0:
            raise ValueError(f"missing arguments!")
        elif len(args) == 2 and args[0].shape == args[1].shape:
            x0, x1 = args
            y = self.apply(x0)
        elif isinstance(args[0], Function) or callable(args[0]):
            logger.warning(f"FIXME: not complete")
            x1 = args[0](self.x)
            y = self.apply(self.x)
        elif isinstance(args[0], np.ndarray):
            x1 = args[0]
            y = self.apply(x1)
        else:
            raise TypeError(f"{args}")

        return Function(x1, y, is_periodic=self.is_periodic)


class SplineFunction(PimplFunc):
    def __init__(self, *args, is_periodic=False,  ** kwargs) -> None:
        super().__init__(is_periodic=is_periodic)

        if len(args) == 0 or len(args) > 2:
            raise NotImplementedError(f"Illegal input {[type(a) for a in args]}")
        elif len(args) == 1 and isinstance(args[0], PPoly):
            self._ppoly = args[0]
        else:
            x = args[0]
            y = args[1]
            if callable(y):
                y = y(x)
            elif isinstance(x, np.ndarray) and isinstance(y, np.ndarray):
                assert(x.shape == y.shape)
            elif isinstance(y, (float, int)):
                y = np.full(len(x), y)
            else:
                raise NotImplementedError(f"Illegal input {[type(a) for a in args]}")

            self._x = x

            if self.is_periodic:
                self._ppoly = scipy.interpolate.CubicSpline(x, y, bc_type="periodic", **kwargs)
            else:
                self._ppoly = scipy.interpolate.CubicSpline(x, y, **kwargs)

    @property
    def x(self) -> np.ndarray:
        return self._ppoly.x

    @cached_property
    def derivative(self):
        return SplineFunction(self._ppoly.derivative())

    @cached_property
    def antiderivative(self):
        return SplineFunction(self._ppoly.antiderivative())

    def apply(self, x=None) -> np.ndarray:
        x = self.x if x is None else x
        return self._ppoly(x)


class PiecewiseFunction(PimplFunc):
    def __init__(self, x, cond, func, *args,    **kwargs) -> None:
        super().__init__(**kwargs)
        self._x = x
        self._cond = cond
        self._func = func

    @property
    def x(self) -> np.ndarray:
        return self._x

    def apply(self, x=None) -> np.ndarray:
        cond = [c(x) for c in self._cond]
        return np.piecewise(x, cond, self._func)


class Function(np.ndarray):
    @staticmethod
    def __new__(cls,  *args,   **kwargs):
        if cls is not Function:
            return object.__new__(cls, *args, **kwargs)
        else:
            if len(args) == 1 and isinstance(args[0], Function):
                pimpl = args[0]._pimpl
                obj = pimpl.apply(*args[1:], **kwargs)
                x = pimpl.x
            elif len(args) >= 2 and isinstance(args[1], Function):
                pimpl = args[1]._pimpl
                obj = pimpl.apply(args[0], *args[2:], **kwargs)
                x = args[0]
            elif len(args) >= 2 and isinstance(args[1], PimplFunc):
                pimpl = args[1]
                obj = pimpl.apply(args[0], *args[2:], **kwargs)
                x = args[0]
            elif len(args) > 2:
                pimpl = PiecewiseFunction(*args, **kwargs)
                obj = pimpl.y
                x = pimpl.x
            else:
                pimpl = SplineFunction(*args, **kwargs)
                obj = pimpl.y
                x = pimpl.x

            obj = obj.view(cls)
            obj._pimpl = pimpl
            obj._x = x
            return obj

    def __array_finalize__(self, obj):
        self._pimpl = getattr(obj, '_pimpl', None)
        self._x = getattr(obj, '_x', None)

    def __array_ufunc__(self, ufunc, method, *inputs,   **kwargs):

        x = next(d.x for d in inputs if isinstance(d, Function))

        def wrapp(d):
            if x is not None and isinstance(d, Function) and d.x is not x:
                d = d(x)
            return d.view(np.ndarray) if isinstance(d, np.ndarray) else d

        inputs = [wrapp(in_) for in_ in inputs]

        if method != "__call__":
            return super().__array_ufunc__(ufunc, method, *inputs, **kwargs)
        else:
            return super(Function, self).__array_ufunc__(ufunc, method, *inputs, **kwargs)

    def __init__(self, *args, **kwargs):
        pass

    def __getitem__(self, key):
        d = super().__getitem__(key)
        if isinstance(d, np.ndarray) and len(d.shape) > 0:
            d.view(Function)
            d._pimpl = self._pimpl
            d._x = self._x[key]
        return d

    @property
    def is_periodic(self):
        return self._pimpl.is_periodic

    @property
    def x(self):
        return self._x

    @cached_property
    def derivative(self):
        return Function(self._x, self._pimpl.derivative)

    @cached_property
    def antiderivative(self):
        return Function(self._x, self._pimpl.antiderivative)

    @cached_property
    def invert(self):
        return Function(*self._pimpl.invert(self._x))

    def pullback(self, *args, **kwargs):
        if len(args) == 0:
            args = [self._x]
        return Function(self._pimpl.pullback(*args, **kwargs))

    def integrate(self, a=None, b=None):
        return self._pimpl.integrate(a or self.x[0], b or self.x[-1])

    def __call__(self,   *args, **kwargs):
        if len(args) == 0:
            args = [self._x]
        return self._pimpl.apply(*args, **kwargs)
