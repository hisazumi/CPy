import sys
import os

# Add the parent directory to sys.path to be able to import the 'cpy' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cpy import CPy, cpybase
from enum import Enum

class Layer(Enum):
    ENHANCE = 'enhance'
    LOGGING = 'logging'

class CPy1(CPy):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.enhanced = False
        self.logged = False

    def reset_flags(self):
        self.enhanced = False
        self.logged = False

    @cpybase
    def greet(self):
        print(f"Hello from {self.name}")

    @greet.layer(Layer.ENHANCE)
    def greet_enhance(self):
        print(f"Enhancing greet for {self.name}...")
        self.enhanced = True
        self.proceed()

    @greet.layer(Layer.LOGGING)
    def greet_logging(self):
        print(f"Logging greet for {self.name}...")
        self.logged = True
        self.proceed()


class CPy2(CPy):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.enhanced = False
        self.logged = False

    def reset_flags(self):
        self.enhanced = False
        self.logged = False

    @cpybase
    def greet(self):
        print(f"Hi from {self.name}")

    @greet.layer(Layer.ENHANCE)
    def greet_enhance(self):
        print(f"Enhancing greet for {self.name} in CPy2...")
        self.enhanced = True
        self.proceed()

    @greet.layer(Layer.LOGGING)
    def greet_logging(self):
        print(f"Logging greet for {self.name} in CPy2...")
        self.logged = True
        self.proceed()


# Create instances of both classes
obj1 = CPy1("Instance 1")
obj2 = CPy2("Instance 2")

print("--- Before activation ---")
obj1.reset_flags()
obj2.reset_flags()
obj1.greet()
obj2.greet()
print(f"Obj1 enhanced: {obj1.enhanced}, logged: {obj1.logged}")
print(f"Obj2 enhanced: {obj2.enhanced}, logged: {obj2.logged}")
print("-" * 25)

# Activate the ENHANCE layer globally for all CPy instances
CPy.activate(Layer.ENHANCE)

print("--- After activating ENHANCE layer ---")
obj1.reset_flags()
obj2.reset_flags()
obj1.greet()
obj2.greet()
print(f"Obj1 enhanced: {obj1.enhanced}, logged: {obj1.logged}")
print(f"Obj2 enhanced: {obj2.enhanced}, logged: {obj2.logged}")
print("-" * 25)

# Activate the LOGGING layer globally
CPy.activate(Layer.LOGGING)

print("--- After activating ENHANCE and LOGGING layers ---")
obj1.reset_flags()
obj2.reset_flags()
obj1.greet()
obj2.greet()
print(f"Obj1 enhanced: {obj1.enhanced}, logged: {obj1.logged}")
print(f"Obj2 enhanced: {obj2.enhanced}, logged: {obj2.logged}")
print("-" * 25)

# Deactivate the ENHANCE layer globally
CPy.deactivate(Layer.ENHANCE)

print("--- After deactivating ENHANCE layer ---")
obj1.reset_flags()
obj2.reset_flags()
obj1.greet()
obj2.greet()
print(f"Obj1 enhanced: {obj1.enhanced}, logged: {obj1.logged}")
print(f"Obj2 enhanced: {obj2.enhanced}, logged: {obj2.logged}")
print("-" * 25)

# Deactivate the LOGGING layer globally
CPy.deactivate(Layer.LOGGING)

print("--- After deactivating LOGGING layer ---")
obj1.reset_flags()
obj2.reset_flags()
obj1.greet()
obj2.greet()
print(f"Obj1 enhanced: {obj1.enhanced}, logged: {obj1.logged}")
print(f"Obj2 enhanced: {obj2.enhanced}, logged: {obj2.logged}")
print("-" * 25)
