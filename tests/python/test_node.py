import unittest
from copy import copy, deepcopy

import numpy as np
from spdm.util.logger import logger
from spdm.data import Dict, List, Node, Link, Path, Query


class Foo(Dict):
    def __init__(self,   *args, **kwargs):
        super().__init__(*args, **kwargs)


class TestNode(unittest.TestCase):
    data = {
        "a": [
            "hello world {name}!",
            "hello world2 {name}!",
            1.0, 2, 3, 4
        ],
        "c": "I'm {age}!",
        "d": {
            "e": "{name} is {age}",
            "f": "{address}"
        }
    }

    def test_new(self):
        self.assertTrue(isinstance(Node("hello"), Node))
        self.assertTrue(isinstance(Node(1), Node))
        self.assertTrue(isinstance(Node(np.ones([10, 20])), Node))
        self.assertTrue(isinstance(Node([1, 2, 3, 4, 5]), List))
        self.assertTrue(isinstance(Node((1, 2, 3, 4, 5)), List))
        self.assertTrue(isinstance(Node({"a": 1, "b": 2, "c": 3}), Dict))
        self.assertFalse(isinstance(Node({1, 2, 3, 4, 5}), List))

    # def test_create(self):
    #     cache = []
    #     d = Node(cache)
    #     self.assertEqual(d.create_child("hello"), "hello")
    #     self.assertEqual(d.create_child(1), 1)
    #     v = np.ones([10, 20])
    #     self.assertIs(d.create_child(v), v)
    #     self.assertTrue(isinstance(d.create_child("hello", always_node=True), Node))

    #     self.assertTrue(isinstance(d.create_child([1, 2, 3, 4, 5]), List))
    #     self.assertTrue(isinstance(d.create_child((1, 2, 3, 4, 5)), List))
    #     self.assertTrue(isinstance(d.create_child({"a": 1, "b": 2, "c": 3}), Dict))

    def test_find_by_key(self):

        d = Dict[Node](self.data)

        self.assertEqual(len(d["a"]),                     6)
        self.assertEqual(d["c"].value,             self.data["c"])
        self.assertEqual(d["d"]["e"].value,   self.data["d"]["e"])
        self.assertEqual(d["d"]["f"].value,   self.data["d"]["f"])
        self.assertEqual(d["a", 0].value,       self.data["a"][0])
        self.assertEqual(d["a", 1].value,       self.data["a"][1])
        self.assertEqual(d["a", 2:6].value,        [1.0, 2, 3, 4])

    def test_dict_insert(self):
        cache = {}

        d = Dict(cache)

        d["a"] = "hello world {name}!"

        self.assertEqual(cache["a"], "hello world {name}!")

        d["e"]["f"] = 5
        d["e"]["g"] = 6
        self.assertEqual(cache["e"]["f"], 5)
        self.assertEqual(cache["e"]["g"], 6)

    def test_dict_update(self):
        cache = deepcopy(self.data)
        d = Dict(cache)

        d.update({"d": {"g": 5}})

        self.assertEqual(cache["d"]["e"], "{name} is {age}")
        self.assertEqual(cache["d"]["f"], "{address}")
        self.assertEqual(cache["d"]["g"], 5)

    def test_node_del(self):
        cache = {
            "a": [
                "hello world {name}!",
                "hello world2 {name}!",
                1, 2, 3, 4
            ]
        }

        d = Node(cache)

        del d["a"]

        self.assertTrue("a" not in cache)

    def test_node_append(self):
        d = List()
        d.append({"a": 1, "b": 2})

        self.assertEqual(len(d), 1)
        self.assertEqual(d[0]["a"].value, 1)
        self.assertEqual(d[0]["b"].value, 2)

    # def test_node_insert(self):
    #     cache = {"this_is_a_cache": True}

    #     d = Dict(cache)

    #     d["a"] = "hello world {name}!"
    #     self.assertEqual(cache["a"], "hello world {name}!")

    #     d["c"] .append(1.23455)
    #     d["c"] .append({"a": "hello world", "b": 3.141567})

    #     self.assertEqual(cache["c"][0],  1.23455)

    def test_child_type_convert_list(self):

        cache = [{"a": 1234}, {"b": 1234}, {"c": 1234}, {"d": 1234}]

        d = List[Foo](cache)

        self.assertFalse(isinstance(cache[1], Foo))
        self.assertTrue(isinstance(d[1], Foo))
    #     self.assertTrue(isinstance(cache[1], Foo))

    def test_chain_mapping(self):
        cache = {"a": 1234, "b": 1234, "c": 12343, "d": 12345}
        d = Dict(cache, a=5, b=4)
        self.assertEqual(d["a"], 5)
        self.assertEqual(d["b"], 4)

        self.assertEqual(d["c"], cache["c"])
        self.assertEqual(d["d"], cache["d"])

#     # def test_node_boolean(self):
#     #     d = Dict()
#     #     self.assertTrue(d.empty)
#     #     self.assertTrue(d["a"] or 12.3, 12.3)


if __name__ == '__main__':
    unittest.main()