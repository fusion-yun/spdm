import logging
import pprint
import sys
import unittest
from spdm.util.numlib import constants
from spdm.util.numlib import np
from spdm.data.Function import Function
from spdm.util.logger import logger


class TestFunction(unittest.TestCase):
    def test_spl(self):
        x = np.linspace(0, 1.0, 128)
        y = np.sin(x*constants.pi*2.0)

        fun = Function(x, y, is_periodic=True)

        x2 = np.linspace(0, 1.0, 64)
        y2 = np.sin(x2*constants.pi*2.0)

        self.assertLess(np.mean((y2-fun(x2))**2), 1.0e-16)

    def test_operator(self):
        x = np.linspace(0, 1, 128)
        y = np.linspace(0, 2, 128)
        fun = Function(x, y)

        self.assertTrue(np.all(-fun == -y))
        self.assertTrue(np.all(fun + 2 == y + 2))
        self.assertTrue(np.all(fun - 2 == y - 2))
        self.assertTrue(np.all(fun * 2 == y * 2))
        self.assertTrue(np.all(fun / 2 == y / 2))
        self.assertTrue(np.all(fun ** 2 == y ** 2))
        # self.assertTrue(np.all(fun @ fun == y)

    def test_construct_from_expression(self):
        x = np.linspace(0, 1, 128)
        y = np.linspace(0, 2, 128)
        fun = Function(x, y*2)

        self.assertTrue(np.all(fun == y * 2))

    def test_np_fun(self):
        x = np.linspace(0, 1, 128)
        y = np.linspace(0, 2, 128)
        fun = Function(x, y, is_periodic=True)

        y2 = np.sin(fun)
        logger.debug(type(y2))


if __name__ == '__main__':
    unittest.main()
