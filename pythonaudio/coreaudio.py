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

    def player(self, samplerate, blocksize=None):
        return _Player(self._id, samplerate, 1)

    def play(self, data, samplerate, blocksize=None):
        with self.player(samplerate, blocksize) as p:
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

    def recorder(self, samplerate, blocksize=None):
        return _Recorder(self._id, samplerate, 1)

    def record(self, numframes, samplerate, blocksize=None):
        with self.recorder(samplerate, blocksize) as p:
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

def _CFString_to_str(str_data):
    str_length = _ca.CFStringGetLength(str_data[0])
    str_buffer = _ffi.new('char[]', str_length+1)

    err = _ca.CFStringGetCString(str_data[0], str_buffer, str_length+1, _cac.kCFStringEncodingUTF8)
    assert err == 1, "Could not decode string"

    return _ffi.string(str_buffer).decode()


class _Player:
    def __init__(self, id, samplerate, channels, blocksize=None, name='outputstream'):
        self._id = id
        self._samplerate = samplerate
        self._name = name
        self._blocksize = blocksize
        self.channels = channels

    def __enter__(self):
        desc = _ffi.new(
            "AudioComponentDescription*",
            dict(componentType=_cac.kAudioUnitType_Output,
                 componentSubType=_cac.kAudioUnitSubType_HALOutput,
                 componentFlags=0,
                 componentFlagsMask=0,
                 componentManufacturer=_cac.kAudioUnitManufacturer_Apple))

        audiocomponent = _au.AudioComponentFindNext(_ffi.NULL, desc)
        name = _ffi.new("CFStringRef*")
        status = _au.AudioComponentCopyName(audiocomponent, name)
        print("CopyName:", status, _CFString_to_str(name))

        self._audiounit = _ffi.new("AudioComponentInstance*")
        status = _au.AudioComponentInstanceNew(audiocomponent, self._audiounit)
        print("InstanceNew:", status)
        status = _au.AudioUnitInitialize(self._audiounit[0])
        print("Initialize:", status)

        data = _ffi.new("UInt32*", self._id)
        self._set_property(
            _cac.kAudioOutputUnitProperty_CurrentDevice,
            _cac.kAudioUnitScope_Input, 0,
            data)

        data = _ffi.new("UInt32*", 1)
        self._set_property(
            _cac.kAudioOutputUnitProperty_EnableIO,
            _cac.kAudioUnitScope_Input, 1,
            data)

        data = _ffi.new("Float64*", self._samplerate)
        self._set_property(
            _cac.kAudioUnitProperty_SampleRate,
            _cac.kAudioUnitScope_Input, 0,
            data)

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
            _cac.kAudioUnitScope_Input, 0,
            streamformat)

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

        self._callback = render_callback

        callbackstruct = _ffi.new(
            "AURenderCallbackStruct*",
            dict(inputProc=render_callback,
                 inputProcRefCon=_ffi.NULL))
        status = _au.AudioUnitSetProperty(
            self._audiounit[0],
            _cac.kAudioUnitProperty_SetRenderCallback,
            _cac.kAudioUnitScope_Global, 0,
            callbackstruct, _ffi.sizeof(callbackstruct[0]))
        print("SetRenderCallback:", status)

        status = _au.AudioOutputUnitStart(self._audiounit[0])
        print("Start:", status)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        status = _au.AudioOutputUnitStop(self._audiounit[0])
        print("Stop:", status)
        status = _au.AudioComponentInstanceDispose(self._audiounit[0])
        print("Dispose:", status)
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

    def play(self, data):
        data = np.asarray(data*0.5, dtype="float32")
        data[data>1] = 1
        data[data<-1] = -1
        idx = 0
        blocksize = 512
        while idx < len(data)-blocksize:
            self._queue.append(data[idx:idx+blocksize])
            idx += blocksize
        self._queue.append(data[idx:])
        while self._queue:
            time.sleep(0.01)



# status = _au.AudioUnitSetProperty(audiounit[0],
#                                   _cac.kAudioOutputUnitProperty_EnableIO,
#                                   _cac.kAudioUnitScope_Input, 1,
#                                   data, datasize[0]);
# print("EnableInputIO:", status)

# status = _au.AudioUnitGetProperty(audiounit[0],
#                                   _cac.kAudioUnitProperty_MaximumFramesPerSlice,
#                                   _cac.kAudioUnitScope_Global, 0,
#                                   data, datasize);
# print("GetProperty:", status, 'MaxFramesPerSlice:', data[0])

# status = _au.AudioUnitSetProperty(
#     audiounit[0], _cac.kAudioUnitProperty_StreamFormat,
#     _cac.kAudioUnitScope_Input, 0,
#     streamformat, _ffi.sizeof(streamformat[0]))
# print("SetInputStreamFormat:", status)

# Here's how to do it: http://atastypixel.com/blog/using-remoteio-audio-unit/

# timestamp = _ffi.new("AudioTimeStamp*")
# timestamp.mSampleTime = 0
# timestamp.mFlags = 0x1
# bufferlist = _ffi.new("AudioBufferList*")
# bufferlist.mNumberBuffers = 1
# bufferlist.mBuffers[0].mNumberChannels = 2
# bytesptr = _ffi.from_buffer(data)
# bufferlist.mBuffers[0].mDataByteSize = len(data)*4
# bufferlist.mBuffers[0].mData = bytesptr
# renderactionflags = _ffi.new("AudioUnitRenderActionFlags*")
# status = _au.AudioUnitRender(audiounit[0], renderactionflags,
#                              timestamp, _cac.outputbus,
#                              len(data),
#                              bufferlist)
# print("Render:", status, renderactionflags[0])
