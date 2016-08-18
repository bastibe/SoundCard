from cffi import FFI

ffi = FFI()
with open('pulseaudio.py.h', 'rt') as f:
    ffi.cdef(f.read())

pa = ffi.dlopen('pulse')

import time
import threading
import re
import numpy


def all_speakers():
    """A list of all known speakers."""
    with _PulseAudio() as p:
        return [_Speaker(id=s['id']) for s in p.get_sink_info_list()]


def default_speaker():
    """The default speaker of the system."""
    with _PulseAudio() as p:
        name = p.get_server_info()['default sink id']
        return get_speaker(name)


def get_speaker(id):
    """Get a specific speaker by a variety of means.

    id can be an int index, a pulseaudio id, a substring of the
    speaker name, or a fuzzy-matched pattern for the speaker name.

    """
    with _PulseAudio() as p:
        speakers = p.get_sink_info_list()
    return _Speaker(id=_match_soundcard(id, speakers)['id'])


def all_microphones():
    """A list of all connected microphones."""
    with _PulseAudio() as p:
        return [Microphone(id=m['id']) for m in p.get_source_info_list()]


def default_microphone():
    """The default microphone of the system."""
    with _PulseAudio() as p:
        name = p.get_server_info()['default source id']
        return get_microphone(name)


def get_microphone(id):
    """Get a specific microphone by a variety of means.

    id can be an int index, a pulseaudio id, a substring of the
    microphone name, or a fuzzy-matched pattern for the microphone
    name.

    """
    with _PulseAudio() as p:
        microphones = p.get_source_info_list()
    return Microphone(id=_match_soundcard(id, microphones)['id'])


def _match_soundcard(id, soundcards):
    """Find id in a list of soundcards.

    id can be an int index, a pulseaudio id, a substring of the
    microphone name, or a fuzzy-matched pattern for the microphone
    name.

    """
    soundcards_by_index = {soundcard['index']: soundcard for soundcard in soundcards}
    soundcards_by_id = {soundcard['id']: soundcard for soundcard in soundcards}
    soundcards_by_name = {soundcard['name']: soundcard for soundcard in soundcards}
    if isinstance(id, int):
        if id in soundcards_by_index:
            return soundcards_by_index[id]
        else:
            raise IndexError('no soundcard with id {}'.format(id))
    elif isinstance(id, str):
        if id in soundcards_by_id:
            return soundcards_by_id[id]
        # try substring match:
        for name, soundcard in soundcards_by_name.items():
            if id in name:
                return soundcard
        # try fuzzy match:
        pattern = '.*'.join(id)
        for name, soundcard in soundcards_by_name.items():
            if re.match(pattern, name):
                return soundcard
        raise IndexError('no soundcard with id {}'.format(id))


class _Speaker:
    """A soundcard output. Can be used to play audio."""

    def __init__(self, *, id):
        self._id = id

    def __repr__(self):
        return '<Speaker {}>'.format(self._id)

    def player(self, samplerate):
        return _Player(self._id, samplerate)

    def play(self, data, samplerate):
        with _Player(self._id, samplerate) as s:
            s.play(data)


class _Stream:
    """An audio stream."""

    def __init__(self, id, samplerate, type, name='outputstream'):
        self._id = id
        self._samplerate = samplerate
        self._name = name
        self._type = type
        self.channels = None

    def __enter__(self):
        self._pulse = _PulseAudio()
        self._pulse.__enter__()
        samplespec = ffi.new("pa_sample_spec*")
        samplespec.format = pa.PA_SAMPLE_FLOAT32LE
        samplespec.rate = self._samplerate
        samplespec.channels = 2
        if not pa.pa_sample_spec_valid(samplespec):
            raise RuntimeException('invalid sample spec')
        self.stream = pa.pa_stream_new(self._pulse.context, self._name.encode(), samplespec, ffi.NULL)
        bufattr = ffi.new("pa_buffer_attr*")
        bufattr.maxlength = 2**32-1 # max buffer length
        bufattr.fragsize = 2**32-1 # block size
        bufattr.minreq = 2**32-1 # start requesting more data at this bytes
        bufattr.prebuf = 2**32-1 # start playback after this bytes are available
        bufattr.tlength = 2**32-1 # buffer length in bytes on server
        if self._type == 'output':
            pa.pa_stream_connect_playback(self.stream, self._id.encode(),
                                          bufattr, pa.PA_STREAM_NOFLAGS, ffi.NULL, ffi.NULL)
        elif self._type == 'input':
            pa.pa_stream_connect_record(self.stream, self._id.encode(), bufattr, pa.PA_STREAM_NOFLAGS)
        while pa.pa_stream_get_state(self.stream) == pa.PA_STREAM_CREATING:
            time.sleep(0.01)
        if pa.pa_stream_get_state(self.stream) != pa.PA_STREAM_READY:
            raise RuntimeError('Stream creation failed. Stream is in status {}'.format(pa.pa_stream_get_state(self.stream)))
        channel_map = pa.pa_stream_get_channel_map(self.stream)
        self.channels = int(channel_map.channels)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.channels = None
        operation = pa.pa_stream_drain(self.stream, ffi.NULL, ffi.NULL)
        self._pulse._block_operation(operation)
        pa.pa_stream_unref(self.stream)
        self._pulse.__exit__(exc_type, exc_value, traceback)
        self._pulse = None


class _Player(_Stream):

    def __init__(self, id, samplerate, name='outputstream'):
        super(_Player, self).__init__(id, samplerate, 'output', name)

    def play(self, data):
        data = numpy.array(data, dtype='float32')
        if data.ndim == 1:
            data = data[:, None] # force 2d
        if data.ndim != 2:
            raise TypeError('data must be 1d or 2d, not {}d'.format(data.ndim))
        if data.shape[1] == 1 and self.channels != 1:
            data = numpy.tile(data, [1, self.channels])
        if data.shape[1] != self.channels:
            raise TypeError('second dimension of data must be equal to the number of channels, not {}'.format(data.shape[1]))
        bytes = data.ravel().tostring()
        pa.pa_stream_write(self.stream, bytes, len(bytes), ffi.NULL, 0, pa.PA_SEEK_RELATIVE)


class Microphone:
    """A soundcard input. Can be used to record audio."""

    def __init__(self, *, id):
        self._id = id

    def __repr__(self):
        return '<Microphone {}>'.format(self._id)

    def recorder(self, samplerate):
        return _Recorder(self._id, samplerate)

    def record(self, samplerate, length):
        with _Recorder(self._id, samplerate) as r:
            return r.record(length)


class _Recorder(_Stream):

    def __init__(self, id, samplerate, name='outputstream'):
        super(_Recorder, self).__init__(id, samplerate, 'input', name)

    def record(self, num_frames):
        captured_frames = 0
        captured_data = []
        data_ptr = ffi.new('void**')
        nbytes_ptr = ffi.new('size_t*')
        while captured_frames < num_frames:
            if pa.pa_stream_readable_size(self.stream) > 0:
                pa.pa_stream_peek(self.stream, data_ptr, nbytes_ptr)
                chunk = numpy.fromstring(ffi.buffer(data_ptr[0], nbytes_ptr[0]), dtype='float32')
                pa.pa_stream_drop(self.stream)
                captured_data.append(chunk)
                captured_frames += len(chunk)/self.channels
            else:
                time.sleep(0.01)
        return numpy.reshape(numpy.concatenate(captured_data), [-1, self.channels])


class _PulseAudio:
    """Communcation with Pulseaudio."""

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
        if operation == ffi.NULL:
            return
        while pa.pa_operation_get_state(operation) == pa.PA_OPERATION_RUNNING:
            time.sleep(0.001)
        pa.pa_operation_unref(operation)

    def get_source_info_list(self):
        info = []
        @ffi.callback("pa_source_info_cb_t")
        def callback(context, source_info, eol, userdata):
            if not eol:
                info.append(dict(index=source_info.index,
                                 name=ffi.string(source_info.description).decode('utf-8'),
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


class AudioThread(threading.Thread):
    """Helper class for pulseaudio's main loop."""

    def __init__(self, mainloop):
        super(AudioThread, self).__init__()
        self.mainloop = mainloop

    def run(self):
        self.retval = ffi.new('int*', 0)
        pa.pa_mainloop_run(self.mainloop, self.retval)

    def stop(self):
        pa.pa_mainloop_quit(self.mainloop, self.retval[0])


if __name__ == '__main__':
    print('Speakers:')
    print(all_speakers())
    print('Default Speaker:')
    print(default_speaker())
    print('Microphones:')
    print(all_microphones())
    print('Default Microphone:')
    print(default_microphone())
    data = numpy.sin(numpy.linspace(0, 2*numpy.pi*100, 44100))
    default_speaker().play(data, 44100)
    # with default_speaker().player(44100) as s:
    #     s.play(data)
    #     s.play(data)
    data = default_microphone().record(44100, 44100)
    print(len(data))
    default_speaker().play(data/numpy.max(data), 44100)
    # import matplotlib.pyplot as plt
    # plt.plot(numpy.linspace(0, len(data)/44100, len(data)), data)
    # plt.show()
