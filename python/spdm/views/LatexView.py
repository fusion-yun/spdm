import collections.abc
import typing
from io import BytesIO
from spdm.data.Expression import Expression, Variable
from spdm.data.Functor import Functor
from spdm.data.Function import Function
import matplotlib.pyplot as plt
import numpy as np


from spdm.utils.logger import logger
from spdm.utils.typing import array_type
from spdm.views.View import View

_EXPR_OP_NAME = {
    "negative": "-",
    "add": "+",
    "subtract": "-",
    "multiply": "*",
    "matmul": "*",
    "true_divide": "/",
    "power": "^",
    "equal": "==",
    "not_equal": "!",
    "less": "<",
    "less_equal": "<=",
    "greater": ">",
    "greater_equal": ">=",
    "add": "+",
    "subtract": "-",
    "multiply": "*",
    "matmul": "*",
    "divide": "/",
    "power": "^",
    # "abs": "",
    "positive": "+",
    # "invert": "",
    "bitwise_and": "&",
    "bitwise_or": "|",

    # "bitwise_xor": "",
    # "right_shift": "",
    # "left_shift": "",
    # "right_shift": "",
    # "left_shift": "",
    "mod": "%",
    # "floor_divide": "",
    # "floor_divide": "",
    # "trunc": "",
    # "round": "",
    # "floor": "",
    # "ceil": "",
}
# fmt:off
_EXPR_OP_LATEX = {
    "negative":         ("-",       0),
    "positive":         ("+",       0),
    "add":              ("+",       1),
    "subtract":         ("-",       1),
    "multiply":         ("\\cdot", 2),
    "matmul":           ("\\cdot", 2),
    "divide":           ("/",       2),    
    "true_divide":      ("/",       2),
    "power":            ("^",       3),
    "equal":            ("==",      0),
    "not_equal":        ("!",       0),
    "less":             ("<",       0),
    "less_equal":       ("<=",      0),
    "greater":          (">",       0),
    "greater_equal":    (">=",      0),


    # "abs":            ("",1),

    # "invert":         ("",1),
    "bitwise_and":      ("&",       0),
    "bitwise_or":       ("|",       0),

    # "bitwise_xor": "",
    # "right_shift": "",
    # "left_shift": "",
    # "right_shift": "",
    # "left_shift": "",
    "mod": "%",
    # "floor_divide": "",
    # "floor_divide": "",
    # "trunc": "",
    # "round": "",
    # "floor": "",
    # "ceil": "",
}
# fmt:on


@View.register(["Latex", "latex"])
class LatexView(View):
    backend = "latex"

    def __init__(self, *args,   **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def render(self, expr: typing.Any, *args, **kwargs) -> str:
        return f"$${self._render(expr, *args, **kwargs)[0]}$$"

    def _render(self, expr: typing.Any, *args, parent: int = None, **kwargs) -> typing.Tuple[str, int]:

        level = 10

        if isinstance(expr, np.ndarray):
            res = f"<{expr.shape}>"

        elif np.isscalar(expr):
            res = f"{expr}"

        elif isinstance(expr, Variable):
            res = expr.__label__
            level = 10

        elif isinstance(expr, Function):
            res, level = self._render_function(expr, *args, parent=parent, **kwargs)

        elif isinstance(expr, Expression) and isinstance(expr._func, Functor) and isinstance(expr._func._func, np.ufunc):
            res, level = self._render_ufunc(expr, *args, parent=parent, **kwargs)

        elif isinstance(expr, Expression) and isinstance(expr._func, Functor):
            res, level = self._render_expr(expr, *args, parent=parent, **kwargs)

        else:
            res = str(expr)

        if parent is not None and parent > level:
            res = f"\\left({res}\\right)"

        return res, level

    def _render_function(self, func: Function, *args, **kwargs) -> typing.Tuple[str, int]:
        return func.__label__, 0

    def _render_ufunc(self, expr: Expression, *args, **kwargs) -> typing.Tuple[str, int]:
        op: np.ufunc = expr._func._func

        if expr._func._method != "__call__" and expr._func._method is not None:
            raise NotImplementedError(f"op={expr._func._func} method={expr._func._method}")

        children = expr._children
        n_children = len(children)

        tag, level = _EXPR_OP_LATEX.get(op.__name__, (None, 10))

        if n_children != 2 or tag is None:
            res = f"{op.__name__}({', '.join([self._render(child)[0] for child in  children])})"

        elif op.__name__ in ("true_divide", "divide"):
            res = f"\\frac{{{self._render(children[0],parent=level)[0]}}}{{{self._render(children[1])[0]}}}"

        else:
            res = f"{self._render(expr._children[0],parent=level)[0]} {tag} {self._render(expr._children[1],parent=level)[0]} "

        return res, level

    def _render_expr(self, expr: Expression, *args, parent=None, **kwargs) -> typing.Tuple[str, int]:
        return f"{expr._func.__label__}\\left({', '.join([self._render(child, *args, parent=None,**kwargs)[0] for child in  expr._children])}\\right)", 0
