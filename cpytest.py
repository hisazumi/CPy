#!/usr/bin/env python
import unittest
from cpy import CPy, cpylayer, cpybase, Critical, Layer

# テスト用のサブクラスを複数作成
class SubClassA(CPy):
    @cpybase
    def method_a(self):
        return "SubClassA base method"

class SubClassB(CPy):
    @cpybase
    def method_b(self):
        return "SubClassB base method"

class TestCPy(unittest.TestCase):
    def setUp(self):
        self.instance_a = SubClassA()
        self.instance_b = SubClassB()

    def test_individual_layer_activation_deactivation(self):
        @cpylayer(SubClassA, 'layerA', 'method_a')
        def layerA_method(self):
            return "layerA method for SubClassA"

        @cpylayer(SubClassB, 'layerB', 'method_b')
        def layerB_method(self):
            return "layerB method for SubClassB"

        # レイヤーを活性化してメソッドを呼び出し、結果を確認
        self.instance_a.activate('layerA')
        self.assertEqual(self.instance_a.method_a(), "layerA method for SubClassA")
        self.instance_b.activate('layerB')
        self.assertEqual(self.instance_b.method_b(), "layerB method for SubClassB")

        # レイヤーを非活性化してベースメソッドが呼ばれることを確認
        self.instance_a.deactivate('layerA')
        self.assertEqual(self.instance_a.method_a(), "SubClassA base method")
        self.instance_b.deactivate('layerB')
        self.assertEqual(self.instance_b.method_b(), "SubClassB base method")

    def test_global_layer_activation_deactivation(self):
        @cpylayer(SubClassA, 'global_layer', 'method_a')
        def global_layer_method_a(self):
            return "global layer method for SubClassA"

        @cpylayer(SubClassB, 'global_layer', 'method_b')
        def global_layer_method_b(self):
            return "global layer method for SubClassB"

        # グローバルにレイヤーを活性化し、すべてのインスタンスに反映されることを確認
        CPy.activate('global_layer')
        self.assertEqual(self.instance_a.method_a(), "global layer method for SubClassA")
        self.assertEqual(self.instance_b.method_b(), "global layer method for SubClassB")

        # グローバルにレイヤーを非活性化し、元のメソッドに戻ることを確認
        CPy.deactivate('global_layer')
        self.assertEqual(self.instance_a.method_a(), "SubClassA base method")
        self.assertEqual(self.instance_b.method_b(), "SubClassB base method")

    def test_layer_context_manager(self):
        @cpylayer(SubClassB, 'temp_layerB', 'method_b')
        def temp_layerB_method(self):
            return "temporary layerB method for SubClassB"

        # Layerコンテキストマネージャーでの一時的なレイヤー活性化
        with Layer('temp_layerB'):
            self.assertEqual(self.instance_b.method_b(), "temporary layerB method for SubClassB")

        # コンテキストを抜けると元に戻る
        self.assertEqual(self.instance_b.method_b(), "SubClassB base method")


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
