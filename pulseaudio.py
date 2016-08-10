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

    def _block_operation(self, operation):
        while pa.pa_operation_get_state(operation) == pa.PA_OPERATION_RUNNING:
            time.sleep(0.001)
        pa.pa_operation_unref(operation)

    def get_source_info_list(self):
        info = []
        @ffi.callback("pa_source_info_cb_t")
        def callback(context, source_info, eol, userdata):
            if not eol:
                info.append(dict(index=source_info.index,
                                 description=ffi.string(source_info.description).decode('utf-8'),
                                 latency=source_info.configured_latency,
                                 id=ffi.string(source_info.name).decode('utf-8')))
        operation = pa.pa_context_get_source_info_list(self.context, callback, ffi.NULL)
        self._block_operation(operation)
        return info

    def get_sink_info_list(self):
        info = []
        @ffi.callback("pa_sink_info_cb_t")
        def callback(context, source_info, eol, userdata):
            if not eol:
                info.append((dict(index=source_info.index,
                                  name=ffi.string(source_info.description).decode('utf-8'),
                                  latency=source_info.configured_latency,
                                  id=ffi.string(source_info.name).decode('utf-8'))))
        operation = pa.pa_context_get_sink_info_list(self.context, callback, ffi.NULL)
        self._block_operation(operation)
        return info

    def get_server_info(self):
        info = {}
        @ffi.callback("pa_server_info_cb_t")
        def callback(context, server_info, userdata):
            info['server version'] = ffi.string(server_info.server_version).decode('utf-8')
            info['server name'] = ffi.string(server_info.server_name).decode('utf-8')
            info['default sink id'] = ffi.string(server_info.default_sink_name).decode('utf-8')
            info['default source id'] = ffi.string(server_info.default_source_name).decode('utf-8')
        operation = pa.pa_context_get_server_info(self.context, callback, ffi.NULL)
        self._block_operation(operation)
        return info

    def play(self, data, samplerate, name="outputstream"):
        samplespec = ffi.new("pa_sample_spec*")
        samplespec.format = pa.PA_SAMPLE_FLOAT32LE
        samplespec.rate = samplerate
        samplespec.channels = 2
        if not pa.pa_sample_spec_valid(samplespec):
            raise RuntimeException('invalid sample spec')
        stream = pa.pa_stream_new(self.context, name.encode(), samplespec, ffi.NULL)
        bufattr = ffi.new("pa_buffer_attr*")
        bufattr.maxlength = 2**32-1 # max buffer length
        bufattr.fragsize = 2**32-1 # block size
        bufattr.minreq = 2**32-1 # start requesting more data at this bytes
        bufattr.prebuf = 2**32-1 # start playback after this bytes are available
        bufattr.tlength = 2**32-1 # buffer length in bytes on server
        pa.pa_stream_connect_playback(stream, self.get_server_info()['default sink id'].encode(),
                                      bufattr, pa.PA_STREAM_NOFLAGS, ffi.NULL, ffi.NULL)
        while pa.pa_stream_get_state(stream) == pa.PA_STREAM_CREATING:
            time.sleep(0.01)
        if pa.pa_stream_get_state(stream) != pa.PA_STREAM_READY:
            raise RuntimeError('Stream creation failed. Stream is in status {}'.format(pa.pa_stream_get_state(stream)))
        data = numpy.array(data, dtype='float32')
        bytes = data.ravel().tostring()
        pa.pa_stream_write(stream, bytes, len(bytes), ffi.NULL, 0, pa.PA_SEEK_RELATIVE)
        operation = pa.pa_stream_drain(stream, ffi.NULL, ffi.NULL)
        self._block_operation(operation)
        pa.pa_stream_unref(stream)

with PulseAudio() as p:
    print(p.get_source_info_list())
    print(p.get_sink_info_list())
    print(p.get_server_info())
    data = numpy.sin(numpy.linspace(0, 2*numpy.pi*100, 44100))
    p.play(data, 44100)
