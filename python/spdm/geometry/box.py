from __future__ import annotations
import numpy as np
from .geo_object import GeoObject
from .bbox import BBox
from ..core.typing import array_type
from ..utils.logger import logger


class Box(GeoObject):
    """ Box 矩形，n维几何体
    """

    def __init__(self, xmin, xmax,  **kwargs) -> None:
        xmin = np.asarray(xmin)
        xmax = np.asarray(xmax)
        super().__init__(ndim=len(xmin),  **kwargs)
        self._xmin = xmin
        self._xmax = xmax
        self._bbox = BBox(xmin, xmax-xmin)

    @property
    def bbox(self) -> BBox: return self._bbox

    @property
    def is_closed(self) -> bool: return True
    @property
    def is_convex(self) -> bool: return True

    def enclose(self, *args) -> bool | array_type:
        """ Return True if all args are inside the geometry, False otherwise. """
        res = self.bbox.enclose(*args)
        if not np.sum(res):
            logger.debug((res, args, self._bbox))
        return res
