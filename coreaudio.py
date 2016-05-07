from cffi import FFI

ffi = FFI()
ffi.cdef("""
// CoreFoundation/CFBase.h:
typedef unsigned char           Boolean;
typedef unsigned int            UInt32;
typedef signed int              SInt32;
typedef SInt32                  OSStatus;
typedef signed long long CFIndex;
typedef const void * CFStringRef;

// CoreFoundation/CFString.h
typedef UInt32 CFStringEncoding;
CFIndex CFStringGetLength(CFStringRef theString);
Boolean CFStringGetCString(CFStringRef theString, char *buffer, CFIndex bufferSize, CFStringEncoding encoding);

// CoreAudio/AudioHardwareBase.h
typedef UInt32  AudioObjectID;
typedef UInt32  AudioObjectPropertySelector;
typedef UInt32  AudioObjectPropertyScope;
typedef UInt32  AudioObjectPropertyElement;
struct  AudioObjectPropertyAddress
{
    AudioObjectPropertySelector mSelector;
    AudioObjectPropertyScope    mScope;
    AudioObjectPropertyElement  mElement;
};
typedef struct AudioObjectPropertyAddress AudioObjectPropertyAddress;

// CoreAudio/AudioHardware.h
Boolean AudioObjectHasProperty(AudioObjectID inObjectID, const AudioObjectPropertyAddress* inAddress);
OSStatus AudioObjectGetPropertyDataSize(AudioObjectID inObjectID,
                                        const AudioObjectPropertyAddress* inAddress,
                                        UInt32 inQualifierDataSize,
                                        const void* inQualifierData,
                                        UInt32* outDataSize);
OSStatus AudioObjectGetPropertyData(AudioObjectID inObjectID,
                                    const AudioObjectPropertyAddress* inAddress,
                                    UInt32 inQualifierDataSize,
                                    const void* inQualifierData,
                                    UInt32* ioDataSize,
                                    void* outData);
""")

kAudioObjectSystemObject = 1
kAudioHardwarePropertyDevices = int.from_bytes(b'dev#', byteorder='big')
kAudioHardwarePropertyDefaultInputDevice = int.from_bytes(b'dIn ', byteorder='big')
kAudioHardwarePropertyDefaultOutputDevice = int.from_bytes(b'dOut', byteorder='big')

kAudioObjectPropertyScopeGlobal = int.from_bytes(b'glob', byteorder='big')
kAudioObjectPropertyScopeInput = int.from_bytes(b'inpt', byteorder='big')
kAudioObjectPropertyScopeOutput = int.from_bytes(b'outp', byteorder='big')
kAudioObjectPropertyScopePlayThrough = int.from_bytes(b'ptru', byteorder='big')

kAudioObjectPropertyName = int.from_bytes(b'lnam', byteorder='big')
kAudioObjectPropertyModelName = int.from_bytes(b'lmod', byteorder='big')
kAudioObjectPropertyManufacturer = int.from_bytes(b'lmak', byteorder='big')

kCFStringEncodingUTF8 = 0x08000100

ca = ffi.dlopen('CoreAudio')

def get_core_audio_property(target, selector, ctype):
    kAudioObjectPropertyElementMaster = 0
    prop = ffi.new("AudioObjectPropertyAddress*",
                   {'mSelector': selector,
                    'mScope': kAudioObjectPropertyScopeGlobal,
                    'mElement': kAudioObjectPropertyElementMaster})

    has_prop = ca.AudioObjectHasProperty(target, prop)
    assert has_prop == 1, 'Core Audio does not have the requested property'

    size = ffi.new("UInt32*")
    err = ca.AudioObjectGetPropertyDataSize(target, prop, 0, ffi.NULL, size)
    assert err == 0, "Can't get Core Audio property size"
    num_values = int(size[0]//ffi.sizeof(ctype))

    prop_data = ffi.new(ctype+'[]', num_values)
    err = ca.AudioObjectGetPropertyData(target, prop, 0, ffi.NULL,
                                        size, prop_data)
    assert err == 0, "Can't get Core Audio property data"

    return [prop_data[idx] for idx in range(num_values)]

def device_ids():
    device_ids = get_core_audio_property(kAudioObjectSystemObject,
                                         kAudioHardwarePropertyDevices,
                                         "AudioObjectID")
    default_input_id = get_core_audio_property(kAudioObjectSystemObject,
                                               kAudioHardwarePropertyDefaultInputDevice,
                                               "AudioObjectID")
    default_output_id = get_core_audio_property(kAudioObjectSystemObject,
                                                kAudioHardwarePropertyDefaultOutputDevice,
                                                "AudioObjectID")

    return dict(ids=device_ids,
                default_in=default_input_id[0],
                default_out=default_output_id[0])

def core_foundation_string_to_str(str_data):
    str_length = ca.CFStringGetLength(str_data[0])
    str_buffer = ffi.new('char[]', str_length+1)

    err = ca.CFStringGetCString(str_data[0], str_buffer, str_length+1, kCFStringEncodingUTF8)
    assert err == 1, "Could not decode string"

    return ffi.string(str_buffer).decode()

print('Device Names:')
ids = device_ids()
for dev in ids['ids']:
    name = get_core_audio_property(dev, kAudioObjectPropertyName, 'CFStringRef')
    if dev == ids['default_in']:
        defaultstring = ' (default input)'
    elif dev == ids['default_out']:
        defaultstring = ' (default output)'
    else:
        defaultstring = ''
    print('    {}: {}{}'.format(dev, core_foundation_string_to_str(name), defaultstring))
