from pypy.rlib import jit

from rupypy.module import ClassDef
from rupypy.objects.functionobject import W_FunctionObject
from rupypy.objects.objectobject import W_BaseObject


class AttributeReader(W_FunctionObject):
    _immutable_fields_ = ["varname"]

    def __init__(self, varname):
        self.varname = varname

    def call(self, space, w_obj, args_w, block):
        return space.find_instance_var(w_obj, self.varname)


class AttributeWriter(W_FunctionObject):
    _immutable_fields_ = ["varname"]

    def __init__(self, varname):
        self.varname = varname

    def call(self, space, w_obj, args_w, block):
        [w_value] = args_w
        space.set_instance_var(w_obj, self.varname, w_value)
        return w_value


class VersionTag(object):
    pass


class W_ModuleObject(W_BaseObject):
    _immutable_fields_ = ["version?"]

    classdef = ClassDef("Module", W_BaseObject.classdef)

    def __init__(self, space, name):
        self.name = name
        self.klass = None
        self.version = VersionTag()
        self.methods_w = {}

    def mutated(self):
        self.version = VersionTag()

    def define_method(self, space, name, method):
        self.mutated()
        self.methods_w[name] = method

    def find_method(self, space, method):
        return self._find_method_pure(space, method, self.version)

    @jit.elidable
    def _find_method_pure(self, space, method, version):
        return self.methods_w.get(method, None)

    def getclass(self, space):
        if self.klass is not None:
            return self.klass
        return W_BaseObject.getclass(self, space)

    def getsingletonclass(self, space):
        if self.klass is None:
            self.klass = space.newclass(self.name, space.getclassfor(type(self)), is_singleton=True)
        return self.klass

    @classdef.method("attr_accessor")
    def method_attr_accessor(self, space, args_w):
        for w_arg in args_w:
            varname = space.symbol_w(w_arg)
            self.define_method(space, varname, AttributeReader(varname))
            self.define_method(space, varname + "=", AttributeWriter(varname))

    @classdef.method("attr_reader", varname="symbol")
    def method_attr_reader(self, space, varname):
        self.define_method(space, varname, AttributeReader(varname))
