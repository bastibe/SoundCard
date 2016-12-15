import os
import cffi

_ffi = cffi.FFI()
_package_dir, _ = os.path.split(__file__)
with open(os.path.join(_package_dir, 'coreaudio.py.h'), 'rt') as f:
    _ffi.cdef(f.read())

_ca = _ffi.dlopen('CoreAudio')
_au = _ffi.dlopen('AudioUnit')

import coreaudioconstants as _cac

def all_soundcards():
    """A list of all known speakers."""
    device_ids = _get_core_audio_property(_cac.kAudioObjectSystemObject,
                                          _cac.kAudioHardwarePropertyDevices,
                                          "AudioObjectID")
    return [_Soundcard(id=d) for d in device_ids]

def default_speaker():
    device_id, = _get_core_audio_property(_cac.kAudioObjectSystemObject,
                                          _cac.kAudioHardwarePropertyDefaultOutputDevice,
                                          "AudioObjectID")
    return _Soundcard(id=device_id)

def default_microphone():
    device_id, = _get_core_audio_property(_cac.kAudioObjectSystemObject,
                                          _cac.kAudioHardwarePropertyDefaultInputDevice,
                                          "AudioObjectID")
    return _Soundcard(id=device_id)

class _Soundcard:
    def __init__(self, *, id):
        self._id = id

    def __repr__(self):
        name = _get_core_audio_property(self._id, _cac.kAudioObjectPropertyName,
                                        'CFStringRef')
        return '<SoundCard {} ({})>'.format(_CFString_to_str(name), self._id)


def _get_core_audio_property(target, selector, ctype):
    prop = _ffi.new("AudioObjectPropertyAddress*",
                   {'mSelector': selector,
                    'mScope': _cac.kAudioObjectPropertyScopeGlobal,
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

print('All Soundcards:')
print(all_soundcards())
print('Default Speaker:')
print(default_speaker())
print('Default Microphone:')
print(default_microphone())


desc = _ffi.new("AudioComponentDescription*")
desc.componentType = _cac.kAudioUnitType_Output
desc.componentSubType = _cac.kAudioUnitSubType_HALOutput
desc.componentFlags = 0
desc.componentFlagsMask = 0
desc.componentManufacturer = _cac.kAudioUnitManufacturer_Apple

audiocomponent = _au.AudioComponentFindNext(_ffi.NULL, desc)
name = _ffi.new("CFStringRef*")
status = _au.AudioComponentCopyName(audiocomponent, name)
print("CopyName:", status, _CFString_to_str(name))

audiounit = _ffi.new("AudioComponentInstance*")
status = _au.AudioComponentInstanceNew(audiocomponent, audiounit)
print("InstanceNew:", status)
status = _au.AudioUnitInitialize(audiounit[0])
print("Initialize:", status)
datasize = _ffi.new("UInt32*")
writeable = _ffi.new("Boolean*")
status = _au.AudioUnitGetPropertyInfo(audiounit[0],
                                      _cac.kAudioOutputUnitProperty_CurrentDevice,
                                      _cac.kAudioUnitScope_Output, 0,
                                      datasize, writeable);
print("GetPropertyInfo:", status)
data = _ffi.new("UInt32*")
status = _au.AudioUnitGetProperty(audiounit[0],
                                  _cac.kAudioOutputUnitProperty_CurrentDevice,
                                  _cac.kAudioUnitScope_Output, 0,
                                  data, datasize);
print("GetProperty:", status, 'currentdevice:', data[0])

data[0] = 1
status = _au.AudioUnitSetProperty(audiounit[0],
                                  _cac.kAudioOutputUnitProperty_EnableIO,
                                  _cac.kAudioUnitScope_Output, 0,
                                  data, datasize[0]);
print("EnableOutputIO:", status)
status = _au.AudioUnitSetProperty(audiounit[0],
                                  _cac.kAudioOutputUnitProperty_EnableIO,
                                  _cac.kAudioUnitScope_Input, 1,
                                  data, datasize[0]);
print("EnableInputIO:", status)

status = _au.AudioUnitGetProperty(audiounit[0],
                                  _cac.kAudioUnitProperty_MaximumFramesPerSlice,
                                  _cac.kAudioUnitScope_Global, 0,
                                  data, datasize);
print("GetProperty:", status, 'MaxFramesPerSlice:', data[0])

channels = 1

streamformat = _ffi.new("AudioStreamBasicDescription*")
streamformat.mSampleRate = 44100
streamformat.mFormatID = _cac.kAudioFormatLinearPCM
streamformat.mFormatFlags = _cac.kAudioFormatFlagIsFloat
streamformat.mFramesPerPacket = 1 # uncompressed audio
streamformat.mChannelsPerFrame = channels
streamformat.mBitsPerChannel = 32
streamformat.mBytesPerPacket = channels * 4
streamformat.mBytesPerFrame = channels * 4

status = _au.AudioUnitSetProperty(audiounit[0], _cac.kAudioUnitProperty_StreamFormat,
                                  _cac.kAudioUnitScope_Output, 1,
                                  streamformat, _ffi.sizeof(streamformat[0]))
print("SetOutputStreamFormat:", status)
status = _au.AudioUnitSetProperty(audiounit[0], _cac.kAudioUnitProperty_StreamFormat,
                                  _cac.kAudioUnitScope_Input, 0,
                                  streamformat, _ffi.sizeof(streamformat[0]))
print("SetInputStreamFormat:", status)

status = _au.AudioUnitGetProperty(audiounit[0], _cac.kAudioUnitProperty_StreamFormat,
                                  _cac.kAudioUnitScope_Output, 0,
                                  streamformat, datasize)
print("GetProperty:", status, "streamformat:", streamformat.mBytesPerFrame)

import numpy as np
data = np.random.randn(512,channels)
data[data > 1] = 1
data[data < -1] = -1
data = np.asarray(data, dtype="float32")

@_ffi.callback("AURenderCallback")
def render_callback(userdata, actionflags, timestamp, busnumber, numframes, bufferlist):
    for bufferidx in range(bufferlist.mNumberBuffers):
        buffer = bufferlist.mBuffers[bufferidx]
        buffersize = buffer.mDataByteSize
        bbuffer = _ffi.buffer(buffer.mData, buffer.mDataByteSize)
        noise = np.random.randn(numframes)
        noisedata = _ffi.from_buffer(noise)
        _ffi.memmove(bbuffer, noisedata, buffersize)
    return 0

callbackstruct = _ffi.new("AURenderCallbackStruct*")
callbackstruct.inputProc = render_callback
callbackstruct.inputProcRefCon = _ffi.NULL
status = _au.AudioUnitSetProperty(audiounit[0],
                                  _cac.kAudioUnitProperty_SetRenderCallback,
                                  _cac.kAudioUnitScope_Global, 0,
                                  callbackstruct, _ffi.sizeof(callbackstruct[0]))
print("SetRenderCallback:", status)

status = _au.AudioOutputUnitStart(audiounit[0])
print("Start:", status)

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

import time
time.sleep(5)

status = _au.AudioOutputUnitStop(audiounit[0])
print("Stop:", status)

status = _au.AudioComponentInstanceDispose(audiounit[0])
print("Dispose:", status)
