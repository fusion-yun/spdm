import collections
import json

import numpy as np
from spdm.data.Entry import Entry
from spdm.data.File import File
from spdm.util.dict_util import as_native
from spdm.util.logger import logger


class JSONFile(File):
    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fid = None

    def open(self) -> File:
        super().open()
        try:
            self._fid = open(self.path,  mode=self.mode_str)
        except OSError as error:
            raise FileExistsError(f"Can not open file {self.path}! {error}")
        else:
            logger.debug(
                f"Open {self.__class__.__name__} File {self.path} mode={self.mode}")
        return self

    def close(self):
        if self._fid is not None:
            self._fid.close()
            self._fid = None
        return super().close()

    def read(self, *args,   **kwargs) -> Entry:
        if not hasattr(self, "_fid"):
            self.open()
        return Entry(json.load(self._fid))

    def write(self,   d, *args,  **kwargs):
        json.dump(as_native(d, enable_ndarray=False), self._fid)


__SP_EXPORT__ = JSONFile
