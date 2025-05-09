#!/usr/bin/env python
import unittest
from cpy import CPy, cpybase, Critical, Layer, CPyRequestType
from enum import Enum

# Define Enum for test layers
class TestLayer(Enum):
    LAYERA = 'layerA'
    LAYERB = 'layerB'
    GLOBAL_LAYER = 'global_layer'
    TEMP_LAYERB = 'temp_layerB'
    L1 = 'l1'
    L2 = 'l2'

# テスト用のサブクラスを複数作成
class SubClassA(CPy):
    @cpybase
    def method_a(self):
        return "SubClassA base method"

    @method_a.layer(TestLayer.LAYERA)
    def method_a_layerA(self):
        return "layerA method for SubClassA"

    @method_a.layer(TestLayer.GLOBAL_LAYER)
    def method_a_global_layer(self):
        return "global layer method for SubClassA"


class SubClassB(CPy):
    @cpybase
    def method_b(self):
        return "SubClassB base method"

    @method_b.layer(TestLayer.LAYERB)
    def method_b_layerB(self):
        return "layerB method for SubClassB"

    @method_b.layer(TestLayer.GLOBAL_LAYER)
    def method_b_global_layer(self):
        return "global layer method for SubClassB"

    @method_b.layer(TestLayer.TEMP_LAYERB)
    def method_b_temp_layerB(self):
        return "temporary layerB method for SubClassB"


class TestCPy(unittest.TestCase):
    def setUp(self):
        self.instance_a = SubClassA()
        self.instance_b = SubClassB()

    def test_individual_layer_activation_deactivation(self):
        # レイヤーを活性化してメソッドを呼び出し、結果を確認
        self.instance_a.activate(TestLayer.LAYERA)
        self.assertEqual(self.instance_a.method_a(), "layerA method for SubClassA")
        self.instance_b.activate(TestLayer.LAYERB)
        self.assertEqual(self.instance_b.method_b(), "layerB method for SubClassB")

        # レイヤーを非活性化してベースメソッドが呼ばれることを確認
        self.instance_a.deactivate(TestLayer.LAYERA)
        self.assertEqual(self.instance_a.method_a(), "SubClassA base method")
        self.instance_b.deactivate(TestLayer.LAYERB)
        self.assertEqual(self.instance_b.method_b(), "SubClassB base method")

    def test_global_layer_activation_deactivation(self):
        # グローバルにレイヤーを活性化し、すべてのインスタンスに反映されることを確認
        CPy.activate(TestLayer.GLOBAL_LAYER)
        self.assertEqual(self.instance_a.method_a(), "global layer method for SubClassA")
        self.assertEqual(self.instance_b.method_b(), "global layer method for SubClassB")

        # グローバルにレイヤーを非活性化し、元のメソッドに戻ることを確認
        CPy.deactivate(TestLayer.GLOBAL_LAYER)
        self.assertEqual(self.instance_a.method_a(), "SubClassA base method")
        self.assertEqual(self.instance_b.method_b(), "SubClassB base method")

    def test_layer_context_manager(self):
        # Layerコンテキストマネージャーでの一時的なレイヤー活性化
        with Layer(TestLayer.TEMP_LAYERB):
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

    @callee.layer(TestLayer.L1)
    def callee_l1(self):
        self.l1_callee_called = True
        self.proceed()

    @callee.layer(TestLayer.L2)
    def callee_l2(self):
        self.l2_callee_called = True


class CPyQTest(unittest.TestCase):

    def test_Critical(self):
        obj = CPyQ1()

        with Critical(obj):
            obj.activate(TestLayer.L1)
            obj.callee()  # still base
            self.assertEqual(False, obj.l1_callee_called)
            self.assertEqual(True, obj.base_callee_called)

            obj.activate(TestLayer.L2)
            obj.callee()  # still base
            self.assertEqual(False, obj.l1_callee_called)
            self.assertEqual(True, obj.base_callee_called)

            obj.deactivate(TestLayer.L2)
            obj.callee()  # of course still base
            self.assertEqual(False, obj.l1_callee_called)
            self.assertEqual(True, obj.base_callee_called)

            # check queue contents
            self.assertEqual([(CPyRequestType.ACTIVATE, TestLayer.L1),
                              (CPyRequestType.ACTIVATE, TestLayer.L2),
                              (CPyRequestType.DEACTIVATE, TestLayer.L2)], obj.queued_request)

        # Criticalセクションを抜けた後、キューが処理される
        self.assertEqual([CPy.Layer.BASE, TestLayer.L1], obj._layer)
        
        # フラグをリセットしてからcalleeを呼び出し、レイヤーメソッドが実行されることを確認
        obj.base_callee_called = False
        obj.l1_callee_called = False
        obj.l2_callee_called = False
        obj.callee()  # activated l1, deactivated l2
        self.assertEqual(True, obj.l1_callee_called)
        self.assertEqual(False, obj.l2_callee_called)
        self.assertEqual(True, obj.base_callee_called) # base should be called via proceed

if __name__ == '__main__':
    unittest.main()
