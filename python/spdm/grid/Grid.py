import typing
from functools import cached_property

from spdm.geometry.GeoObject import GeoObject

from ..geometry.GeoObject import GeoObject
from ..utils.logger import logger
from ..utils.Pluggable import Pluggable
from ..utils.typing import NumericType, ScalarType


class Grid(Pluggable):

    _plugin_registry = {}

    @classmethod
    def __dispatch__init__(cls, _grid_type, self, *args, **kwargs) -> None:
        if _grid_type is None or len(_grid_type) == 0:
            _grid_type = kwargs.get("grid_type", None)

            if _grid_type is None:
                _grid_type = [RegularGrid]
            elif isinstance(_grid_type, str):
                _grid_type = [_grid_type,
                              f"spdm.grid.{_grid_type}Grid#{_grid_type}Grid",
                              f"spdm.grid.{_grid_type}Mesh#{_grid_type}Mesh"
                              f"spdm.grid.{_grid_type.capitalize()}Grid#{_grid_type.capitalize()}Grid",
                              f"spdm.grid.{_grid_type.capitalize()}Mesh#{_grid_type.capitalize()}Mesh"
                              ]

        super().__dispatch__init__(_grid_type, self, *args, **kwargs)

    def __init__(self, *args, **kwargs) -> None:
        if self.__class__ is Grid:
            return Grid.__dispatch__init__(None, self, *args, **kwargs)
        self._uv_points = args
        self._geometry: GeoObject = kwargs.get("geometry", None)

        self._appinfo = kwargs
        self._appinfo.setdefault("grid_type", self.__class__.__name__)
        self._appinfo.setdefault("units", ["-"])

    @property
    def name(self) -> str: return self._appinfo.get("name", 'unamed')

    @property
    def units(self) -> typing.List[str]: return self._appinfo.get("units", ["-"])

    @property
    def geometry(self) -> GeoObject: return self._geometry
    """ Geometry of the grid  网格的几何形状  """

    @property
    def uv_points(self) -> typing.Tuple[NumericType]: return self._uv_points

    @cached_property
    def points(self) -> typing.Tuple[NumericType]:
        """ 网格点坐标 """
        return self._uv_points if self._geometry is None else self._geometry.points(*self._uv_points)

    def interpolator(self, y: NumericType, *args, **kwargs) -> typing.Callable[..., NumericType] | NumericType:
        raise NotImplementedError(f"{self.__class__.__name__}.interpolator")

    def derivative(self, y: NumericType, *args, **kwargs) -> typing.Callable[..., NumericType] | NumericType:
        raise NotImplementedError(f"{self.__class__.__name__}.derivative")

    def antiderivative(self, y:  NumericType, *args, **kwargs) -> typing.Callable[..., NumericType] | NumericType:
        raise NotImplementedError(f"{self.__class__.__name__}.antiderivative")

    def integrate(self, y:  NumericType, *args, **kwargs) -> ScalarType:
        raise NotImplementedError(f"{self.__class__.__name__}.integrate")


@Grid.register([None, 'regular', 'null'])
class RegularGrid(Grid):
    """Regular/Null Grid
        ------
        - Null  也无坐标点坐标, 无几何形状信息，
        - Normal 存储坐标点坐标，没有额外的几何形状信息
    """
    pass


def as_grid(*args, **kwargs) -> Grid:
    if len(args) == 1 and isinstance(args[0], Grid):
        if len(kwargs) > 0:
            logger.warning(f"Ignore kwargs {kwargs}")
        return args[0]
    else:
        return Grid(*args, **kwargs)
