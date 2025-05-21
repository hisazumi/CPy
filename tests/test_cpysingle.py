#!/usr/bin/env python

import unittest
from cpy import CPySingle, cpylayer, cpybase
from enum import Enum

PKG = 'testcpy'

class LayerEnum(Enum):
    L1 = 'l1'
    L2 = 'l2'
    L3 = 'l3' # 新しいレイヤーを追加して実行順序のテストに使う

class CPy1(CPySingle):

    _layer_order = [LayerEnum.L1, LayerEnum.L2, LayerEnum.L3] # Define the execution order of layers for this class

    def __init__(self):
        self.reset()
        super(CPy1, self).__init__()

    def reset(self):
        self.base_called = False
        self.l1_called = False
        self.l2_called = False
        self.l3_called = False # L3 レイヤーの状態を追加
        self.execution_order = [] # 実行順序を記録するためのリスト
        self._l1_should_proceed = True # test_l1 で proceed() を呼ぶかどうかのフラグ

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
        self.proceed() # このレイヤーでは常に proceed() を呼ぶ

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
        # CPy2 にも reset メソッドを追加
        self.l1_called = False
        self.base_called = False # CPy2 の base も確認できるようにする

    @cpybase
    def test(self):
        self.base_called = True # CPy2 の base も呼ばれることを確認

    @test.layer(LayerEnum.L1)
    def test_c2l1(self): # メソッド名を修正
        self.l1_called = True


class CPyTest(unittest.TestCase):

    def test_cpy1_check_layers(self):
        # L3 レイヤーも追加されたことを確認
        self.assertEqual(set([LayerEnum.L1, LayerEnum.L2, LayerEnum.L3]), set(CPy1.layers.keys()))

    def test_cpy2_check_layers(self):
        # CPy1 と CPy2 が互いに汚染されていないことを確認
        self.assertEqual(set([LayerEnum.L1]), set(CPy2.layers.keys()))

    def test_cpy1_test_base_called_without_layers(self):
        obj = CPy1()
        obj.test()
        self.assertEqual(True, obj.base_called)
        self.assertEqual(['base'], obj.execution_order) # 実行順序を確認

    def test_cpy1_test_activate_l1_without_proceed(self):
        # L1 をアクティベートし、L1 メソッド内で proceed() を呼ばないケース
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj._l1_should_proceed = False # proceed() を呼ばないように設定
        obj.test()
        self.assertEqual(False, obj.base_called)
        self.assertEqual(True, obj.l1_called)
        self.assertEqual(False, obj.l2_called) # proceed() が呼ばれないので L2 は呼ばれない
        self.assertEqual(['l1'], obj.execution_order) # 実行順序を確認

    def test_cpy1_test_activate_l1_with_proceed(self):
        # L1 をアクティベートし、L1 メソッド内で proceed() を呼ぶケース (デフォルトの挙動)
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj._l1_should_proceed = True # proceed() を呼ぶように設定 (デフォルト)
        obj.test()
        # L1 をアクティベートし proceed() を呼ぶが、L2 はアクティブではないため L1 -> base と実行されることを期待
        self.assertEqual(True, obj.base_called)
        self.assertEqual(True, obj.l1_called)
        self.assertEqual(False, obj.l2_called) # L2 はアクティブではないので呼ばれない
        self.assertEqual(['l1', 'base'], obj.execution_order) # 実行順序を確認


    def test_cpy1_test_actdeact_l1(self):
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj._l1_should_proceed = True # proceed() を呼ぶように設定 (デフォルト)
        obj.test() # 最初の実行
        # L1 をアクティベートし proceed() を呼ぶが、L2 はアクティブではないため L1 -> base と実行されることを期待
        self.assertEqual(['l1', 'base'], obj.execution_order) # 実行順序を確認
        obj.reset()
        obj.deactivate(LayerEnum.L1)
        obj.test() # 2回目の実行
        self.assertEqual(True, obj.base_called)
        self.assertEqual(False, obj.l1_called)
        self.assertEqual(False, obj.l2_called) # L1 が無効なので L2 は呼ばれない
        self.assertEqual(['base'], obj.execution_order) # 実行順序を確認


    def test_cpy1_test_activate_l1_l2_with_proceed(self):
        # L1 と L2 をアクティベートし、L1 と L2 メソッド内で proceed() を呼ぶケース
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj.activate(LayerEnum.L2)
        obj._l1_should_proceed = True # proceed() を呼ぶように設定 (デフォルト)
        obj.test()
        self.assertEqual(True, obj.base_called) # L1, L2 と proceed() が呼ばれるため base は L2 から呼ばれる
        self.assertEqual(True, obj.l1_called)
        self.assertEqual(True, obj.l2_called)
        self.assertEqual(['l1', 'l2', 'base'], obj.execution_order) # 実行順序を確認


    def test_cpy1_test_actl1l2_deactl1_with_proceed(self):
        # L1 と L2 をアクティベートし、L1 をディアクティベートするケース
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj.activate(LayerEnum.L2)
        obj._l1_should_proceed = True # proceed() を呼ぶように設定 (デフォルト)
        obj.test() # 最初の実行
        self.assertEqual(['l1', 'l2', 'base'], obj.execution_order) # 実行順序を確認
        obj.reset()
        obj.deactivate(LayerEnum.L1)
        obj.test() # 2回目の実行
        self.assertEqual(True, obj.base_called)  # L1 が無効なので L2 -> base と実行される
        self.assertEqual(False, obj.l1_called)
        self.assertEqual(True, obj.l2_called)
        self.assertEqual(['l2', 'base'], obj.execution_order) # 実行順序を確認


    def test_cpy1_skiptest_base_called_without_layers(self):
        obj = CPy1()
        obj.skiptest()
        self.assertEqual(True, obj.base_called)
        self.assertEqual(False, obj.l1_called)
        self.assertEqual(False, obj.l2_called)
        self.assertEqual(['skiptest_base'], obj.execution_order) # 実行順序を確認

    def test_cpy1_skiptest_activate_l2_and_base_called(self):
        obj = CPy1()
        obj.activate(LayerEnum.L2) # skiptest に L2 レイヤーはないので base が呼ばれる
        obj.skiptest()
        self.assertEqual(True, obj.base_called)
        self.assertEqual(False, obj.l1_called)
        self.assertEqual(False, obj.l2_called)
        self.assertEqual(['skiptest_base'], obj.execution_order) # 実行順序を確認

    def test_cpy2_test_activate_l1(self):
        # CPy2 の test メソッドに L1 レイヤーをアクティベート
        obj = CPy2()
        obj.activate(LayerEnum.L1)
        obj.test()
        self.assertEqual(False, obj.base_called) # CPy2 の L1 レイヤーは proceed() を呼ばないので base は呼ばれない
        self.assertEqual(True, obj.l1_called)

    def test_cpy1_test_execution_order_l1_l2_l3(self):
        # L1, L2, L3 を順にアクティベートした場合の実行順序を確認
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        obj.activate(LayerEnum.L2)
        obj.activate(LayerEnum.L3)
        obj._l1_should_proceed = True # L1 で proceed() を呼ぶように設定
        obj.test()
        # L1 (proceed) -> L2 (proceed) -> L3 の順で呼ばれ、L3 は proceed() を呼ばないので base は呼ばれないことを期待
        self.assertEqual(['l1', 'l2', 'l3'], obj.execution_order)

    def test_cpy1_test_execution_order_l3_l2_l1(self):
        # L3, L2, L1 を順にアクティベートした場合の実行順序を確認 (アクティベート順ではなく定義順に実行されることを確認)
        obj = CPy1()
        obj.activate(LayerEnum.L3)
        obj.activate(LayerEnum.L2)
        obj.activate(LayerEnum.L1)
        obj._l1_should_proceed = True # L1 で proceed() を呼ぶように設定
        obj.test()
        # 定義順 (L1 -> L2 -> L3) で呼ばれることを期待
        # L1 (proceed) -> L2 (proceed) -> L3 の順で呼ばれ、L3 は proceed() を呼ばないので base は呼ばれないことを期待
        self.assertEqual(['l1', 'l2', 'l3'], obj.execution_order)

    def test_cpy1_method_with_exception_l1(self):
        # L1 レイヤーで例外が発生する場合のテスト
        obj = CPy1()
        obj.activate(LayerEnum.L1)
        with self.assertRaises(ValueError) as cm:
            obj.method_with_exception()
        self.assertEqual("Test Exception", str(cm.exception))
        # 例外が発生したため、base メソッドは呼ばれないことを確認
        self.assertEqual([], obj.execution_order) # 実行順序リストが空であることを確認


if __name__ == '__main__':
    unittest.main()
