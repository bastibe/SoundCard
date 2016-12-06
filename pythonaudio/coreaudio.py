import os
import cffi

_ffi = cffi.FFI()
_package_dir, _ = os.path.split(__file__)
with open(os.path.join(_package_dir, 'coreaudio.py.h'), 'rt') as f:
    _ffi.cdef(f.read())

_ca = _ffi.dlopen('CoreAudio')

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
        name = _get_core_audio_property(self._id, _cac.kAudioObjectPropertyName, 'CFStringRef')
        return '<SoundCard {}>'.format(_CFString_to_str(name))


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
