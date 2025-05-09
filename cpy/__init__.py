# -*- coding: utf-8 -*-
# CPySingle: extends a single class with Context-Oriented Programming (COP)
# The scope of layer activation and deactivation is limited to a single class

from enum import Enum
from typing import Any, Dict, List, Callable, Type, Optional, Tuple, Union, Protocol

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
        # array of valid functions for proceeds, init at method call
        self._proceed_funcs: List[Callable] = []
        # cache
        self.cache: Dict[Enum, List[Callable]] = {}
        self.purge_cache()

    def purge_cache(self) -> None:
        self.cache = {}

    def activate(self, layer: Enum) -> None:
        self.purge_cache()
        self._layer.append(layer)

    def deactivate(self, layer: Enum) -> None:
        self.purge_cache()
        self._layer.remove(layer)

    def proceed(self, *args: Any, **kwargs: Any) -> Any:
        current: Callable = self._proceed_funcs.pop()
        retval: Any = current(self, *args, **kwargs)
        self._proceed_funcs.append(current)
        return retval

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
    def activated_funcs_for_base(self_instance: Any, base_fname: str) -> List[Callable]:
        active_methods: List[Callable] = [original_base_func] # The base method itself is the first in the list
        if hasattr(self_instance.__class__, 'layers') and isinstance(self_instance.__class__.layers, dict):
            for layer_key_active in self_instance._layer:
                if layer_key_active == CPySingle.Layer.BASE: continue # Base is already added

                class_layers: Dict[Enum, Dict[str, Callable]] = self_instance.__class__.layers
                if layer_key_active in class_layers:
                    layer_specific_methods: Dict[str, Callable] = class_layers[layer_key_active]
                    if isinstance(layer_specific_methods, dict) and base_fname in layer_specific_methods:
                        active_methods.append(layer_specific_methods[base_fname])
        return active_methods

    # This is the function that is actually registered as a class method and called at runtime
    def runtime_behavior_of_base_method(self_instance: Any, *args: Any, **kwargs: Any) -> Any:
        fname: str = original_base_func.__name__
        if fname in self_instance.cache:
            self_instance._proceed_funcs = self_instance.cache[fname]
        else:
            self_instance._proceed_funcs = activated_funcs_for_base(self_instance, fname)
            self_instance.cache[fname] = self_instance._proceed_funcs
        return self_instance.proceed(*args, **kwargs)

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
        self.queued_request: List[Tuple[str, Enum]] = []
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
            self.queued_request.append(('act', layer))
        else:
            super(CPy, self).activate(layer)

    def req_deactivate(self, layer: Enum) -> None:
        if self.in_critical:
            self.queued_request.append(('dea', layer))
        else:
            super(CPy, self).deactivate(layer)

    def begin(self) -> None:
        self.in_critical = True

    def end(self) -> None:
        self.do()
        self.in_critical = False

    def do(self) -> None:
        for r in self.queued_request:
            if r[0] == 'act':
                super(CPy, self).activate(r[1])
            elif r[0] == 'dea':
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
