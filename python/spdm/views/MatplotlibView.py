import collections.abc
from io import BytesIO
import typing

import matplotlib.pyplot as plt

from ..utils.logger import logger
from .View import View


@View.register("matplotlib")
class MatplotlibView(View):
    def __init__(self, *args,  **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def display(self, *objs, **kwargs) -> typing.Any:

        fig, axis = plt.subplots()

        if len(objs) == 1 and isinstance(objs[0], collections.abc.Sequence):
            objs = objs[0]

        for obj in objs:
            if isinstance(obj, tuple):
                obj, opts = obj
            else:
                opts = {}

            if hasattr(obj, "plot"):
                axis = obj.plot(axis, **opts)
            else:
                logger.error(f"Can not plot {obj}")

        axis.set_aspect('equal')
        axis.axis('scaled')
        axis.set_xlabel(kwargs.pop("xlabel", ""))
        axis.set_ylabel(kwargs.pop("ylabel", ""))

        fig.suptitle(kwargs.pop("title", ""))
        fig.align_ylabels()
        fig.tight_layout()

        pos = axis.get_position()

        fig.text(pos.xmax+0.01, 0.5*(pos.ymin+pos.ymax), self.signature,
                 verticalalignment='center', horizontalalignment='left',
                 fontsize='small', alpha=0.2, rotation='vertical')

        res = "<Nothing to show />"

        schema = kwargs.pop("schema", self._schema)

        if schema is "html":
            buf = BytesIO()
            fig.savefig(buf, format='svg', transparent=True)
            buf.seek(0)
            res = buf.getvalue().decode('utf-8')
            plt.close(fig)
            return res
        else:
            return fig
