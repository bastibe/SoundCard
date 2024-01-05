class PAMeta(type):
    def __getattr__(self, _):
        return None


class PAStub(metaclass=PAMeta):
    PA_CONTEXT_READY = None

    def _dummy_function(self, *args, **kwargs):
        return None

    def __getattr__(self, _):
        return self._dummy_function


class FFI:
    NULL = None

    def cdef(self, _):
        return NotImplemented

    def dlopen(self, _):
        return PAStub()
