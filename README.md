# CPy Library

## Overview

The `CPy` library adds **context-oriented programming** features to Python by providing decorators to add layers to Python classes and modify the behavior of specific methods.

It enables you to dynamically add and activate layers of methods that override base implementations. Using `CPy`, you can enable or disable specific method layers, control execution flows, and proceed to the next function in a layered stack. This is especially useful for scenarios where method behaviors need to vary based on active contexts or layers.

## Installation

This library is provided as Python scripts. Add the following files to your project:

- `cpy.py`

## Usage

### Inheriting from CPy and Declaring Base Methods Using the @cpybase Decorator

To utilize the layering system provided by CPy, your class must inherit from the CPy base class. Additionally, any methods that you wish to modify through layers need to be declared as base methods by using the @cpybase decorator.

This involves two key steps:

1.	Inherit from CPy: Ensure your class inherits from the CPy class to access the layering functionalities.
2.	Declare Base Methods with @cpybase: Decorate methods that can be overridden or extended by layers with the @cpybase decorator.

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

Next, use the @methodname.layer decorator to add layers to specific methods.

```python
    @test.layer('l1') # @methodname.layer(layer name)
    def test_l1(self):
        self.l1_called = True

    @test.layer('l2')
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

obj = CPy1()
obj.activate('l1')
obj.activate('l2')
obj.test()
print(obj.base_called)  # False
print(obj.l1_called)    # True
print(obj.l2_called)    # True
```