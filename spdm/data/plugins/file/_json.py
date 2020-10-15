'''IO Plugin of JSON '''
import json
import pathlib

import numpy

from spdm.data.DataEntry import DataEntry
from spdm.util.logger import logger

from .file import FileEntry

__plugin_spec__ = {
    "name": "json",
    "filename_pattern": ["*.json"],
    "support_data_type": [int, float, str, dict, list],
    "filename_extension": "json"

}


# class ndArrayEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, numpy.ndarray):
#             return obj.tolist()
#         # Let the base class default method raise the TypeError
#         return json.JSONEncoder.default(self, obj)


class JSONEntry(FileEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read(self, *args, **kwargs):
        with self.open(mode="r") as fid:
            res = json.load(fid)
        return res

    def write(self, d, *args, **kwargs):
        with self.open(mode="w") as fid:
            json.dump(d, fid)


__SP_EXPORT__ = JSONEntry