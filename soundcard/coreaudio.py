import os
import cffi
import numpy
import collections
import time
import re
import math
import threading
import warnings

_ffi = cffi.FFI()
_package_dir, _ = os.path.split(__file__)
with open(os.path.join(_package_dir, 'coreaudio.py.h'), 'rt') as f:
    _ffi.cdef(f.read())

_ca = _ffi.dlopen('CoreAudio')
_au = _ffi.dlopen('AudioUnit')

from soundcard import coreaudioconstants as _cac


def all_speakers():
    """A list of all connected speakers."""
    device_ids = _CoreAudio.get_property(
        _cac.kAudioObjectSystemObject,
        _cac.kAudioHardwarePropertyDevices,
        "AudioObjectID")
    return [_Speaker(id=d) for d in device_ids
            if _Speaker(id=d).channels > 0]


def all_microphones(include_loopback=False):
    """A list of all connected microphones."""

    # macOS does not support loopback recording functionality
    if include_loopback:
        warnings.warn("macOS does not support loopback recording functionality", Warning)

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


def get_speaker(id):
    """Get a specific speaker by a variety of means.

    id can be an a CoreAudio id, a substring of the speaker name, or a
    fuzzy-matched pattern for the speaker name.

    """
    return _match_device(id, all_speakers())


def default_microphone():
    """The default microphone of the system."""
    device_id, = _CoreAudio.get_property(
        _cac.kAudioObjectSystemObject,
        _cac.kAudioHardwarePropertyDefaultInputDevice,
        "AudioObjectID")
    return _Microphone(id=device_id)


def get_microphone(id, include_loopback=False):
    """Get a specific microphone by a variety of means.

    id can be a CoreAudio id, a substring of the microphone name, or a
    fuzzy-matched pattern for the microphone name.

    """
    return _match_device(id, all_microphones(include_loopback))


def _match_device(id, devices):
    """Find id in a list of devices.

    id can be a CoreAudio id, a substring of the device name, or a
    fuzzy-matched pattern for the microphone name.

    """
    devices_by_id = {device.id: device for device in devices}
    devices_by_name = {device.name: device for device in devices}
    if id in devices_by_id:
        return devices_by_id[id]
    # try substring match:
    for name, device in devices_by_name.items():
        if id in name:
            return device
    # try fuzzy match:
    pattern = '.*'.join(id)
    for name, device in devices_by_name.items():
        if re.match(pattern, name):
            return device
    raise IndexError('no device with id {}'.format(id))


class _Soundcard:
    """A soundcard. This is meant to be subclassed.

    Properties:
    - `name`: the name of the soundcard

    """
    def __init__(self, *, id):
        self._id = id

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        name = _CoreAudio.get_property(
            self._id, _cac.kAudioObjectPropertyName, 'CFStringRef')
        return _CoreAudio.CFString_to_str(name)


class _Speaker(_Soundcard):
    """A soundcard output. Can be used to play audio.

    Use the `play` method to play one piece of audio, or use the
    `player` method to get a context manager for playing continuous
    audio.

    Properties:
    - `channels`: either the number of channels to play, or a list
      of channel indices. Index -1 is silence, and subsequent numbers
      are channel numbers (left, right, center, ...)
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
        if channels is None:
            channels = self.channels
        return _Player(self._id, samplerate, channels, blocksize)

    def play(self, data, samplerate, channels=None, blocksize=None):
        if channels is None and len(data.shape) == 2:
            channels = data.shape[1]
        elif channels is None:
            channels = self.channels
        with self.player(samplerate, channels, blocksize) as p:
            p.play(data)


class _Microphone(_Soundcard):
    """A soundcard input. Can be used to record audio.

    Use the `record` method to record a piece of audio, or use the
    `recorder` method to get a context manager for recording
    continuous audio.

    Properties:
    - `channels`: either the number of channels to record, or a list
      of channel indices. Index -1 is silence, and subsequent numbers
      are channel numbers (left, right, center, ...)
    - `name`: the name of the soundcard

    """

    @property
    def isloopback(self):
        return False

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
        if channels is None:
            channels = self.channels
        return _Recorder(self._id, samplerate, channels, blocksize)

    def record(self, numframes, samplerate, channels=None, blocksize=None):
        if channels is None:
            channels = self.channels
        with self.recorder(samplerate, channels, blocksize) as p:
            return p.record(numframes)


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
            for bufferidx in range(bufferlist.mNumberBuffers):
                dest = bufferlist.mBuffers[bufferidx]
                channels = dest.mNumberChannels
                bytes_written = 0
                to_write = dest.mDataByteSize
                while bytes_written < to_write:
                    if self._queue:
                        data = self._queue.popleft()
                        srcbuffer = _ffi.from_buffer(data)
                        numbytes = min(len(srcbuffer), to_write-bytes_written)
                        _ffi.memmove(dest.mData+bytes_written, srcbuffer, numbytes)
                        if numbytes < len(srcbuffer):
                            leftover = data[numbytes//4//channels:]
                            self._queue.appendleft(leftover)
                        bytes_written += numbytes
                    else:
                        src = bytearray(to_write-bytes_written)
                        _ffi.memmove(dest.mData+bytes_written, src, len(src))
                        bytes_written += len(src)
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

        data = numpy.asarray(data, dtype="float32", order='C')
        data[data>1] = 1
        data[data<-1] = -1
        if data.ndim == 1:
            data = data[:, None] # force 2d
        if data.ndim != 2:
            raise TypeError('data must be 1d or 2d, not {}d'.format(data.ndim))
        if data.shape[1] == 1 and self._au.channels != 1:
            data = numpy.tile(data, [1, self._au.channels])
        if data.shape[1] != self._au.channels:
            raise TypeError('second dimension of data must be equal to the number of channels, not {}'.format(data.shape[1]))
        idx = 0
        while idx < len(data)-self._au.blocksize:
            self._queue.append(data[idx:idx+self._au.blocksize])
            idx += self._au.blocksize
        self._queue.append(data[idx:])
        while self._queue and wait:
            time.sleep(0.001)

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

        # Input AudioUnits can't use non-native sample rates.
        # Therefore, if a non-native sample rate is requested, use a
        # resampled block size and resample later, manually:
        if iotype == 'input':
            self.resample = self.samplerate/samplerate
            # blocksize = math.ceil(blocksize*self.resample)
            # self.samplerate stays at its default value
        else:
            self.resample = 1
            self.samplerate = samplerate

        # there are two maximum block sizes for some reason:
        maxblocksize = min(self.blocksizerange[1],
                           self.maxblocksize)
        if self.blocksizerange[0] <= blocksize <= maxblocksize:
            self.blocksize = blocksize
        else:
            raise TypeError("blocksize must be between {} and {}"
                            .format(self.blocksizerange[0],
                                    maxblocksize))

        if isinstance(channels, collections.Iterable):
            if iotype == 'output':
                # invert channel map and fill with -1 ([2, 0] -> [1, -1, 0]):
                self.channels = len([c for c in channels if c >= 0])
                channelmap = [-1]*(max(channels)+1)
                for idx, c in enumerate(channels):
                    channelmap[c] = idx
                self.channelmap = channelmap
            else:
                self.channels = len(channels)
                self.channelmap = channels
        elif isinstance(channels, int):
            self.channels = channels
        else:
            raise TypeError('channels must be iterable or integer')

    def _set_property(self, property, scope, element, data):
        if '[]' in _ffi.typeof(data).cname:
            num_values = len(data)
        else:
            num_values = 1
        status = _au.AudioUnitSetProperty(self.ptr[0],
                                          property, scope, element,
                                          data, _ffi.sizeof(_ffi.typeof(data).item.cname)*num_values)
        if status != 0:
            raise RuntimeError(_cac.error_number_to_string(status))

    def _get_property(self, property, scope, element, type):
        datasize = _ffi.new("UInt32*")
        status = _au.AudioUnitGetPropertyInfo(self.ptr[0],
                                              property, scope, element,
                                              datasize, _ffi.NULL)
        num_values = datasize[0]//_ffi.sizeof(type)
        data = _ffi.new(type + '[{}]'.format(num_values))
        status = _au.AudioUnitGetProperty(self.ptr[0],
                                          property, scope, element,
                                          data, datasize)
        if status != 0:
            raise RuntimeError(_cac.error_number_to_string(status))
        if num_values == 1:
            return data[0]
        else:
            return data

    @property
    def device(self):
        return self._get_property(
            _cac.kAudioOutputUnitProperty_CurrentDevice,
            _cac.kAudioUnitScope_Global, 0, "UInt32")

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
            _cac.kAudioUnitScope_Input, 1, "UInt32")

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
            _cac.kAudioUnitScope_Output, 0, "UInt32")

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
            self._au_scope, self._au_element, "Float64")

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
            self._au_scope, self._au_element, "AudioStreamBasicDescription")
        assert streamformat
        return streamformat.mChannelsPerFrame

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
    def maxblocksize(self):
        maxblocksize = self._get_property(
            _cac.kAudioUnitProperty_MaximumFramesPerSlice,
            _cac.kAudioUnitScope_Global, 0, "UInt32")
        assert maxblocksize
        return maxblocksize

    @property
    def channelmap(self):
        scope = {2: 1, 1: 2}[self._au_scope]
        map = self._get_property(
            _cac.kAudioOutputUnitProperty_ChannelMap,
            scope, self._au_element,
            "SInt32")
        last_meaningful = max(idx for idx, c in enumerate(map) if c != -1)
        return list(map[0:last_meaningful+1])

    @channelmap.setter
    def channelmap(self, map):
        scope = {2: 1, 1: 2}[self._au_scope]
        cmap = _ffi.new("SInt32[]", map)
        self._set_property(
            _cac.kAudioOutputUnitProperty_ChannelMap,
            scope, self._au_element,
            cmap)

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


class _Resampler:
    def __init__(self, fromsamplerate, tosamplerate, channels):
        self.fromsamplerate = fromsamplerate
        self.tosamplerate = tosamplerate
        self.channels = channels

        fromstreamformat = _ffi.new(
            "AudioStreamBasicDescription*",
            dict(mSampleRate=self.fromsamplerate,
                 mFormatID=_cac.kAudioFormatLinearPCM,
                 mFormatFlags=_cac.kAudioFormatFlagIsFloat,
                 mFramesPerPacket=1,
                 mChannelsPerFrame=self.channels,
                 mBitsPerChannel=32,
                 mBytesPerPacket=self.channels * 4,
                 mBytesPerFrame=self.channels * 4))

        tostreamformat = _ffi.new(
            "AudioStreamBasicDescription*",
            dict(mSampleRate=self.tosamplerate,
                 mFormatID=_cac.kAudioFormatLinearPCM,
                 mFormatFlags=_cac.kAudioFormatFlagIsFloat,
                 mFramesPerPacket=1,
                 mChannelsPerFrame=self.channels,
                 mBitsPerChannel=32,
                 mBytesPerPacket=self.channels * 4,
                 mBytesPerFrame=self.channels * 4))

        self.audioconverter = _ffi.new("AudioConverterRef*")
        _au.AudioConverterNew(fromstreamformat, tostreamformat, self.audioconverter)

        @_ffi.callback("AudioConverterComplexInputDataProc")
        def converter_callback(converter, numberpackets, bufferlist, desc, userdata):
            return self.converter_callback(converter, numberpackets, bufferlist, desc, userdata)
        self._converter_callback = converter_callback

        self.queue = []

        self.blocksize = 512
        self.outbuffer = _ffi.new("AudioBufferList*", [1, 1])
        self.outbuffer.mNumberBuffers = 1
        self.outbuffer.mBuffers[0].mNumberChannels = self.channels
        self.outbuffer.mBuffers[0].mDataByteSize = self.blocksize*4*self.channels
        self.outdata = _ffi.new("Float32[]", self.blocksize*self.channels)
        self.outbuffer.mBuffers[0].mData = self.outdata
        self.outsize = _ffi.new("UInt32*")

    def converter_callback(self, converter, numberpackets, bufferlist, desc, userdata):
        numframes = min(numberpackets[0], len(self.todo), self.blocksize)
        raw_data = self.todo[:numframes].tostring()
        _ffi.memmove(self.outdata, raw_data, len(raw_data))
        bufferlist[0].mBuffers[0].mDataByteSize = len(raw_data)
        bufferlist[0].mBuffers[0].mData = self.outdata
        numberpackets[0] = numframes
        self.todo = self.todo[numframes:]

        if len(self.todo) == 0 and numframes == 0:
            return -1
        return 0

    def resample(self, data):
        self.todo = numpy.array(data, dtype='float32')
        while len(self.todo) > 0:
            self.outsize[0] = self.blocksize

            status = _au.AudioConverterFillComplexBuffer(self.audioconverter[0],
                                                         self._converter_callback,
                                                         _ffi.NULL,
                                                         self.outsize,
                                                         self.outbuffer,
                                                         _ffi.NULL)

            if status != 0 and status != -1:
                raise RuntimeError('error during sample rate conversion:', status)

            array = numpy.frombuffer(_ffi.buffer(self.outdata), dtype='float32').copy()

            self.queue.append(array[:self.outsize[0]*self.channels])

        converted_data = numpy.concatenate(self.queue)
        self.queue.clear()

        return converted_data

    def __del__(self):
        _au.AudioConverterDispose(self.audioconverter[0])


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
        self._resampler = _Resampler(self._au.samplerate, samplerate, self._au.channels)
        self._record_event = threading.Event()

    def __enter__(self):
        self._queue = collections.deque()
        self._pending_chunk = numpy.zeros([0])

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
                print('error during recording:', status)

            data = numpy.frombuffer(_ffi.buffer(data), dtype='float32')
            self._queue.append(data)
            self._record_event.set()
            return status

        self._au.set_callback(input_callback)
        self._au.start()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._au.close()

    def _record_chunk(self):
        """Record one chunk of audio data, as returned by core audio

        The data will be returned as a 1D numpy array, which will be used by
        the `record` method. This function is the interface of the `_Recorder`
        object with core audio.
        """
        while not self._queue:
            self._record_event.wait()
            self._record_event.clear()
        return self._queue.popleft()

    def record(self, numframes=None):
        """Record a block of audio data.

        The data will be returned as a frames × channels float32 numpy array.
        This function will wait until numframes frames have been recorded.
        If numframes is given, it will return exactly `numframes` frames,
        and buffer the rest for later.

        If numframes is None, it will return whatever the audio backend
        has available right now.
        Use this if latency must be kept to a minimum, but be aware that
        block sizes can change at the whims of the audio backend.

        If using `record` with `numframes=None` after using `record` with a
        required `numframes`, the last buffered frame will be returned along
        with the new recorded block.
        (If you want to empty the last buffered frame instead, use `flush`)

        """

        if numframes is None:
            blocks = [self._pending_chunk, self._record_chunk()]
            self._pending_chunk = numpy.zeros([0])
        else:
            blocks = [self._pending_chunk]
            self._pending_chunk = numpy.zeros([0])
            recorded_frames = len(blocks[0])
            required_frames = int(numframes/self._au.resample)*self._au.channels
            while recorded_frames < required_frames:
                block = self._record_chunk()
                blocks.append(block)
                recorded_frames += len(block)
            if recorded_frames > required_frames:
                to_split = -(recorded_frames-required_frames)
                blocks[-1], self._pending_chunk = numpy.split(blocks[-1], [to_split])

        data = numpy.concatenate(blocks)

        if self._au.channels != 1:
            data = data.reshape([-1, self._au.channels])

        if self._au.resample != 1:
            data = self._resampler.resample(data)

        if self._au.channels != 1:
            data = data.reshape([-1, self._au.channels])

        return data

    def flush(self):
        """Return the last pending chunk
        After using the record method, this will return the last incomplete
        chunk and delete it.

        """
        last_chunk = numpy.reshape(self._pending_chunk, [-1, self._au.channels])
        self._pending_chunk = numpy.zeros([0])
        return last_chunk
