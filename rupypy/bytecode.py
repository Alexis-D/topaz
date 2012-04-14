from rupypy import consts


class CompilerContext(object):
    def __init__(self, space):
        self.space = space
        self.data = []
        self.consts = []
        self.const_positions = {}
        self.locals = {}

    def create_bytecode(self):
        bc = "".join(self.data)
        locs = [None] * len(self.locals)
        for name, pos in self.locals.iteritems():
            locs[pos] = name
        return Bytecode(bc, self.count_stackdepth(bc), self.consts[:], locs)

    def count_stackdepth(self, bc):
        i = 0
        current_stackdepth = max_stackdepth = 0
        while i < len(bc):
            c = ord(bc[i])
            i += 1
            stack_effect = consts.BYTECODE_STACK_EFFECT[c]
            if stack_effect == consts.SEND_EFFECT:
                stack_effect = -ord(bc[i+1])
            elif stack_effect == consts.ARRAY_EFFECT:
                stack_effect = -ord(bc[i]) + 1
            i += consts.BYTECODE_NUM_ARGS[c]
            current_stackdepth += stack_effect
            max_stackdepth = max(max_stackdepth, current_stackdepth)
        return max_stackdepth

    def emit(self, c, arg0=-1, arg1=-1):
        self.data.append(chr(c))
        if arg0 != -1:
            self.data.append(chr(arg0))
        if arg1 != -1:
            self.data.append(chr(arg1))

    def get_pos(self):
        return len(self.data)

    def patch_jump(self, pos):
        self.data[pos + 1] = chr(len(self.data))

    def create_local(self, name):
        if name not in self.locals:
            self.locals[name] = len(self.locals)
        return self.locals[name]

    def local_defined(self, name):
        return name in self.locals

    def create_const(self, w_obj):
        if w_obj not in self.const_positions:
            self.const_positions[w_obj] = len(self.consts)
            self.consts.append(w_obj)
        return self.const_positions[w_obj]

    def create_int_const(self, intvalue):
        return self.create_const(self.space.newint(intvalue))

    def create_symbol_const(self, symbol):
        return self.create_const(self.space.newsymbol(symbol))

    def create_string_const(self, strvalue):
        return self.create_const(self.space.newstr_fromstr(strvalue))


class Bytecode(object):
    _immutable_fields_ = ["code", "consts[*]", "max_stackdepth", "locals[*]"]

    def __init__(self, code, max_stackdepth, consts, locals):
        self.code = code
        self.max_stackdepth = max_stackdepth
        self.consts = consts
        self.locals = locals