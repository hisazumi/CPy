#!/usr/bin/env python

import unittest
from cpy import CPySingle, cpylayer, cpybase
from enum import Enum

PKG = 'testcpy'

class LayerEnum(Enum):
    L1 = 'l1'
    L2 = 'l2'

class CPy1(CPySingle):

    def __init__(self):
        self.reset()
        super(CPy1, self).__init__()

    def reset(self):
        self.base_called = False
        self.l1_called = False
        self.l2_called = False

    @cpybase
    def test(self):
        self.base_called = True

    @cpybase
    def skiptest(self):
        self.base_called = True

    @test.layer(LayerEnum.L1)
    def test_l1(self):
        self.l1_called = True


    @test.layer(LayerEnum.L2)
    def test_l2(self):
        self.l2_called = True
        self.proceed()


class CPy2(CPySingle):

    def __init__(self):
        self.reset()
        super(CPy2, self).__init__()

    @cpybase
    def test(self):
        pass

    @test.layer(LayerEnum.L1)
    def test_c2l2(self):
        pass


class CPyTest(unittest.TestCase):

    def test_check_layers(self):
        self.assertEqual(set([LayerEnum.L1.value, LayerEnum.L2.value]), set(CPy1.layers.keys()))

    def test_check_layers2(self):
        # confirm CPy1 and CPy2 are not contaminated each other
        self.assertEqual(set([LayerEnum.L1.value]), set(CPy2.layers.keys()))

    def test_base_called(self):
        obj = CPy1()
        obj.test()
        self.assertEqual(True, obj.base_called)

    def test_activate_l1(self):
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj.test()
        self.assertEqual(False, obj.base_called)
        self.assertEqual(True, obj.l1_called)

    def test_actdeact_l1(self):
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj.test()

        obj.reset()

        obj.deactivate(LayerEnum.L1)
        obj.test()
        self.assertEqual(True, obj.base_called)
        self.assertEqual(False, obj.l1_called)

    def test_activate_l1_l2(self):
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj.activate(LayerEnum.L2)
        obj.test()
        self.assertEqual(False, obj.base_called)
        self.assertEqual(True, obj.l1_called)  # proceed
        self.assertEqual(True, obj.l2_called)

    def test_actl1l2_deactl1(self):
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj.activate(LayerEnum.L2)
        obj.test()

        obj.reset()

        obj.deactivate(LayerEnum.L1)
        obj.test()
        self.assertEqual(True, obj.base_called)  # proceed
        self.assertEqual(False, obj.l1_called)
        self.assertEqual(True, obj.l2_called)

    def test_basemethod_called_without_layers(self):
        obj = CPy1()
        obj.skiptest()
        self.assertEqual(True, obj.base_called)
        self.assertEqual(False, obj.l1_called)
        self.assertEqual(False, obj.l2_called)

    def test_activate_l2_and_base_called(self):
        obj = CPy1()
        obj.activate(LayerEnum.L2)
        obj.skiptest()
        self.assertEqual(True, obj.base_called)
        self.assertEqual(False, obj.l1_called)
        self.assertEqual(False, obj.l2_called)


if __name__ == '__main__':
    unittest.main()
