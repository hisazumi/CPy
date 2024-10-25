# CPy Library

## Overview

The `CPy` library adds **context-oriented programming** features to Python by providing decorators to add layers to Python classes and modify the behavior of specific methods.

It enables you to dynamically add and activate layers of methods that override base implementations. Using `CPy`, you can enable or disable specific method layers, control execution flows, and proceed to the next function in a layered stack. This is especially useful for scenarios where method behaviors need to vary based on active contexts or layers.

## Installation

This library is provided as Python scripts. Add the following files to your project:

- `cpy.py`

## Usage

### Base Methods and the @cpybase Decorator

In CPy, **base methods** are the original implementations that can be overridden or extended by layer-specific methods. To allow a method’s behavior to be modified by layers, you need to decorate it with the @cpybase decorator. This signals that the method is eligible for layering and integrates it into the CPy layering system.

Use the @cpybase decorator to mark methods that can have their behavior altered by layers:

```python
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
```

### Adding Layers

Next, use the @cpylayer decorator to add layers to specific methods.

```python
@cpylayer(CPy1, 'l1', 'test') # @cpylayer(class name, layer name, method name)
def test_l1(self):
    self.l1_called = True

@cpylayer(CPy1, 'l2', 'test')
def test_l2(self):
    self.l2_called = True
    self.proceed()
```

### Instantiating the Class and Calling Methods

Create an instance of the class and call the methods to see the layered behavior.

```python
obj = CPy1()
obj.activate('l1')
obj.test()
print(obj.base_called)  # False
print(obj.l1_called)    # True

obj.activate('l2')
obj.test()
print(obj.base_called)  # False
print(obj.l2_called)    # True
```