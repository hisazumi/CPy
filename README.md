# CPy Library

## Overview

The `CPy` library adds **context-oriented programming** features to Python by providing decorators to add layers to Python classes and modify the behavior of specific methods.

It enables you to dynamically add and activate layers of methods that override base implementations. Using `CPy`, you can enable or disable specific method layers, control execution flows, and proceed to the next function in a layered stack. **CPy supports applying layers to multiple instances of the same class or different classes simultaneously.** This is especially useful for scenarios where method behaviors need to vary based on active contexts or layers.

## Installation

This library is provided as Python scripts. Add the following files to your project:

- `cpy.py`

## Usage

### Defining Layers using Enum

It is recommended to define your layers using Python's `Enum` for better readability and maintainability.

```python
from enum import Enum

class AppLayer(Enum):
    FEATURE_X = 'feature_x'
    DEBUG_LOG = 'debug_log'
    VALIDATION = 'validation'
```

### Inheriting from CPy and Declaring Base Methods Using the @cpybase Decorator

To utilize the layering system provided by CPy, your class must inherit from the CPy base class. Additionally, any methods that you wish to modify through layers need to be declared as base methods by using the @cpybase decorator.

```python
from cpy import CPy, cpybase
from enum import Enum # Import Enum if defining layers in the same file

# Assuming AppLayer Enum is defined as above or imported

class MyClass(CPy):
    def __init__(self, name):
        super().__init__()
        self.name = name

    @cpybase # declare as a base method
    def process_data(self, data):
        print(f"{self.name} processing: {data}")
        return f"Processed: {data}"
```

### Adding Layers using @base_method_name.layer Decorator

Use the `@base_method_name.layer` decorator to add layers to specific base methods. You can use the Enum members defined earlier.

```python
    @process_data.layer(AppLayer.FEATURE_X) # Add FEATURE_X layer to process_data
    def process_data_feature_x(self, data):
        print(f"Applying Feature X for {self.name}...")
        modified_data = f"[{data}]"
        return self.proceed(modified_data) # Use self.proceed() to call the next method in the stack

    @process_data.layer(AppLayer.DEBUG_LOG) # Add DEBUG_LOG layer
    def process_data_debug_log(self, data):
        print(f"DEBUG: process_data called with {data} on {self.name}")
        return self.proceed(data)
```

### Adding Layers using @cpylayer Decorator

You can also define layer methods outside the class definition using the `@cpylayer` decorator. This is useful for organizing layer definitions separately.

```python
# Assuming MyClass and AppLayer are defined or imported

@cpylayer(AppLayer.VALIDATION) # Apply VALIDATION layer to MyClass.process_data
def process_data_validation(self, data):
    if not isinstance(data, str):
        print(f"Validation failed for {self.name}: data must be a string.")
        return None # Stop processing if validation fails
    print(f"Validation successful for {self.name}.")
    return self.proceed(data)
```

### Activating and Deactivating Layers

Activate or deactivate layers on individual instances or globally for all CPy instances using the `activate()` and `deactivate()` methods. Use the Enum members for specifying layers.

```python
# Create instances
obj1 = MyClass("Instance 1")
obj2 = MyClass("Instance 2")

print("--- Before activation ---")
obj1.process_data("initial data")
obj2.process_data("initial data")
print("-" * 25)

# Activate a layer on a single instance
obj1.activate(AppLayer.FEATURE_X)

print("--- After activating FEATURE_X on Instance 1 ---")
obj1.process_data("data A")
obj2.process_data("data B") # Feature X is not active on obj2
print("-" * 25)

# Activate a layer globally for all CPy instances
CPy.activate(AppLayer.DEBUG_LOG)

print("--- After activating DEBUG_LOG globally ---")
obj1.process_data("data C") # Both FEATURE_X and DEBUG_LOG are active on obj1
obj2.process_data("data D") # Only DEBUG_LOG is active on obj2
print("-" * 25)

# Deactivate a layer on a single instance
obj1.deactivate(AppLayer.FEATURE_X)

print("--- After deactivating FEATURE_X on Instance 1 ---")
obj1.process_data("data E") # Only DEBUG_LOG is active on obj1
obj2.process_data("data F") # Only DEBUG_LOG is active on obj2
print("-" * 25)

# Deactivate a layer globally
CPy.deactivate(AppLayer.DEBUG_LOG)

print("--- After deactivating DEBUG_LOG globally ---")
obj1.process_data("data G") # No layers active on obj1
obj2.process_data("data H") # No layers active on obj2
print("-" * 25)
```

### Using Critical Section

The `Critical` context manager allows queuing layer activation/deactivation requests within a block, processing them only upon exiting the block.

```python
from cpy import Critical

obj = MyClass("Critical Instance")

with Critical(obj):
    obj.activate(AppLayer.FEATURE_X)
    obj.process_data("data in critical") # Layers are not active yet
    print("Inside critical section")

# Layers are activated upon exiting the critical section
print("--- After critical section ---")
obj.process_data("data after critical")
```

### Using Layer Context Manager

The `Layer` context manager provides a convenient way to temporarily activate a layer within a `with` block. The layer is automatically deactivated upon exiting the block.

```python
from cpy import Layer

obj = MyClass("Layer Context Instance")

print("--- Before Layer context ---")
obj.process_data("initial data")
print("-" * 25)

with Layer(AppLayer.DEBUG_LOG):
    print("--- Inside Layer context (DEBUG_LOG active) ---")
    obj.process_data("data in context")
    print("-" * 25)

print("--- After Layer context ---")
obj.process_data("data after context") # DEBUG_LOG is now deactivated
print("-" * 25)
```

## Running Tests

To run the unit tests, execute the following command in your terminal:

```bash
python3 cpytest.py
```

This will run the tests defined in `cpytest.py` to verify the library's functionality.
