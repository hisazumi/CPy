#!/usr/bin/env python

import unittest
from cpy import CPySingle, cpylayer, cpybase
from enum import Enum

PKG = 'testcpy'

class LayerEnum(Enum):
    L1 = 'l1'
    L2 = 'l2'
    L3 = 'l3' # Add a new layer for execution order tests

class CPy1(CPySingle):

    _layer_order = [LayerEnum.L1, LayerEnum.L2, LayerEnum.L3] # Define the execution order of layers for this class

    def __init__(self):
        self.reset()
        super(CPy1, self).__init__()

    def reset(self):
        self.base_called = False
        self.l1_called = False
        self.l2_called = False
        self.l3_called = False # Add state for L3 layer
        self.execution_order = [] # List to record execution order
        self._l1_should_proceed = True # Flag to control if test_l1 calls proceed()

    @cpybase
    def test(self):
        self.base_called = True
        self.execution_order.append('base')

    @cpybase
    def skiptest(self):
        self.base_called = True
        self.execution_order.append('skiptest_base')

    @test.layer(LayerEnum.L1)
    def test_l1(self):
        self.l1_called = True
        self.execution_order.append('l1')
        if self._l1_should_proceed:
            self.proceed()

    @test.layer(LayerEnum.L2)
    def test_l2(self):
        self.l2_called = True
        self.execution_order.append('l2')
        self.proceed() # Always call proceed() in this layer

    @test.layer(LayerEnum.L3)
    def test_l3(self):
        self.l3_called = True
        self.execution_order.append('l3')

    @cpybase
    def method_with_exception(self):
        pass

    @method_with_exception.layer(LayerEnum.L1)
    def method_with_exception_l1(self):
        raise ValueError("Test Exception")


class CPy2(CPySingle):

    def __init__(self):
        self.reset()
        super(CPy2, self).__init__()

    def reset(self):
        # Add reset method to CPy2
        self.l1_called = False
        self.base_called = False # Also check if CPy2's base is called

    @cpybase
    def test(self):
        self.base_called = True # Confirm that CPy2's base is also called

    @test.layer(LayerEnum.L1)
    def test_c2l1(self): # Correct method name
        self.l1_called = True


class CPyTest(unittest.TestCase):

    def test_cpy1_check_layers(self):
        # Confirm that L3 layer has also been added
        self.assertEqual(set([LayerEnum.L1, LayerEnum.L2, LayerEnum.L3]), set(CPy1.layers.keys()))

    def test_cpy2_check_layers(self):
        # Confirm that CPy1 and CPy2 are not polluting each other
        self.assertEqual(set([LayerEnum.L1]), set(CPy2.layers.keys()))

    def test_cpy1_test_base_called_without_layers(self):
        obj = CPy1()
        obj.test()
        self.assertEqual(True, obj.base_called)
        self.assertEqual(['base'], obj.execution_order) # Check execution order

    def test_cpy1_test_activate_l1_without_proceed(self):
        # Case where L1 is activated and proceed() is not called within the L1 method
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj._l1_should_proceed = False # Set to not call proceed()
        obj.test()
        self.assertEqual(False, obj.base_called)
        self.assertEqual(True, obj.l1_called)
        self.assertEqual(False, obj.l2_called) # L2 is not called because proceed() is not called
        self.assertEqual(['l1'], obj.execution_order) # Check execution order

    def test_cpy1_test_activate_l1_with_proceed(self):
        # Case where L1 is activated and proceed() is called within the L1 method (default behavior)
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj._l1_should_proceed = True # Set to call proceed() (default)
        obj.test()
        # Expect execution to be L1 -> base because L1 is activated and calls proceed(), but L2 is not active
        self.assertEqual(True, obj.base_called)
        self.assertEqual(True, obj.l1_called)
        self.assertEqual(False, obj.l2_called) # L2 is not called because it's not active
        self.assertEqual(['l1', 'base'], obj.execution_order) # Check execution order


    def test_cpy1_test_actdeact_l1(self):
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj._l1_should_proceed = True # Set to call proceed() (default)
        obj.test() # First execution
        # Expect execution to be L1 -> base because L1 is activated and calls proceed(), but L2 is not active
        self.assertEqual(['l1', 'base'], obj.execution_order) # Check execution order
        obj.reset()
        obj.deactivate(LayerEnum.L1)
        obj.test() # Second execution
        self.assertEqual(True, obj.base_called)
        self.assertEqual(False, obj.l1_called)
        self.assertEqual(False, obj.l2_called) # L2 is not called because L1 is deactivated
        self.assertEqual(['base'], obj.execution_order) # Check execution order


    def test_cpy1_test_activate_l1_l2_with_proceed(self):
        # Case where L1 and L2 are activated and proceed() is called within L1 and L2 methods
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj.activate(LayerEnum.L2)
        obj._l1_should_proceed = True # Set to call proceed() (default)
        obj.test()
        self.assertEqual(True, obj.base_called) # base is called because L1 and L2 call proceed()
        self.assertEqual(True, obj.l1_called)
        self.assertEqual(True, obj.l2_called)
        self.assertEqual(['l1', 'l2', 'base'], obj.execution_order) # Check execution order


    def test_cpy1_test_actl1l2_deactl1_with_proceed(self):
        # Case where L1 and L2 are activated, then L1 is deactivated
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj.activate(LayerEnum.L2)
        obj._l1_should_proceed = True # Set to call proceed() (default)
        obj.test() # First execution
        self.assertEqual(['l1', 'l2', 'base'], obj.execution_order) # Check execution order
        obj.reset()
        obj.deactivate(LayerEnum.L1)
        obj.test() # Second execution
        self.assertEqual(True, obj.base_called)  # Since L1 is deactivated, execution goes L2 -> base
        self.assertEqual(False, obj.l1_called)
        self.assertEqual(True, obj.l2_called)
        self.assertEqual(['l2', 'base'], obj.execution_order) # Check execution order


    def test_cpy1_skiptest_base_called_without_layers(self):
        obj = CPy1()
        obj.skiptest()
        self.assertEqual(True, obj.base_called)
        self.assertEqual(False, obj.l1_called)
        self.assertEqual(False, obj.l2_called)
        self.assertEqual(['skiptest_base'], obj.execution_order) # Check execution order

    def test_cpy1_skiptest_activate_l2_and_base_called(self):
        obj = CPy1()
        obj.activate(LayerEnum.L2) # Since skiptest has no L2 layer, base is called
        obj.skiptest()
        self.assertEqual(True, obj.base_called)
        self.assertEqual(False, obj.l1_called)
        self.assertEqual(False, obj.l2_called)
        self.assertEqual(['skiptest_base'], obj.execution_order) # Check execution order

    def test_cpy2_test_activate_l1(self):
        # Activate L1 layer for CPy2's test method
        obj = CPy2()
        obj.activate(LayerEnum.L1)
        obj.test()
        self.assertEqual(False, obj.base_called) # CPy2's L1 layer does not call proceed(), so base is not called
        self.assertEqual(True, obj.l1_called)

    def test_cpy1_test_execution_order_l1_l2_l3(self):
        # Check execution order when L1, L2, L3 are activated in order
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj.activate(LayerEnum.L2)
        obj.activate(LayerEnum.L3)
        obj._l1_should_proceed = True # Set to call proceed() in L1
        obj.test()
        # Expect execution in defined order (L1 -> L2 -> L3), and base is not called because L3 does not call proceed()
        self.assertEqual(['l1', 'l2', 'l3'], obj.execution_order)

    def test_cpy1_test_execution_order_l3_l2_l1(self):
        # Check execution order when L3, L2, L1 are activated in order (confirming execution is by definition order, not activation order)
        obj = CPy1()
        obj.activate(LayerEnum.L3)
        obj.activate(LayerEnum.L2)
        obj.activate(LayerEnum.L1)
        obj._l1_should_proceed = True # Set to call proceed() in L1
        obj.test()
        # Expect execution in defined order (L1 -> L2 -> L3), and base is not called because L3 does not call proceed()
        self.assertEqual(['l1', 'l2', 'l3'], obj.execution_order)

    def test_cpy1_method_with_exception_l1(self):
        # Test case for when an exception occurs in the L1 layer
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        with self.assertRaises(ValueError) as cm:
            obj.method_with_exception()
        self.assertEqual("Test Exception", str(cm.exception))
        # Confirm that the base method is not called because an exception occurred
        self.assertEqual([], obj.execution_order) # Confirm execution order list is empty


if __name__ == '__main__':
    unittest.main()
