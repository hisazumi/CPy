#!/usr/bin/env python
import unittest
from cpy import CPy, cpylayer, cpybase, Critical

class CPyQ1(CPy):

    def __init__(self):
        super(CPyQ1, self).__init__()
        self.base_callee_called = False
        self.l1_callee_called = False
        self.l2_callee_called = False

    @cpybase
    def callee(self):
        self.base_callee_called = True


@cpylayer(CPyQ1, 'l1', 'callee')
def callee_l1(self):
    self.l1_callee_called = True


@cpylayer(CPyQ1, 'l2', 'callee')
def callee_l2(self):
    self.l2_callee_called = True


class CPyQTest(unittest.TestCase):

    def test_basic(self):
        obj1 = CPyQ1()
        obj2 = CPyQ1()
        obj1.activate('l1')
        obj1.callee()
        self.assertEqual(True, obj1.l1_callee_called)
        self.assertEqual(False, obj1.l2_callee_called)


    def test_Critical(self):
        obj = CPyQ1()

        with Critical(obj):
            obj.activate('l1')
            obj.callee()  # still base
            self.assertEqual(False, obj.l1_callee_called)
            self.assertEqual(True, obj.base_callee_called)

            obj.activate('l2')
            obj.callee()  # still base
            self.assertEqual(False, obj.l1_callee_called)
            self.assertEqual(True, obj.base_callee_called)

            obj.deactivate('l2')
            obj.callee()  # of course still base
            self.assertEqual(False, obj.l1_callee_called)
            self.assertEqual(True, obj.base_callee_called)

            # check queue contents
            self.assertEqual([('act', 'l1'), ('act', 'l2'),
                              ('dea', 'l2')], obj.queued_request)

        self.assertEqual(['base', 'l1'], obj._layer)
        obj.callee()  # activated l1, deactivated l2
        self.assertEqual(True, obj.l1_callee_called)
        self.assertEqual(False, obj.l2_callee_called)


if __name__ == '__main__':
    unittest.main()
