class CPy(object):

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
        super(CPy, self).__init__()
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


def cpybase(func):
    def activated_funcs(self, fname):
        a = [func]  # for base
        try:
            a.extend([self.__class__.layers[l][fname]
                      for l in self._layer
                      if l in self.__class__.layers])
        except:
            pass
        return a

    def f(self, *args, **kwargs):
        fname = func.__name__
        if fname in self.cache:
            self._proceed_funcs = self.cache[fname]
        else:
            self._proceed_funcs = activated_funcs(self, fname)
            self.cache[fname] = self._proceed_funcs
        return self.proceed(*args, **kwargs)

    return f


def cpylayer(cls, layer, name):
    def f(func):
        cls.add_method(layer, name, func)
    return f


