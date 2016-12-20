import os
import cffi
import numpy as np
import collections
import time

_ffi = cffi.FFI()
_package_dir, _ = os.path.split(__file__)
with open(os.path.join(_package_dir, 'coreaudio.py.h'), 'rt') as f:
    _ffi.cdef(f.read())

_ca = _ffi.dlopen('CoreAudio')
_au = _ffi.dlopen('AudioUnit')

import coreaudioconstants as _cac


def all_speakers():
    """A list of all connected speakers."""
    device_ids = _CoreAudio.get_property(
        _cac.kAudioObjectSystemObject,
        _cac.kAudioHardwarePropertyDevices,
        "AudioObjectID")
    return [_Speaker(id=d) for d in device_ids
            if _Speaker(id=d).channels > 0]


def all_microphones():
    """A list of all connected microphones."""
    device_ids = _CoreAudio.get_property(
        _cac.kAudioObjectSystemObject,
        _cac.kAudioHardwarePropertyDevices,
        "AudioObjectID")
    return [_Microphone(id=d) for d in device_ids
            if _Microphone(id=d).channels > 0]


def default_speaker():
    """The default speaker of the system."""
    device_id, = _CoreAudio.get_property(
        _cac.kAudioObjectSystemObject,
        _cac.kAudioHardwarePropertyDefaultOutputDevice,
        "AudioObjectID")
    return _Speaker(id=device_id)


def default_microphone():
    """The default microphone of the system."""
    device_id, = _CoreAudio.get_property(
        _cac.kAudioObjectSystemObject,
        _cac.kAudioHardwarePropertyDefaultInputDevice,
        "AudioObjectID")
    return _Microphone(id=device_id)


class _Soundcard:
    """A soundcard. This is meant to be subclassed.

    Properties:
    - `name`: the name of the soundcard

    """
    def __init__(self, *, id):
        self._id = id

    @property
    def name(self):
        name = _CoreAudio.get_property(
            self._id, _cac.kAudioObjectPropertyName, 'CFStringRef')
        return _CoreAudio.CFString_to_str(name)

# TODO: implement soundcard searching
class _Speaker(_Soundcard):
    """A soundcard output. Can be used to play audio.

    Use the `play` method to play one piece of audio, or use the
    `player` method to get a context manager for playing continuous
    audio.

    Properties:
    - `channels`: the number of available channels
    - `name`: the name of the soundcard

    """

    @property
    def channels(self):
        bufferlist = _CoreAudio.get_property(
            self._id,
            _cac.kAudioDevicePropertyStreamConfiguration,
            'AudioBufferList', scope=_cac.kAudioObjectPropertyScopeOutput)
        if bufferlist and bufferlist[0].mNumberBuffers > 0:
            return bufferlist[0].mBuffers[0].mNumberChannels
        else:
            return 0

    def __repr__(self):
        return '<Speaker {} ({} channels)>'.format(self.name, self.channels)

    def player(self, samplerate, channels=None, blocksize=None):
        return _Player(self._id, samplerate, channels or self.channels, blocksize=blocksize)

    def play(self, data, samplerate, channels=None, blocksize=None):
        with self.player(samplerate, channels or self.channels, blocksize) as p:
            p.play(data)


class _Microphone(_Soundcard):
    """A soundcard input. Can be used to record audio.

    Use the `record` method to record a piece of audio, or use the
    `recorder` method to get a context manager for recording
    continuous audio.

    Properties:
    - `channels`: the number of available channels
    - `name`: the name of the soundcard

    """

    @property
    def channels(self):
        bufferlist = _CoreAudio.get_property(
            self._id,
            _cac.kAudioDevicePropertyStreamConfiguration,
            'AudioBufferList', scope=_cac.kAudioObjectPropertyScopeInput)
        if bufferlist and bufferlist[0].mNumberBuffers > 0:
            return bufferlist[0].mBuffers[0].mNumberChannels
        else:
            return 0

    def __repr__(self):
        return '<Microphone {} ({} channels)>'.format(self.name, self.channels)

    def recorder(self, samplerate, channels=None, blocksize=None):
        return _Recorder(self._id, samplerate, channels or self.channels)

    def record(self, numframes, samplerate, channels=None, blocksize=None):
        with self.recorder(samplerate, channels or self.channels, blocksize) as p:
            p.record(numframes)


class _CoreAudio:
    """A helper class for interacting with CoreAudio."""

    @staticmethod
    def get_property(target, selector, ctype, scope=_cac.kAudioObjectPropertyScopeGlobal):
        """Get a CoreAudio property.

        This might include things like a list of available sound
        cards, or various meta data about those sound cards.

        Arguments:
        - `target`: The AudioObject that the property belongs to
        - `selector`: The Selector for this property
        - `scope`: The Scope for this property
        - `ctype`: The type of the property

        Returns:
        A list of objects of type `ctype`

        """

        prop = _ffi.new("AudioObjectPropertyAddress*",
                        {'mSelector': selector,
                         'mScope': scope,
                         'mElement': _cac.kAudioObjectPropertyElementMaster})

        has_prop = _ca.AudioObjectHasProperty(target, prop)
        assert has_prop == 1, 'Core Audio does not have the requested property'

        size = _ffi.new("UInt32*")
        err = _ca.AudioObjectGetPropertyDataSize(target, prop, 0, _ffi.NULL, size)
        assert err == 0, "Can't get Core Audio property size"
        num_values = int(size[0]//_ffi.sizeof(ctype))

        prop_data = _ffi.new(ctype+'[]', num_values)
        err = _ca.AudioObjectGetPropertyData(target, prop, 0, _ffi.NULL,
                                             size, prop_data)
        assert err == 0, "Can't get Core Audio property data"

        return [prop_data[idx] for idx in range(num_values)]

    @staticmethod
    def set_property(target, selector, prop_data, scope=_cac.kAudioObjectPropertyScopeGlobal):
        """Set a CoreAudio property.

        This is typically a piece of meta data about a sound card.

        Arguments:
        - `target`: The AudioObject that the property belongs to
        - `selector`: The Selector for this property
        - `scope`: The Scope for this property
        - `prop_data`: The new property value

        """

        prop = _ffi.new("AudioObjectPropertyAddress*",
                        {'mSelector': selector,
                         'mScope': scope,
                         'mElement': _cac.kAudioObjectPropertyElementMaster})

        err = _ca.AudioObjectSetPropertyData(target, prop, 0, _ffi.NULL,
                                             _ffi.sizeof(_ffi.typeof(prop_data).item.cname), prop_data)
        assert err == 0, "Can't set Core Audio property data"

    @staticmethod
    def CFString_to_str(cfstrptr):
        """Converts a CFStringRef to a Python str."""

        str_length = _ca.CFStringGetLength(cfstrptr[0])
        str_buffer = _ffi.new('char[]', str_length+1)

        err = _ca.CFStringGetCString(cfstrptr[0], str_buffer, str_length+1, _cac.kCFStringEncodingUTF8)
        assert err == 1, "Could not decode string"

        return _ffi.string(str_buffer).decode()


class _Player:
    """A context manager for an active output stream.

    Audio playback is available as soon as the context manager is
    entered. Audio data can be played using the `play` method.
    Successive calls to `play` will queue up the audio one piece after
    another. If no audio is queued up, this will play silence.

    This context manager can only be entered once, and can not be used
    after it is closed.

    """

    def __init__(self, id, samplerate, channels, blocksize=None):
        self._au = _AudioUnit("output", id, samplerate, channels, blocksize)

    def __enter__(self):
        self._queue = collections.deque()

        @_ffi.callback("AURenderCallback")
        def render_callback(userdata, actionflags, timestamp,
                            busnumber, numframes, bufferlist):
            if self._queue:
                src = self._queue.popleft()
            else:
                src = np.zeros(numframes, "float32")
            srcbuffer = _ffi.from_buffer(src)

            for bufferidx in range(bufferlist.mNumberBuffers):
                dest = bufferlist.mBuffers[bufferidx]
                destbuffer = _ffi.buffer(dest.mData, dest.mDataByteSize)
                _ffi.memmove(destbuffer, srcbuffer, len(srcbuffer))
            return 0

        self._au.set_callback(render_callback)

        self._au.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._au.close()

    def play(self, data, wait=True):
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

        data = np.asarray(data*0.5, dtype="float32")
        data[data>1] = 1
        data[data<-1] = -1
        idx = 0
        while idx < len(data)-self._au.blocksize:
            self._queue.append(data[idx:idx+self._au.blocksize])
            idx += self._au.blocksize
        self._queue.append(data[idx:])
        while self._queue and wait:
            time.sleep(0.001)


class _Recorder:
    """A context manager for an active input stream.

    Audio recording is available as soon as the context manager is
    entered. Recorded audio data can be read using the `record`
    method. If no audio data is available, `record` will block until
    the requested amount of audio data has been recorded.

    This context manager can only be entered once, and can not be used
    after it is closed.

    """

    def __init__(self, id, samplerate, channels, blocksize=None):
        self._au = _AudioUnit("input", id, samplerate, channels, blocksize)

    def __enter__(self):
        self._queue = collections.deque()

        channels = self._au.channels
        au = self._au.ptr[0]

        @_ffi.callback("AURenderCallback")
        def input_callback(userdata, actionflags, timestamp,
                           busnumber, numframes, bufferlist):
            bufferlist = _ffi.new("AudioBufferList*", [1, 1])
            bufferlist.mNumberBuffers = 1
            bufferlist.mBuffers[0].mNumberChannels = channels
            bufferlist.mBuffers[0].mDataByteSize = numframes * 4 * channels
            data = _ffi.new("Float32[]", numframes * channels)
            bufferlist.mBuffers[0].mData = data

            status = _au.AudioUnitRender(au,
                                         actionflags,
                                         timestamp,
                                         busnumber,
                                         numframes,
                                         bufferlist)

            if status != 0:
                print(status)

            self._queue.append(data)
            return status

        self._au.set_callback(input_callback)
        self._au.start()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._au.close()

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

        while len(self._queue) < num_frames/self._au.blocksize:
            time.sleep(0.001)

        data = np.concatenate([np.frombuffer(_ffi.buffer(d), dtype='float32') for d in self._queue])
        self._queue.clear()
        return data


class _AudioUnit:
    """Communication helper with AudioUnits.

    This provides an abstraction over a single AudioUnit. Can be used
    as soon as it instatiated.

    Properties:
    - `enableinput`, `enableoutput`: set up the AudioUnit for playback
       or recording. It is not possible to record and play at the same
       time.
    - `device`: The numeric ID of the underlying CoreAudio device.
    - `blocksize`: The amount of buffering in the AudioUnit. Values
       outside of `blocksizerange` will be silently clamped to that
       range.
    - `blocksizerange`: The minimum and maximum possible block size.
    - `samplerate`: The sampling rate of the CoreAudio device. This
       will lead to errors if changed in a recording AudioUnit.
    - `channels`: The number of channels of the AudioUnit.

    """

    def __init__(self, iotype, device, samplerate, channels, blocksize):
        self._iotype = iotype

        desc = _ffi.new(
            "AudioComponentDescription*",
            dict(componentType=_cac.kAudioUnitType_Output,
                 componentSubType=_cac.kAudioUnitSubType_HALOutput,
                 componentFlags=0,
                 componentFlagsMask=0,
                 componentManufacturer=_cac.kAudioUnitManufacturer_Apple))

        audiocomponent = _au.AudioComponentFindNext(_ffi.NULL, desc)
        if not audiocomponent:
            raise Runtime("could not find audio component")
        self.ptr = _ffi.new("AudioComponentInstance*")
        status = _au.AudioComponentInstanceNew(audiocomponent, self.ptr)
        if status:
            raise RuntimeError(_cac.error_number_to_string(status))

        if iotype == 'input':
            self.enableinput = True
            self.enableoutput = False
            self._au_scope = _cac.kAudioUnitScope_Output
            self._au_element = 1
        elif iotype == 'output':
            self.enableinput = False
            self.enableoutput = True
            self._au_scope = _cac.kAudioUnitScope_Input
            self._au_element = 0

        self.device = device

        blocksize = blocksize or self.blocksize
        if self.blocksizerange[0] <= blocksize <= self.blocksizerange[1]:
            self.blocksize = blocksize
        else:
            raise TypeError("blocksize must be between {} and {}"
                            .format(self.blocksizerange[0],
                                    self.blocksizerange[1]))

        self.samplerate = samplerate
        self.channels = channels

    def _set_property(self, property, scope, element, data):
        status = _au.AudioUnitSetProperty(self.ptr[0],
                                          property, scope, element,
                                          data, _ffi.sizeof(_ffi.typeof(data).item.cname))
        if status != 0:
            raise RuntimeError(_cac.error_number_to_string(status))

    def _get_property(self, property, scope, element, type):
        data = _ffi.new(type)
        datasize = _ffi.new("UInt32*", _ffi.sizeof(_ffi.typeof(data).item.cname))
        status = _au.AudioUnitGetProperty(self.ptr[0],
                                          property, scope, element,
                                          data, datasize)
        if status != 0:
            raise RuntimeError(_cac.error_number_to_string(status))
        return data

    @property
    def device(self):
        return self._get_property(
            _cac.kAudioOutputUnitProperty_CurrentDevice,
            _cac.kAudioUnitScope_Global, 0, "UInt32*")[0]

    @device.setter
    def device(self, dev):
        data = _ffi.new("UInt32*", dev)
        self._set_property(
            _cac.kAudioOutputUnitProperty_CurrentDevice,
            _cac.kAudioUnitScope_Global, 0, data)

    @property
    def enableinput(self):
        return self._get_property(
            _cac.kAudioOutputUnitProperty_EnableIO,
            _cac.kAudioUnitScope_Input, 1, "UInt32*")

    @enableinput.setter
    def enableinput(self, yesno):
        data = _ffi.new("UInt32*", yesno)
        self._set_property(
            _cac.kAudioOutputUnitProperty_EnableIO,
            _cac.kAudioUnitScope_Input, 1, data)

    @property
    def enableoutput(self):
        return self._get_property(
            _cac.kAudioOutputUnitProperty_EnableIO,
            _cac.kAudioUnitScope_Output, 0, "UInt32*")[0]

    @enableoutput.setter
    def enableoutput(self, yesno):
        data = _ffi.new("UInt32*", yesno)
        self._set_property(
            _cac.kAudioOutputUnitProperty_EnableIO,
            _cac.kAudioUnitScope_Output, 0, data)

    @property
    def samplerate(self):
        return self._get_property(
            _cac.kAudioUnitProperty_SampleRate,
            self._au_scope, self._au_element, "Float64*")[0]

    @samplerate.setter
    def samplerate(self, samplerate):
        data = _ffi.new("Float64*", samplerate)
        self._set_property(
            _cac.kAudioUnitProperty_SampleRate,
            self._au_scope, self._au_element, data)

    @property
    def channels(self):
        streamformat = self._get_property(
            _cac.kAudioUnitProperty_StreamFormat,
            self._au_scope, self._au_element, "AudioStreamBasicDescription*")
        assert streamformat
        return streamformat[0].mChannelsPerFrame

    @channels.setter
    def channels(self, channels):
        streamformat = _ffi.new(
            "AudioStreamBasicDescription*",
            dict(mSampleRate=self.samplerate,
                 mFormatID=_cac.kAudioFormatLinearPCM,
                 mFormatFlags=_cac.kAudioFormatFlagIsFloat,
                 mFramesPerPacket=1,
                 mChannelsPerFrame=channels,
                 mBitsPerChannel=32,
                 mBytesPerPacket=channels * 4,
                 mBytesPerFrame=channels * 4))
        self._set_property(
            _cac.kAudioUnitProperty_StreamFormat,
            self._au_scope, self._au_element, streamformat)

    @property
    def blocksizerange(self):
        framesizerange = _CoreAudio.get_property(
            self.device,
            _cac.kAudioDevicePropertyBufferFrameSizeRange,
            'AudioValueRange', scope=_cac.kAudioObjectPropertyScopeOutput)
        assert framesizerange
        return framesizerange[0].mMinimum, framesizerange[0].mMaximum

    @property
    def blocksize(self):
        framesize = _CoreAudio.get_property(
            self.device,
            _cac.kAudioDevicePropertyBufferFrameSize,
            'UInt32', scope=_cac.kAudioObjectPropertyScopeOutput)
        assert framesize
        return framesize[0]

    @blocksize.setter
    def blocksize(self, blocksize):
        framesize = _ffi.new("UInt32*", blocksize)
        status = _CoreAudio.set_property(
            self.device,
            _cac.kAudioDevicePropertyBufferFrameSize,
            framesize, scope=_cac.kAudioObjectPropertyScopeOutput)

    def set_callback(self, callback):
        """Set a callback function for the AudioUnit. """

        if self._iotype == 'input':
            callbacktype = _cac.kAudioOutputUnitProperty_SetInputCallback
        elif self._iotype == 'output':
            callbacktype = _cac.kAudioUnitProperty_SetRenderCallback

        self._callback = callback
        callbackstruct = _ffi.new(
            "AURenderCallbackStruct*",
            dict(inputProc=callback,
                 inputProcRefCon=_ffi.NULL))
        self._set_property(
            callbacktype,
            _cac.kAudioUnitScope_Global, 0, callbackstruct)

    def start(self):
        """Start processing audio, and start calling the callback."""

        status = _au.AudioUnitInitialize(self.ptr[0])
        if status:
            raise RuntimeError(_cac.error_number_to_string(status))
        status = _au.AudioOutputUnitStart(self.ptr[0])
        if status:
            raise RuntimeError(_cac.error_number_to_string(status))

    def close(self):
        """Stop processing audio, and stop calling the callback."""

        status = _au.AudioOutputUnitStop(self.ptr[0])
        if status:
            raise RuntimeError(_cac.error_number_to_string(status))
        status = _au.AudioComponentInstanceDispose(self.ptr[0])
        if status:
            raise RuntimeError(_cac.error_number_to_string(status))
        del self.ptr


# Here's how to do it: http://atastypixel.com/blog/using-remoteio-audio-unit/
# https://developer.apple.com/library/content/technotes/tn2091/_index.html
