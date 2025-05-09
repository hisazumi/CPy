# -*- coding: utf-8 -*-
# CPySingle: extends a single class with Context-Oriented Programming (COP)
# The scope of layer activation and deactivation is limited to a single class
class CPySingle(object):
    @classmethod
    def init_layer(cls):
        if not hasattr(cls, 'layers'):
            cls.layers = {}

    @classmethod
    def add_layer(cls, layer):
        cls.init_layer()
        cls.layers[layer] = {}

    @classmethod
    def add_method(cls, layer, name, method):
        cls.init_layer()
        if layer not in cls.layers:
            cls.add_layer(layer)
        cls.layers[layer][name] = method

    def __init__(self):
        super(CPySingle, self).__init__()
        # array of activated layers
        self._layer = ['base']
        # array of valid functions for proceeds, init at method call
        self._proceed_funcs = []
        # cache
        self.purge_cache()

    def purge_cache(self):
        self.cache = {}

    def activate(self, layer):
        self.purge_cache()
        self._layer.append(layer)

    def deactivate(self, layer):
        self.purge_cache()
        self._layer.remove(layer)

    def proceed(self, *args, **kwargs):
        current = self._proceed_funcs.pop()
        retval = current(self, *args, **kwargs)
        self._proceed_funcs.append(current)
        return retval

# LayerMethodRegistrar: Helper class for accessing and registering class and method from the decorator
class LayerMethodRegistrar:
    def __init__(self, func_to_decorate, layer_name, base_method_name):
        self.func_to_decorate = func_to_decorate
        self.layer_name = layer_name
        self.base_method_name = base_method_name

    def __set_name__(self, owner_cls, name_in_class):
        if hasattr(owner_cls, 'add_method') and callable(owner_cls.add_method):
            owner_cls.add_method(self.layer_name, self.base_method_name, self.func_to_decorate)
        else:
            raise TypeError(
                f"The class {owner_cls.__name__} where '{name_in_class}' is defined "
                f"does not have an 'add_method'. Ensure it inherits from CPySingle or CPy."
            )

    def __get__(self, instance, owner_cls):
        if instance is None:
            return self.func_to_decorate
        return self.func_to_decorate.__get__(instance, owner_cls)

def cpybase(func):  # decorator for base method
    def activated_funcs(self, fname):
        active_methods = [func]
        if hasattr(self.__class__, 'layers') and isinstance(self.__class__.layers, dict):
            for layer_key_active in self._layer:
                if layer_key_active == 'base':
                    continue
                class_layers = self.__class__.layers
                if layer_key_active in class_layers:
                    layer_specific_methods = class_layers[layer_key_active]
                    if isinstance(layer_specific_methods, dict) and fname in layer_specific_methods:
                        active_methods.append(layer_specific_methods[fname])
        return active_methods

    def f(self, *args, **kwargs):
        fname = func.__name__
        if fname in self.cache:
            self._proceed_funcs = self.cache[fname]
        else:
            self._proceed_funcs = activated_funcs(self, fname)
            self.cache[fname] = self._proceed_funcs
        return self.proceed(*args, **kwargs)
    return f

# cpylayer: decorator for layer method
def cpylayer(layer_name, base_method_name):
    def decorator(func):
        return LayerMethodRegistrar(func, layer_name, base_method_name)
    return decorator

# CPy: extends multiple classes with Context-Oriented Programming (COP)
# The scope of layer activation and deactivation is not limited to a single class
class CPy(CPySingle):
    instances: list["CPy"] = []

    def __init__(self):
        super(CPy, self).__init__()
        self.queued_request = []
        self.in_critical = False
        CPy.instances.append(self)

    @classmethod
    def activate(cls, layer):
        for i in CPy.instances:
            i.req_activate(layer)

    @classmethod
    def deactivate(cls, layer):
        for i in CPy.instances:
            i.req_deactivate(layer)

    def req_activate(self, layer):
        if self.in_critical:
            self.queued_request.append(('act', layer))
        else:
            super(CPy, self).activate(layer)

    def req_deactivate(self, layer):
        if self.in_critical:
            self.queued_request.append(('dea', layer))
        else:
            super(CPy, self).deactivate(layer)

    def begin(self):
        self.in_critical = True

    def end(self):
        self.do()
        self.in_critical = False

    def do(self):
        for r in self.queued_request:
            if r[0] == 'act':
                super(CPy, self).activate(r[1])
            elif r[0] == 'dea':
                super(CPy, self).deactivate(r[1])
        self.queued_request = []

# Critical: a context manager for critical section
class Critical(object):

    def __init__(self, obj):
        self.obj = obj

    def __enter__(self):
        self.obj.begin()

    def __exit__(self, type, value, traceback):
        self.obj.end()

# Layer: a context manager for layer activation and deactivation
class Layer(object):

    def __init__(self, layer):
        self.layer = layer

    def __enter__(self):
        CPy.activate(self.layer)

    def __exit__(self, type, value, traceback):
        CPy.deactivate(self.layer)
