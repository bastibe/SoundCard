import numpy
from cffi import FFI

ffi = FFI()
with open('pulseaudio.py.h', 'rt') as f:
    ffi.cdef(f.read())

pa = ffi.dlopen('pulse')

import time
from threading import Thread

class AudioThread(Thread):
    def __init__(self, mainloop):
        super(AudioThread, self).__init__()
        self.mainloop = mainloop
    def run(self):
        self.retval = ffi.new('int*', 0)
        pa.pa_mainloop_run(self.mainloop, self.retval)
    def stop(self):
        pa.pa_mainloop_quit(self.mainloop, self.retval[0])

class PulseAudio:
    def __init__(self):
        self.mainloop = pa.pa_mainloop_new()
        self.mainloop_api = pa.pa_mainloop_get_api(self.mainloop)
        self.context = pa.pa_context_new(self.mainloop_api, b"audio")
        pa.pa_context_connect(self.context, ffi.NULL, pa.PA_CONTEXT_NOFLAGS, ffi.NULL)
        self.thread = AudioThread(self.mainloop)

    def __enter__(self):
        self.thread.start()
        while pa.pa_context_get_state(self.context) != pa.PA_CONTEXT_READY:
            time.sleep(0.001)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.thread.stop()
        self.thread.join()
        pa.pa_context_disconnect(self.context)
        pa.pa_context_unref(self.context)
        pa.pa_mainloop_free(self.mainloop)

    def get_source_info_list(self):
        info = []
        @ffi.callback("pa_source_info_cb_t")
        def callback(context, source_info, eol, userdata):
            if not eol:
                info.append(dict(index=source_info.index,
                                 description=ffi.string(source_info.description).decode('utf-8'),
                                 latency=source_info.configured_latency))
        operation = pa.pa_context_get_source_info_list(self.context, callback, ffi.NULL)
        while pa.pa_operation_get_state(operation) == pa.PA_OPERATION_RUNNING:
            time.sleep(0.001)
        pa.pa_operation_unref(operation)
        return info

    def get_sink_info_list(self):
        info = []
        @ffi.callback("pa_sink_info_cb_t")
        def callback(context, source_info, eol, userdata):
            if not eol:
                info.append((dict(index=source_info.index,
                                  name=ffi.string(source_info.description).decode('utf-8'),
                                  latency=source_info.configured_latency)))
        operation = pa.pa_context_get_sink_info_list(self.context, callback, ffi.NULL)
        while pa.pa_operation_get_state(operation) == pa.PA_OPERATION_RUNNING:
            time.sleep(0.01)
        pa.pa_operation_unref(operation)
        return info

with PulseAudio() as p:
    print(p.get_source_info_list())
    print(p.get_sink_info_list())
