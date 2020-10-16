import collections
import pathlib

import numpy as np

try:
    from lxml.etree import _Element as XMLElement
    from lxml.etree import ParseError as XMLParseError
    from lxml.etree import XPath as XPath

    from lxml.etree import parse as parse_xml
    _HAS_LXML = True
except ImportError:
    from xml.etree.ElementTree import Element as XMLElement
    from xml.etree.ElementTree import ParseError as XMLParseError
    from xml.etree.ElementTree import parse as parse_xml
    XPath = str
    _HAS_LXML = False


from spdm.util.LazyProxy import LazyProxy
from spdm.util.logger import logger

from ..Document import Document
from ..Handler import Handler, Holder, Request


def merge_xml(first, second):
    if first is None or second is None or first.tag != second.tag:
        return

    for child in second:
        id = child.attrib.get("id", None)
        if id is not None:
            target = first.find(f"{child.tag}[@id='{id}']")
        else:
            target = first.find(child.tag)
        if target is not None:
            merge_xml(target, child)
        else:
            first.append(child)


def load_xml(path, *args,  mode="r", **kwargs):
    # TODO: add handler non-local request ,like http://a.b.c.d/babalal.xml
    if isinstance(path, str):
        # o = urisplit(uri)
        path = pathlib.Path(path)

    if isinstance(path, collections.abc.Sequence):
        root = load_xml(path[0], mode=mode)
        for fp in path[1:]:
            merge_xml(root, load_xml(fp, mode=mode))
        return root
    elif not isinstance(path, pathlib.Path) or not path.is_file():
        raise FileNotFoundError(path)

    try:
        root = parse_xml(path.as_posix()).getroot()
        logger.debug(f"Loading XML file from {path}")

    except XMLParseError as msg:
        raise RuntimeError(f"ParseError: {path}: {msg}")

    for child in root.findall("{http://www.w3.org/2001/XInclude}include"):
        fp = path.parent/child.attrib["href"]
        root.insert(0, load_xml(fp))
        root.remove(child)
    return root


class XMLHolder(Holder):
    def __init__(self, element,  *args,  **kwargs):
        if not isinstance(element, XMLElement):
            element = load_xml(element, *args,  **kwargs)

        super().__init__(element)


class XMLHandler(Handler):
    def __init__(self,  *args, envs=None, prefix=None,  **kwargs):
        super().__init__(*args, **kwargs)
        self._envs = envs or {}
        self._prefix = prefix or []

    def xpath(self, path):
        res = "."
        query = {}
        prefix = self._prefix
        prev = prefix[-1] if len(prefix) > 0 else None
        for p in path:
            if type(p) is int:
                res += f"[ @id='{p}' or position()= {p+1} or @id='*']"
            elif isinstance(p, str) and p[0] == '@':
                res += f"[{p}]"
            elif isinstance(p, str):
                res += f"/{p}"
            else:
                # TODO: handle slice
                raise TypeError(f"Illegal path type! {type(p)} {path}")
            prev = p

        if _HAS_LXML:
            res = XPath(res)
        return res

    def _convert(self, element, query={}, path=[],  lazy=True, projection=None,):
        if not isinstance(element, XMLElement):
            return element
        res = None

        if len(element) > 0 and lazy:
            res = LazyProxy(XMLHolder(element), handler=XMLHandler(
                prefix=self._prefix+path,
                envs={**query, **self._envs}))
        elif "dtype" in element.attrib or (len(element) == 0 and len(element.attrib) == 0):
            dtype = element.attrib.get("dtype", None)

            if dtype == "string" or dtype is None:
                res = [element.text]
            elif dtype == "int":
                res = [int(v) for v in element.text.split(',')]
            elif dtype == "float":
                res = [float(v) for v in element.text.split(',')]
            else:
                raise NotImplementedError(f"Not supported dtype {dtype}!")

            dims = [int(v) for v in element.attrib.get("dims", "").split(',') if v != '']
            if len(dims) == 0 and len(res) == 1:
                res = res[0]
            elif len(dims) > 0 and len(res) != 0:
                res = np.array(res).reshape(dims)
            else:
                res = np.array(res)
        else:
            res = {child.tag: self._convert(child, query=query, lazy=lazy) for child in element}
            for k, v in element.attrib.items():
                res[f"@{k}"] = v

            text = element.text.strip() if element.text is not None else None
            if text is None or len(text) == 0:
                pass
            elif "{" in text:
                try:
                    q = {}
                    prev = None
                    for p in (self._prefix + path):
                        if type(p) is int:
                            q[f"{prev}#id"] = p
                        prev = p
                    res["@text"] = text.format(**q, **query, **self._envs)
                except KeyError:
                    res["@text"] = text
            else:
                res["@text"] = text
        return res

    def put(self, holder, path, value, *args, **kwargs):
        if not only_one:
            return Request(path).apply(lambda p,  v=value, s=self, h=holder: s._push(h, p, v))
        else:
            raise NotImplementedError()

    def get(self, holder, path, *args, only_one=False, **kwargs):
        if not only_one:
            return Request(path).apply(lambda p: self.get(holder, p, only_one=True, **kwargs))
        else:
            return self._convert(self.xpath(path).evaluate(holder.data), path=path, **kwargs)

    def get_value(self, holder, path, *args,  only_one=False, **kwargs):
        if not only_one:
            return Request(path).apply(lambda p: self.get_value(holder, p, only_one=True, **kwargs))
        else:
            obj = self.xpath(path).evaluate(holder.data)
            if isinstance(obj, collections.abc.Sequence) and len(obj) > 0:
                obj = obj[0]

            return self._convert(obj, path=path, lazy=False, **kwargs)

    def iter(self, holder, path, *args, **kwargs):
        tree = holder.data
        for req in Request(path):
            for child in self.xpath(req).evaluate(tree):
                yield self._convert(child, path=req)


def open_xml(path, *args,  **kwargs):
    return Document(root=XMLHolder(path), handler=XMLHandler(*args,  **kwargs))


# def connect_xml(uri, *args, filename_pattern="{_id}.h5", handler=None, **kwargs):

#     path = pathlib.Path(getattr(uri, "path", uri))

#     Document(
#         root=XMLHolder(uri, mode=mode),
#         handler=XMLHandler()
#     )

#     return FileCollection(path, *args,
#                           filename_pattern=filename_pattern,
#                           document_factory=lambda fpath, mode:,
#                           **kwargs)


# __SP_EXPORT__ = connect_XML
