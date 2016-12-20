import os
import cffi

_ffi = cffi.FFI()
_package_dir, _ = os.path.split(__file__)
with open(os.path.join(_package_dir, 'pulseaudio.py.h'), 'rt') as f:
    _ffi.cdef(f.read())

_pa = _ffi.dlopen('pulse')

import time
import re
import numpy


def all_speakers():
    """A list of all connected speakers."""
    with _PulseAudio() as p:
        return [_Speaker(id=s['id']) for s in p.sink_list]


def default_speaker():
    """The default speaker of the system."""
    with _PulseAudio() as p:
        name = p.server_info['default sink id']
        return get_speaker(name)


def get_speaker(id):
    """Get a specific speaker by a variety of means.

    id can be an int index, a pulseaudio id, a substring of the
    speaker name, or a fuzzy-matched pattern for the speaker name.

    """
    with _PulseAudio() as p:
        speakers = p.sink_list
    return _Speaker(id=_match_soundcard(id, speakers)['id'])


def all_microphones():
    """A list of all connected microphones."""
    with _PulseAudio() as p:
        return [_Microphone(id=m['id']) for m in p.source_list]


def default_microphone():
    """The default microphone of the system."""
    with _PulseAudio() as p:
        name = p.server_info['default source id']
        return get_microphone(name)


def get_microphone(id):
    """Get a specific microphone by a variety of means.

    id can be a pulseaudio id, a substring of the microphone name, or
    a fuzzy-matched pattern for the microphone name.

    """
    with _PulseAudio() as p:
        microphones = p.source_list
    return _Microphone(id=_match_soundcard(id, microphones)['id'])


def _match_soundcard(id, soundcards):
    """Find id in a list of soundcards.

    id can be a pulseaudio id, a substring of the microphone name, or
    a fuzzy-matched pattern for the microphone name.

    """
    soundcards_by_id = {soundcard['id']: soundcard for soundcard in soundcards}
    soundcards_by_name = {soundcard['name']: soundcard for soundcard in soundcards}
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

# TODO: implement name property
class _Speaker:
    """A soundcard output. Can be used to play audio.

    Use the `play` method to play one piece of audio, or use the
    `player` method to get a context manager for playing continuous
    audio.

    Properties:
    - `channels`: the number of available channels

    """

    def __init__(self, *, id):
        self._id = id

    def __repr__(self):
        return '<Speaker {} ({} channels)>'.format(self._id, self.channels)

    @property
    def channels(self):
        return self._get_info()['channels']

    def _get_info(self):
        with _PulseAudio() as p:
            return p.sink_info(self._id)

    def player(self, samplerate, blocksize=None):
        return _Player(self._id, samplerate, self.channels, blocksize=blocksize)

    def play(self, data, samplerate):
        with _Player(self._id, samplerate, self.channels) as s:
            s.play(data)


class _Microphone:
    """A soundcard input. Can be used to record audio.

    Use the `record` method to record a piece of audio, or use the
    `recorder` method to get a context manager for recording
    continuous audio.

    Properties:
    - `channels`: the number of available channels

    """

    def __init__(self, *, id):
        self._id = id

    def __repr__(self):
        return '<Microphone {} ({} channels)>'.format(self._id, self.channels)

    @property
    def channels(self):
        return self._get_info()['channels']

    def _get_info(self):
        with _PulseAudio() as p:
            return p.source_info(self._id)

    def recorder(self, samplerate, blocksize=None):
        return _Recorder(self._id, samplerate, self.channels, blocksize=blocksize)

    def record(self, samplerate, length):
        with _Recorder(self._id, samplerate, self.channels) as r:
            return r.record(length)


class _Stream:
    """A context manager for an active audio stream.

    This class is meant to be subclassed. Children must implement the
    `_connect_stream` method which takes a `pa_buffer_attr*` struct,
    and connects an appropriate stream.

    This context manager can only be entered once, and can not be used
    after it is closed.

    """

    def __init__(self, id, samplerate, channels, blocksize=None, name='outputstream'):
        self._id = id
        self._samplerate = samplerate
        self._name = name
        self._blocksize = blocksize
        self.channels = channels

    def __enter__(self):
        self._pulse = _PulseAudio()
        self._pulse.__enter__()
        samplespec = _ffi.new("pa_sample_spec*")
        samplespec.format = _pa.PA_SAMPLE_FLOAT32LE
        samplespec.rate = self._samplerate
        samplespec.channels = self.channels
        if not self._pulse._pa_sample_spec_valid(samplespec):
            raise RuntimeException('invalid sample spec')
        self.stream = self._pulse._pa_stream_new(self._pulse.context, self._name.encode(), samplespec, _ffi.NULL)
        bufattr = _ffi.new("pa_buffer_attr*")
        bufattr.maxlength = 2**32-1 # max buffer length
        bufattr.fragsize = self._blocksize*self.channels*4 if self._blocksize else 2**32-1 # recording block size
        bufattr.minreq = 2**32-1 # start requesting more data at this bytes
        bufattr.prebuf = 2**32-1 # start playback after this bytes are available
        bufattr.tlength = self._blocksize*self.channels*4 if self._blocksize else 2**32-1 # buffer length in bytes on server
        self._connect_stream(bufattr)
        while self._pulse._pa_stream_get_state(self.stream) not in [_pa.PA_STREAM_READY, _pa.PA_STREAM_FAILED]:
            time.sleep(0.01)
        if self._pulse._pa_stream_get_state(self.stream) == _pa.PA_STREAM_FAILED:
            raise RuntimeError('Stream creation failed. Stream is in status {}'
                               .format(self._pulse.pa_stream_get_state(self.stream)))
        channel_map = self._pulse._pa_stream_get_channel_map(self.stream)
        self.channels = int(channel_map.channels)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self._pulse._pa_stream_drain(self.stream, _ffi.NULL, _ffi.NULL)
            self._pulse._pa_stream_disconnect(self.stream)
            while self._pulse._pa_stream_get_state(self.stream) != _pa.PA_STREAM_TERMINATED:
                time.sleep(0.01)
                self._pulse._pa_stream_unref(self.stream)
        finally:
            # make sure that this definitely gets called no matter what:
            self._pulse.__exit__(exc_type, exc_value, traceback)


class _Player(_Stream):
    """A context manager for an active output stream.

    Audio playback is available as soon as the context manager is
    entered. Audio data can be played using the `play` method.
    Successive calls to `play` will queue up the audio one piece after
    another. If no audio is queued up, this will play silence.

    This context manager can only be entered once, and can not be used
    after it is closed.

    """

    def _connect_stream(self, bufattr):
        self._pulse._pa_stream_connect_playback(self.stream, self._id.encode(), bufattr, _pa.PA_STREAM_ADJUST_LATENCY,
                                                _ffi.NULL, _ffi.NULL)

    def play(self, data):
        """Play some audio data.

        Internally, all data is handled as float32 and with the
        appropriate number of channels. For maximum performance,
        provide data as a `frames × channels` float32 numpy array.

        If single-channel or one-dimensional data is given, this data
        will be played on all available channels.

        This function will return *before* all data has been played,
        so that additional data can be provided for gapless playback.
        The amount of buffering can be controlled through the
        blocksize of the player object.

        If data is provided faster than it is played, later pieces
        will be queued up and played one after another.

        """

        data = numpy.array(data, dtype='float32')
        if data.ndim == 1:
            data = data[:, None] # force 2d
        if data.ndim != 2:
            raise TypeError('data must be 1d or 2d, not {}d'.format(data.ndim))
        if data.shape[1] == 1 and self.channels != 1:
            data = numpy.tile(data, [1, self.channels])
        if data.shape[1] != self.channels:
            raise TypeError('second dimension of data must be equal to the number of channels, not {}'.format(data.shape[1]))
        bufattr = self._pulse._pa_stream_get_buffer_attr(self.stream)
        while data.nbytes > 0:
            nwrite = self._pulse._pa_stream_writable_size(self.stream) // 4
            if nwrite == 0:
                time.sleep(0.001)
                continue
            bytes = data[:nwrite].ravel().tostring()
            self._pulse._pa_stream_write(self.stream, bytes, len(bytes), _ffi.NULL, 0, _pa.PA_SEEK_RELATIVE)
            data = data[nwrite:]


class _Recorder(_Stream):
    """A context manager for an active input stream.

    Audio recording is available as soon as the context manager is
    entered. Recorded audio data can be read using the `record`
    method. If no audio data is available, `record` will block until
    the requested amount of audio data has been recorded.

    This context manager can only be entered once, and can not be used
    after it is closed.

    """

    def _connect_stream(self, bufattr):
        self._pulse._pa_stream_connect_record(self.stream, self._id.encode(), bufattr, _pa.PA_STREAM_ADJUST_LATENCY)

    def record(self, num_frames):
        """Record some audio data.

        The data will be returned as a `frames × channels` float32
        numpy array.

        This function will wait until `num_frames` frames have been
        recorded. However, the audio backend holds the final authority
        over how much audio data can be read at a time, so the
        returned amount of data will often be slightly larger than
        what was requested. The amount of buffering can be controlled
        through the blocksize of the recorder object.

        """

        captured_frames = 0
        captured_data = []
        data_ptr = _ffi.new('void**')
        nbytes_ptr = _ffi.new('size_t*')
        while captured_frames < num_frames:
            readable_bytes = self._pulse._pa_stream_readable_size(self.stream)
            if readable_bytes > 0:
                data_ptr[0] = _ffi.NULL
                nbytes_ptr[0] = 0
                self._pulse._pa_stream_peek(self.stream, data_ptr, nbytes_ptr)
                if data_ptr[0] != _ffi.NULL:
                    chunk = numpy.fromstring(_ffi.buffer(data_ptr[0], nbytes_ptr[0]), dtype='float32')
                if data_ptr[0] == _ffi.NULL and nbytes_ptr[0] != 0:
                    chunk = numpy.zeros(nbytes_ptr[0]//4, dtype='float32')
                if nbytes_ptr[0] > 0:
                    self._pulse._pa_stream_drop(self.stream)
                    captured_data.append(chunk)
                    captured_frames += len(chunk)/self.channels
            else:
                time.sleep(0.001)
        return numpy.reshape(numpy.concatenate(captured_data), [-1, self.channels])


def _lock(func):
    """Call a pulseaudio function while holding the mainloop lock."""
    def func_with_lock(*args, **kwargs):
        self = args[0]
        with self._lock_mainloop():
            return func(*args[1:], **kwargs)
    return func_with_lock


def _lock_and_block(func):
    """Call a pulseaudio function while holding the mainloop lock, and
       block until the operation has finished.

    Use this for pulseaudio functions that return a `pa_operation *`.

    """
    def func_with_lock(*args, **kwargs):
        self = args[0]
        with self._lock_mainloop():
            operation = func(*args[1:], **kwargs)
        self._block_operation(operation)
        self._pa_operation_unref(operation)
    return func_with_lock


class _PulseAudio:
    """Context manager for communcation with Pulseaudio.

    This instantiates the pulseaudio main loop, and a pulseaudio
    context. Together, these provide the building blocks for
    interacting with pulseaudio.

    Pulseaudio can be interacted with as soon as the context manager
    is entered.

    This can be used to query the pulseaudio server for sources,
    sinks, and server information, and provides thread-safe access to
    the main pulseaudio functions.

    Any function that would return a `pa_operation *` in pulseaudio
    will block until the operation has finished.

    This context manager can only be entered once, and can not be used
    after it is closed.

    """

    def __init__(self):
        # these functions are called before the mainloop starts, so we
        # don't need to hold the lock:
        self.mainloop = _pa.pa_threaded_mainloop_new()
        self.mainloop_api = _pa.pa_threaded_mainloop_get_api(self.mainloop)
        self.context = _pa.pa_context_new(self.mainloop_api, b"audio")
        _pa.pa_context_connect(self.context, _ffi.NULL, _pa.PA_CONTEXT_NOFLAGS, _ffi.NULL)

    def __enter__(self):
        _pa.pa_threaded_mainloop_start(self.mainloop)
        # from now on, all pulseaudio interactions needs to hold the
        # mainloop lock.
        while self._pa_context_get_state(self.context) != _pa.PA_CONTEXT_READY:
            time.sleep(0.001)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        operation = self._pa_context_drain(self.context, _ffi.NULL, _ffi.NULL)
        self._block_operation(operation)
        self._pa_context_disconnect(self.context)
        self._pa_context_unref(self.context)
        # no more mainloop locking necessary from here on:
        _pa.pa_threaded_mainloop_stop(self.mainloop)
        _pa.pa_threaded_mainloop_free(self.mainloop)

    def _block_operation(self, operation):
        """Wait until the operation has finished."""
        if operation == _ffi.NULL:
            return
        while self._pa_operation_get_state(operation) == _pa.PA_OPERATION_RUNNING:
            time.sleep(0.001)

    @property
    def source_list(self):
        """Return a list of dicts of information about available sources."""
        info = []
        @_ffi.callback("pa_source_info_cb_t")
        def callback(context, source_info, eol, userdata):
            if not eol:
                info.append(dict(name=_ffi.string(source_info.description).decode('utf-8'),
                                 id=_ffi.string(source_info.name).decode('utf-8')))
        self._pa_context_get_source_info_list(self.context, callback, _ffi.NULL)
        return info

    def source_info(self, id):
        """Return a dictionary of information about a specific source."""
        info = []
        @_ffi.callback("pa_source_info_cb_t")
        def callback(context, source_info, eol, userdata):
            if not eol:
                info.append(dict(latency=source_info.latency,
                                 configured_latency=source_info.configured_latency,
                                 channels=source_info.sample_spec.channels))
        self._pa_context_get_source_info_by_name(self.context, id.encode(), callback, _ffi.NULL)
        return info[0]

    @property
    def sink_list(self):
        """Return a list of dicts of information about available sinks."""
        info = []
        @_ffi.callback("pa_sink_info_cb_t")
        def callback(context, sink_info, eol, userdata):
            if not eol:
                info.append((dict(name=_ffi.string(sink_info.description).decode('utf-8'),
                                  id=_ffi.string(sink_info.name).decode('utf-8'))))
        self._pa_context_get_sink_info_list(self.context, callback, _ffi.NULL)
        return info

    def sink_info(self, id):
        """Return a dictionary of information about a specific sink."""
        info = []
        @_ffi.callback("pa_sink_info_cb_t")
        def callback(context, sink_info, eol, userdata):
            if not eol:
                info.append(dict(latency=sink_info.latency,
                                 configured_latency=sink_info.configured_latency,
                                 channels=sink_info.sample_spec.channels))
        self._pa_context_get_sink_info_by_name(self.context, id.encode(), callback, _ffi.NULL)
        return info[0]

    @property
    def server_info(self):
        """Return a dictionary of information about the server."""
        info = {}
        @_ffi.callback("pa_server_info_cb_t")
        def callback(context, server_info, userdata):
            info['server version'] = _ffi.string(server_info.server_version).decode('utf-8')
            info['server name'] = _ffi.string(server_info.server_name).decode('utf-8')
            info['default sink id'] = _ffi.string(server_info.default_sink_name).decode('utf-8')
            info['default source id'] = _ffi.string(server_info.default_source_name).decode('utf-8')
        self._pa_context_get_server_info(self.context, callback, _ffi.NULL)
        return info

    def _lock_mainloop(self):
        """Context manager for locking the mainloop.

        Hold this lock before calling any pulseaudio function while
        the mainloop is running.

        """

        class Lock():
            def __enter__(self_):
                _pa.pa_threaded_mainloop_lock(self.mainloop)
            def __exit__(self_, exc_type, exc_value, traceback):
                _pa.pa_threaded_mainloop_unlock(self.mainloop)
        return Lock()

    # create thread-safe versions of all used pulseaudio functions:
    _pa_context_get_source_info_list = _lock_and_block(_pa.pa_context_get_source_info_list)
    _pa_context_get_source_info_by_name = _lock_and_block(_pa.pa_context_get_source_info_by_name)
    _pa_context_get_sink_info_list = _lock_and_block(_pa.pa_context_get_sink_info_list)
    _pa_context_get_sink_info_by_name = _lock_and_block(_pa.pa_context_get_sink_info_by_name)
    _pa_context_get_server_info = _lock_and_block(_pa.pa_context_get_server_info)
    _pa_context_get_state = _lock(_pa.pa_context_get_state)
    _pa_context_drain = _lock(_pa.pa_context_drain)
    _pa_context_disconnect = _lock(_pa.pa_context_disconnect)
    _pa_context_unref = _lock(_pa.pa_context_unref)
    _pa_operation_get_state = _lock(_pa.pa_operation_get_state)
    _pa_operation_unref = _lock(_pa.pa_operation_unref)
    _pa_stream_get_state = _lock(_pa.pa_stream_get_state)
    _pa_sample_spec_valid = _lock(_pa.pa_sample_spec_valid)
    _pa_stream_new = _lock(_pa.pa_stream_new)
    _pa_stream_get_channel_map = _lock(_pa.pa_stream_get_channel_map)
    _pa_stream_drain = _lock_and_block(_pa.pa_stream_drain)
    _pa_stream_disconnect = _lock(_pa.pa_stream_disconnect)
    _pa_stream_unref = _lock(_pa.pa_stream_unref)
    _pa_stream_connect_record = _lock(_pa.pa_stream_connect_record)
    _pa_stream_readable_size = _lock(_pa.pa_stream_readable_size)
    _pa_stream_peek = _lock(_pa.pa_stream_peek)
    _pa_stream_drop = _lock(_pa.pa_stream_drop)
    _pa_stream_connect_playback = _lock(_pa.pa_stream_connect_playback)
    _pa_stream_get_buffer_attr = _lock(_pa.pa_stream_get_buffer_attr)
    _pa_stream_writable_size = _lock(_pa.pa_stream_writable_size)
    _pa_stream_write = _lock(_pa.pa_stream_write)
