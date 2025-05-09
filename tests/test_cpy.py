#!/usr/bin/env python
import unittest
from cpy import CPy, cpybase, Critical, Layer, CPyRequestType
from enum import Enum

# Define Enum for test layers
class LayerEnumForTest(Enum):
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

    @method_a.layer(LayerEnumForTest.LAYERA)
    def method_a_layerA(self):
        return "layerA method for SubClassA"

    @method_a.layer(LayerEnumForTest.GLOBAL_LAYER)
    def method_a_global_layer(self):
        return "global layer method for SubClassA"


class SubClassB(CPy):
    @cpybase
    def method_b(self):
        return "SubClassB base method"

    @method_b.layer(LayerEnumForTest.LAYERB)
    def method_b_layerB(self):
        return "layerB method for SubClassB"

    @method_b.layer(LayerEnumForTest.GLOBAL_LAYER)
    def method_b_global_layer(self):
        return "global layer method for SubClassB"

    @method_b.layer(LayerEnumForTest.TEMP_LAYERB)
    def method_b_temp_layerB(self):
        return "temporary layerB method for SubClassB"


class TestCPy(unittest.TestCase):
    def setUp(self):
        self.instance_a = SubClassA()
        self.instance_b = SubClassB()

    def test_individual_layer_activation_deactivation(self):
        # レイヤーを活性化してメソッドを呼び出し、結果を確認
        self.instance_a.activate(LayerEnumForTest.LAYERA)
        self.assertEqual(self.instance_a.method_a(), "layerA method for SubClassA")
        self.instance_b.activate(LayerEnumForTest.LAYERB)
        self.assertEqual(self.instance_b.method_b(), "layerB method for SubClassB")

        # レイヤーを非活性化してベースメソッドが呼ばれることを確認
        self.instance_a.deactivate(LayerEnumForTest.LAYERA)
        self.assertEqual(self.instance_a.method_a(), "SubClassA base method")
        self.instance_b.deactivate(LayerEnumForTest.LAYERB)
        self.assertEqual(self.instance_b.method_b(), "SubClassB base method")

    def test_global_layer_activation_deactivation(self):
        # グローバルにレイヤーを活性化し、すべてのインスタンスに反映されることを確認
        CPy.activate(LayerEnumForTest.GLOBAL_LAYER)
        self.assertEqual(self.instance_a.method_a(), "global layer method for SubClassA")
        self.assertEqual(self.instance_b.method_b(), "global layer method for SubClassB")

        # グローバルにレイヤーを非活性化し、元のメソッドに戻ることを確認
        CPy.deactivate(LayerEnumForTest.GLOBAL_LAYER)
        self.assertEqual(self.instance_a.method_a(), "SubClassA base method")
        self.assertEqual(self.instance_b.method_b(), "SubClassB base method")

    def test_layer_context_manager(self):
        # Layerコンテキストマネージャーでの一時的なレイヤー活性化
        with Layer(LayerEnumForTest.TEMP_LAYERB):
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

    @callee.layer(LayerEnumForTest.L1)
    def callee_l1(self):
        self.l1_callee_called = True
        self.proceed()

    @callee.layer(LayerEnumForTest.L2)
    def callee_l2(self):
        self.l2_callee_called = True


class CPyQTest(unittest.TestCase):

    def test_Critical(self):
        obj = CPyQ1()

        with Critical(obj):
            obj.activate(LayerEnumForTest.L1)
            obj.callee()  # still base
            self.assertEqual(False, obj.l1_callee_called)
            self.assertEqual(True, obj.base_callee_called)

            obj.activate(LayerEnumForTest.L2)
            obj.callee()  # still base
            self.assertEqual(False, obj.l1_callee_called)
            self.assertEqual(True, obj.base_callee_called)

            obj.deactivate(LayerEnumForTest.L2)
            obj.callee()  # of course still base
            self.assertEqual(False, obj.l1_callee_called)
            self.assertEqual(True, obj.base_callee_called)

            # check queue contents
            self.assertEqual([(CPyRequestType.ACTIVATE, LayerEnumForTest.L1),
                              (CPyRequestType.ACTIVATE, LayerEnumForTest.L2),
                              (CPyRequestType.DEACTIVATE, LayerEnumForTest.L2)], obj.queued_request)

        # Criticalセクションを抜けた後、キューが処理される
        self.assertEqual([CPy.Layer.BASE, LayerEnumForTest.L1], obj._layer)
        
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
