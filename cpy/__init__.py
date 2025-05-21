# -*- coding: utf-8 -*-
# CPySingle: extends a single class with Context-Oriented Programming (COP)
# The scope of layer activation and deactivation is limited to a single class

from enum import Enum
from typing import Any, Dict, List, Callable, Type, Optional, Tuple, Union, Protocol

class CPyRequestType(Enum):
    ACTIVATE = 'act'
    DEACTIVATE = 'dea'

class CPySingle(object):
    class Layer(Enum):
        BASE = 'base'

    layers: Dict[Enum, Dict[str, Callable]]

    @classmethod
    def init_layer(cls) -> None:
        if not hasattr(cls, 'layers'):
            cls.layers = {}

    @classmethod
    def add_layer(cls, layer: Enum) -> None:
        cls.init_layer()
        if layer in cls.layers:
            raise ValueError(f"Layer '{layer}' already exists. Cannot add duplicate layer.")
        cls.layers[layer] = {}

    @classmethod
    def add_method(cls, layer: Enum, name: str, method: Callable) -> None:
        cls.init_layer()
        if layer not in cls.layers:
            cls.add_layer(layer)
        cls.layers[layer][name] = method

    def __init__(self) -> None:
        super(CPySingle, self).__init__()
        # array of activated layers
        self._layer: List[Enum] = [CPySingle.Layer.BASE]
        # Stores the execution state for each base method call:
        # { base_method_name: { 'chain': List[Callable], 'index': int } }
        self._execution_state: Dict[str, Dict[str, Union[List[Callable], int]]] = {}
        # cache (This might still be useful for performance, but the logic needs adjustment)
        # self.cache: Dict[Enum, List[Callable]] = {}
        # self.purge_cache()

    # def purge_cache(self) -> None:
    #     self.cache = {}
    #     self._execution_state = {} # Clear on reset too

    def activate(self, layer: Enum) -> None:
        # self.purge_cache() # Activating/deactivating shouldn't purge execution state
        if layer not in self._layer:
            self._layer.append(layer)

    def deactivate(self, layer: Enum) -> None:
        # self.purge_cache() # Activating/deactivating shouldn't purge execution state
        if layer in self._layer:
            self._layer.remove(layer)

    def proceed(self, *args: Any, **kwargs: Any) -> Any:
        # Get the name of the currently executing base method.
        # This requires the runtime_behavior_of_base_method to set this context.
        # A simple way is to assume the last added state in _execution_state is the current one.
        # This works for CPySingle where base methods are not expected to be called re-entrantly.
        if not self._execution_state:
             raise RuntimeError("proceed() called without active base method")

        # Get the name of the most recent base method call
        current_base_method_name = list(self._execution_state.keys())[-1]
        state = self._execution_state[current_base_method_name]
        execution_chain: List[Callable] = state['chain'] # type: ignore[assignment]
        current_index: int = state['index'] # type: ignore[assignment]

        next_index = current_index + 1

        if next_index < len(execution_chain):
            state['index'] = next_index
            next_func = execution_chain[next_index]
            retval: Any = next_func(self, *args, **kwargs)
            return retval
        else:
            # If we've gone past the end of the chain, it means the last function called proceed.
            # The chain is now complete for this base method call.
            # Clean up the state for this base method.
            del self._execution_state[current_base_method_name]
            # Return None or potentially the result of the last executed function if needed,
            # but the current structure implies the return value comes from the executed function.
            return None # Or perhaps the return value of the last executed function? Let's stick to None for now.


# LayerMethodRegistrar: Helper class for accessing and registering class and method from the decorator
class LayerMethodRegistrar:
    def __init__(self, func_to_decorate: Callable, layer: Enum, base_method_name: str) -> None:
        self.func_to_decorate: Callable = func_to_decorate
        self.layer: Enum = layer
        self.base_method_name: str = base_method_name

    def __set_name__(self, owner_cls: Type, name_in_class: str) -> None:
        if hasattr(owner_cls, 'add_method') and callable(owner_cls.add_method):
            owner_cls.add_method(self.layer, self.base_method_name, self.func_to_decorate)
        else:
            raise TypeError(
                f"The class {owner_cls.__name__} where '{name_in_class}' is defined "
                f"does not have an 'add_method'. Ensure it inherits from CPySingle or CPy."
            )

    def __get__(self, instance: Optional[Any], owner_cls: Type) -> Callable:
        if instance is None:
            return self.func_to_decorate
        return self.func_to_decorate.__get__(instance, owner_cls)

class CPyBaseWithLayer(Protocol):
    layer: Callable[[Enum], Callable]
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

def cpybase(original_base_func: Callable) -> CPyBaseWithLayer:
    def build_execution_chain(self_instance: Any, base_fname: str) -> List[Callable]:
        execution_chain: List[Callable] = []
        class_layers: Dict[Enum, Dict[str, Callable]] = getattr(self_instance.__class__, 'layers', {})
        defined_layer_order: List[Enum] = getattr(self_instance.__class__, '_layer_order', []) # Get defined order

        # If _layer_order is not defined, fall back to activation order (current behavior)
        if not defined_layer_order:
             defined_layer_order = [layer for layer in self_instance._layer if layer != CPySingle.Layer.BASE]
             # Optionally sort by definition order if available in class_layers, but _layer_order is clearer

        # Build the chain based on defined order, including only active layers
        for layer_key in defined_layer_order:
             if layer_key in self_instance._layer and layer_key in class_layers:
                 layer_specific_methods: Dict[str, Callable] = class_layers[layer_key]
                 if isinstance(layer_specific_methods, dict) and base_fname in layer_specific_methods:
                     execution_chain.append(layer_specific_methods[base_fname])

        # Always append the base method at the end of the chain
        if CPySingle.Layer.BASE in class_layers and base_fname in class_layers[CPySingle.Layer.BASE]:
             execution_chain.append(class_layers[CPySingle.Layer.BASE][base_fname])
        else:
             # This case should ideally not happen if cpybase is used correctly
             # but as a fallback, append the original function if not found in layers
             execution_chain.append(original_base_func)


        return execution_chain

    # This is the function that is actually registered as a class method and called at runtime
    def runtime_behavior_of_base_method(self_instance: Any, *args: Any, **kwargs: Any) -> Any:
        fname: str = original_base_func.__name__

        # Build the execution chain based on defined order and active layers
        execution_chain = build_execution_chain(self_instance, fname)

        if not execution_chain:
            # If no active layers and no base method found (shouldn't happen with base method always added)
            # or if the base method itself wasn't registered correctly.
            # As a fallback, call the original base function directly.
            return original_base_func(self_instance, *args, **kwargs)

        # Store the execution chain and starting index (before the first element)
        self_instance._execution_state[fname] = {
            'chain': execution_chain,
            'index': -1 # Start index at -1 so the first proceed() call executes the first element (index 0)
        }

        # Start the execution by calling proceed()
        # The first call to proceed will execute the first function in the chain
        retval: Any = self_instance.proceed(*args, **kwargs)

        # The state for this base method call is cleared within the last proceed() call
        # when the index goes out of bounds.

        return retval

    def layer_decorator_factory(layer: Enum) -> Callable:
        def decorator(layer_function_to_register: Callable) -> LayerMethodRegistrar:
            # Register the layer method using LayerMethodRegistrar
            # Get the base method name from original_base_func.__name__
            return LayerMethodRegistrar(layer_function_to_register, layer, original_base_func.__name__)
        return decorator

    # Dynamically add the 'layer' attribute with type hint
    setattr(runtime_behavior_of_base_method, 'layer', layer_decorator_factory)
    # Cast to the protocol type to satisfy the type checker
    return runtime_behavior_of_base_method # type: ignore[return-value]

# cpylayer: decorator for layer method
def cpylayer(layer: Enum, base_method_name: str) -> Callable:
    def decorator(func: Callable) -> LayerMethodRegistrar:
        return LayerMethodRegistrar(func, layer, base_method_name)
    return decorator

# CPy: extends multiple classes with Context-Orientated Programming (COP)
# The scope of layer activation and deactivation is not limited to a single class
class CPy(CPySingle):
    instances: List["CPy"] = []

    def __init__(self) -> None:
        super(CPy, self).__init__()
        self.queued_request: List[Tuple[CPyRequestType, Enum]] = []
        self.in_critical: bool = False
        CPy.instances.append(self)

    @classmethod
    def activate(cls, layer: Enum) -> None:
        for i in CPy.instances:
            i.req_activate(layer)

    @classmethod
    def deactivate(cls, layer: Enum) -> None:
        for i in CPy.instances:
            i.req_deactivate(layer)

    def req_activate(self, layer: Enum) -> None:
        if self.in_critical:
            self.queued_request.append((CPyRequestType.ACTIVATE, layer))
        else:
            super(CPy, self).activate(layer)

    def req_deactivate(self, layer: Enum) -> None:
        if self.in_critical:
            self.queued_request.append((CPyRequestType.DEACTIVATE, layer))
        else:
            super(CPy, self).deactivate(layer)

    def begin(self) -> None:
        self.in_critical = True

    def end(self) -> None:
        self.do()
        self.in_critical = False

    def do(self) -> None:
        for r in self.queued_request:
            if r[0] == CPyRequestType.ACTIVATE:
                super(CPy, self).activate(r[1])
            elif r[0] == CPyRequestType.DEACTIVATE:
                super(CPy, self).deactivate(r[1])
        self.queued_request = []

# Critical: a context manager for critical section
class Critical(object):

    def __init__(self, obj: CPy) -> None:
        self.obj: CPy = obj

    def __enter__(self) -> None:
        self.obj.begin()

    def __exit__(self, type: Optional[Type[BaseException]], value: Optional[BaseException], traceback: Optional[Any]) -> None:
        self.obj.end()

# Layer: a context manager for layer activation and deactivation
class Layer(object):

    def __init__(self, layer: Enum) -> None:
        self.layer_name: Enum = layer

    def __enter__(self) -> None:
        CPy.activate(self.layer_name)

    def __exit__(self, type: Optional[Type[BaseException]], value: Optional[BaseException], traceback: Optional[Any]) -> None:
        CPy.deactivate(self.layer_name)
