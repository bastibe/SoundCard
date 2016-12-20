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
    """A list of all known speakers."""
    device_ids = _get_core_audio_property(_cac.kAudioObjectSystemObject,
                                          _cac.kAudioHardwarePropertyDevices,
                                          "AudioObjectID")
    return [_Speaker(id=d) for d in device_ids
            if _Speaker(id=d).channels > 0]

def all_microphones():
    """A list of all known microphones."""
    device_ids = _get_core_audio_property(_cac.kAudioObjectSystemObject,
                                          _cac.kAudioHardwarePropertyDevices,
                                          "AudioObjectID")
    return [_Microphone(id=d) for d in device_ids
            if _Microphone(id=d).channels > 0]

def default_speaker():
    device_id, = _get_core_audio_property(_cac.kAudioObjectSystemObject,
                                          _cac.kAudioHardwarePropertyDefaultOutputDevice,
                                          "AudioObjectID")
    return _Speaker(id=device_id)

def default_microphone():
    device_id, = _get_core_audio_property(_cac.kAudioObjectSystemObject,
                                          _cac.kAudioHardwarePropertyDefaultInputDevice,
                                          "AudioObjectID")
    return _Microphone(id=device_id)


class _Soundcard:
    def __init__(self, *, id):
        self._id = id

    def __repr__(self):
        name = _get_core_audio_property(self._id, _cac.kAudioObjectPropertyName,
                                        'CFStringRef')
        return '<SoundCard {} ({} channels)>'.format(_CFString_to_str(name), self.channels)


class _Speaker(_Soundcard):
    @property
    def channels(self):
        bufferlist = _get_core_audio_property(
            self._id,
            _cac.kAudioDevicePropertyStreamConfiguration,
            'AudioBufferList', scope=_cac.kAudioObjectPropertyScopeOutput)
        if bufferlist and bufferlist[0].mNumberBuffers > 0:
            return bufferlist[0].mBuffers[0].mNumberChannels
        else:
            return 0

    def player(self, samplerate, channels=None, blocksize=None):
        return _Player(self._id, samplerate, channels or self.channels, blocksize=blocksize)

    def play(self, data, samplerate, channels=None, blocksize=None):
        with self.player(samplerate, channels or self.channels, blocksize) as p:
            p.play(data)


class _Microphone(_Soundcard):
    @property
    def channels(self):
        bufferlist = _get_core_audio_property(
            self._id,
            _cac.kAudioDevicePropertyStreamConfiguration,
            'AudioBufferList', scope=_cac.kAudioObjectPropertyScopeInput)
        if bufferlist and bufferlist[0].mNumberBuffers > 0:
            return bufferlist[0].mBuffers[0].mNumberChannels
        else:
            return 0

    def recorder(self, samplerate, channels=None, blocksize=None):
        return _Recorder(self._id, samplerate, channels or self.channels)

    def record(self, numframes, samplerate, channels=None, blocksize=None):
        with self.recorder(samplerate, channels or self.channels, blocksize) as p:
            p.record(numframes)


def _get_core_audio_property(target, selector, ctype, scope=_cac.kAudioObjectPropertyScopeGlobal):
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

def _set_core_audio_property(target, selector, prop_data, scope=_cac.kAudioObjectPropertyScopeGlobal):
    prop = _ffi.new("AudioObjectPropertyAddress*",
                    {'mSelector': selector,
                     'mScope': scope,
                     'mElement': _cac.kAudioObjectPropertyElementMaster})

    err = _ca.AudioObjectSetPropertyData(target, prop, 0, _ffi.NULL,
                                         _ffi.sizeof(_ffi.typeof(prop_data).item.cname), prop_data)
    assert err == 0, "Can't set Core Audio property data"

def _CFString_to_str(str_data):
    str_length = _ca.CFStringGetLength(str_data[0])
    str_buffer = _ffi.new('char[]', str_length+1)

    err = _ca.CFStringGetCString(str_data[0], str_buffer, str_length+1, _cac.kCFStringEncodingUTF8)
    assert err == 1, "Could not decode string"

    return _ffi.string(str_buffer).decode()


class _Stream:
    def __init__(self, id, samplerate, channels, blocksize=None):
        self._id = id
        self._samplerate = samplerate
        self._blocksize = blocksize
        self.channels = channels

    def __exit__(self, exc_type, exc_value, traceback):
        status = _au.AudioOutputUnitStop(self._audiounit[0])
        if status:
            raise RuntimeError(_cac.error_number_to_string(status))
        status = _au.AudioComponentInstanceDispose(self._audiounit[0])
        if status:
            raise RuntimeError(_cac.error_number_to_string(status))
        del self._audiounit

    def _set_property(self, property, scope, element, data):
        status = _au.AudioUnitSetProperty(self._audiounit[0],
                                          property, scope, element,
                                          data, _ffi.sizeof(_ffi.typeof(data).item.cname))
        if status != 0:
            raise RuntimeError(_cac.error_number_to_string(status))

    def _get_property(self, property, scope, element, type):
        data = _ffi.new(type)
        datasize = _ffi.new("UInt32*")
        status = _au.AudioUnitGetProperty(self._audiounit[0],
                                          property, scope, element,
                                          data, datasize)
        print(data[0], datasize[0])
        if status != 0:
            raise RuntimeError(_cac.error_number_to_string(status))
        return data

    def _set_blocksize(self):
        if self._blocksize is not None:
            framesizerange = _get_core_audio_property(
                self._id,
                _cac.kAudioDevicePropertyBufferFrameSizeRange,
                'AudioValueRange', scope=_cac.kAudioObjectPropertyScopeOutput)
            assert framesizerange
            if not(framesizerange[0].mMinimum <= self._blocksize <= framesizerange[0].mMaximum):
                raise RuntimeError("blocksize must be between {} and {} (is {})"
                                   .format(framesizerange[0].mMinimum,
                                           framesizerange[0].mMaximum,
                                           self._blocksize))

            framesize = _ffi.new("UInt32*", self._blocksize)
            status = _set_core_audio_property(
                self._id,
                _cac.kAudioDevicePropertyBufferFrameSize,
                framesize, scope=_cac.kAudioObjectPropertyScopeOutput)
        else:
            framesize = _get_core_audio_property(
                self._id,
                _cac.kAudioDevicePropertyBufferFrameSize,
                'UInt32', scope=_cac.kAudioObjectPropertyScopeOutput)
            assert framesize
            self._blocksize = framesize[0]

    def _create_audiounit(self):
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
        self._audiounit = _ffi.new("AudioComponentInstance*")
        status = _au.AudioComponentInstanceNew(audiocomponent, self._audiounit)
        if status:
            raise RuntimeError(_cac.error_number_to_string(status))

    def _set_device(self):
        data = _ffi.new("UInt32*", self._id)
        self._set_property(
            _cac.kAudioOutputUnitProperty_CurrentDevice,
            _cac.kAudioUnitScope_Global, 0, data)

    def _set_enable_io(self, scope, element):
        data = _ffi.new("UInt32*", 1)
        self._set_property(
            _cac.kAudioOutputUnitProperty_EnableIO,
            scope, element, data)

    def _set_disable_io(self, scope, element):
        data = _ffi.new("UInt32*", 0)
        self._set_property(
            _cac.kAudioOutputUnitProperty_EnableIO,
            scope, element, data)

    def _set_samplerate(self, scope, element):
        data = _ffi.new("Float64*", self._samplerate)
        self._set_property(
            _cac.kAudioUnitProperty_SampleRate,
            scope, element, data)

    def _set_stream_format(self, scope, element):
        streamformat = _ffi.new(
            "AudioStreamBasicDescription*",
            dict(mSampleRate=self._samplerate,
                 mFormatID = _cac.kAudioFormatLinearPCM,
                 mFormatFlags=_cac.kAudioFormatFlagIsFloat,
                 mFramesPerPacket=1, # uncompressed audio
                 mChannelsPerFrame=self.channels,
                 mBitsPerChannel=32,
                 mBytesPerPacket=self.channels * 4,
                 mBytesPerFrame=self.channels * 4))
        self._set_property(
            _cac.kAudioUnitProperty_StreamFormat,
            scope, element, streamformat)

    def _set_callback(self, callback, callbacktype):
        self._render_callback = callback
        callbackstruct = _ffi.new(
            "AURenderCallbackStruct*",
            dict(inputProc=callback,
                 inputProcRefCon=_ffi.NULL))
        self._set_property(
            callbacktype,
            _cac.kAudioUnitScope_Global, 0, callbackstruct)


class _Player(_Stream):
    def __enter__(self):
        self._set_blocksize()
        self._create_audiounit()
        self._set_enable_io(_cac.kAudioUnitScope_Output, 0)
        self._set_disable_io(_cac.kAudioUnitScope_Input, 1)
        self._set_device()
        self._set_samplerate(_cac.kAudioUnitScope_Input, 0)
        self._set_stream_format(_cac.kAudioUnitScope_Input, 0)

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

        self._set_callback(render_callback, _cac.kAudioUnitProperty_SetRenderCallback)

        status = _au.AudioUnitInitialize(self._audiounit[0])
        if status:
            raise RuntimeError(_cac.error_number_to_string(status))
        status = _au.AudioOutputUnitStart(self._audiounit[0])
        if status:
            raise RuntimeError(_cac.error_number_to_string(status))

        return self

    def play(self, data, wait=True):
        data = np.asarray(data*0.5, dtype="float32")
        data[data>1] = 1
        data[data<-1] = -1
        idx = 0
        while idx < len(data)-self._blocksize:
            self._queue.append(data[idx:idx+self._blocksize])
            idx += self._blocksize
        self._queue.append(data[idx:])
        while self._queue and wait:
            time.sleep(0.001)


class _Recorder(_Stream):
    def __enter__(self):
        self._set_blocksize()
        self._create_audiounit()
        self._set_enable_io(_cac.kAudioUnitScope_Input, 1)
        self._set_disable_io(_cac.kAudioUnitScope_Output, 0)
        self._set_device()
        self._set_samplerate(_cac.kAudioUnitScope_Output, 1)
        self._set_stream_format(_cac.kAudioUnitScope_Output, 1)

        self._queue = collections.deque()

        @_ffi.callback("AURenderCallback")
        def input_callback(userdata, actionflags, timestamp,
                           busnumber, numframes, bufferlist):
            bufferlist = _ffi.new("AudioBufferList*", [1, 1])
            bufferlist.mNumberBuffers = 1
            bufferlist.mBuffers[0].mNumberChannels = self.channels
            bufferlist.mBuffers[0].mDataByteSize = numframes * 4 * self.channels
            data = _ffi.new("Float32[]", numframes * self.channels)
            bufferlist.mBuffers[0].mData = data

            status = _au.AudioUnitRender(self._audiounit[0],
                                         actionflags,
                                         timestamp,
                                         busnumber,
                                         numframes,
                                         bufferlist)

            if status != 0:
                print(status)

            self._queue.append(data)
            return status

        self._set_callback(input_callback, _cac.kAudioOutputUnitProperty_SetInputCallback)

        status = _au.AudioUnitInitialize(self._audiounit[0])
        if status:
            raise RuntimeError(_cac.error_number_to_string(status))
        status = _au.AudioOutputUnitStart(self._audiounit[0])
        if status:
            raise RuntimeError(_cac.error_number_to_string(status))

        return self

    def record(self, numframes):
        while len(self._queue) < numframes/self._blocksize:
            time.sleep(0.001)

        data = np.concatenate([np.frombuffer(_ffi.buffer(d), dtype='float32') for d in self._queue])
        self._queue.clear()
        return data


# Here's how to do it: http://atastypixel.com/blog/using-remoteio-audio-unit/
# https://developer.apple.com/library/content/technotes/tn2091/_index.html
