

from spdm.utils.logger import logger
from spdm.core.entity import Entity


class Bundle(Entity):
    """同类 Actor 的合集

    Args:
        Pluggable (_type_): _description_
        SpTree (_type_): _description_
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
