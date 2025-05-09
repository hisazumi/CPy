from cpy import CPy, cpylayer, cpybase

class CPy1(CPy):
    def __init__(self):
        self.reset()
        super(CPy1, self).__init__()

    def reset(self):
        self.base_called = False
        self.l1_called = False
        self.l2_called = False

    @cpybase # declare as a base method
    def test(self):
        self.base_called = True

    @cpybase # declare as a base method
    def skiptest(self):
        self.base_called = True

    @cpylayer('l1', 'test') # @cpylayer(layer name, method name)
    def test_l1(self):
        self.l1_called = True

    @cpylayer('l2', 'test')
    def test_l2(self):
        self.l2_called = True
        self.proceed()

obj = CPy1()
obj.activate('l1')
obj.test()
print(obj.base_called)  # False
print(obj.l1_called)    # True

obj = CPy1()
obj.activate('l1')
obj.activate('l2')
obj.test()
print(obj.base_called)  # False
print(obj.l1_called)    # True
print(obj.l2_called)    # True