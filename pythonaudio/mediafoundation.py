"""Re-Implementation of https://msdn.microsoft.com/en-us/library/windows/desktop/aa369729%28v=vs.85%29.aspx using the CFFI"""

import os
import cffi
import numpy as np

_ffi = cffi.FFI()
_package_dir, _ = os.path.split(__file__)
with open(os.path.join(_package_dir, 'mediafoundation.py.h'), 'rt') as f:
    _ffi.cdef(f.read())

mmdevapi = _ffi.dlopen('MMDevAPI')
combase = _ffi.dlopen('combase')
ole32 = _ffi.dlopen('ole32')

def all_speakers():
    """A list of all connected speakers."""
    with _DeviceEnumerator() as enum:
        return [_Speaker(dev) for dev in enum.all_devices('speaker')]

def default_speaker():
    """The default speaker of the system."""
    with _DeviceEnumerator() as enum:
        return _Speaker(enum.default_device('speaker'))

def get_speaker(id):
    """Get a specific speaker by a variety of means.

    id can be an a WASAPI id, a substring of the speaker name, or a
    fuzzy-matched pattern for the speaker name.

    """
    return _match_device(id, all_speakers())

def all_microphones():
    """A list of all connected microphones."""
    with _DeviceEnumerator() as enum:
        return [_Microphone(dev) for dev in enum.all_devices('microphone')]

def default_microphone():
    """The default microphone of the system."""
    with _DeviceEnumerator() as enum:
        return _Microphone(enum.default_device('microphone'))

def get_microphone(id):
    """Get a specific microphone by a variety of means.

    id can be a WASAPI id, a substring of the microphone name, or a
    fuzzy-matched pattern for the microphone name.

    """
    return _match_device(id, all_microphones())

def _match_device(id, devices):
    """Find id in a list of devices.

    id can be a WASAPI id, a substring of the device name, or a
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

def str2wstr(string):
    return _ffi.new('int16_t[]', [ord(s) for s in string]+[0])

def guidof(uuid_str):
    IID = _ffi.new('LPIID')
    # convert to zero terminated wide string
    uuid = str2wstr(uuid_str)
    hr = combase.IIDFromString(_ffi.cast("char*", uuid), IID)
    check_errors(hr)
    return IID

def check_errors(hr):
    # see shared/winerror.h:
    S_OK = 0
    S_FALSE = 1
    RPC_E_CHANGED_MODE = 0x80010106
    REGDB_E_CLASSNOTREG = 0x80040154
    CLASS_E_NOAGGREGATION = 0x80040110
    E_NOINTERFACE = 0x80004002
    E_POINTER = 0x80004003
    E_OUTOFMEMORY = 0x8007000e
    E_INVALIDARG = 0x80070057
    AUDCLNT_E_DEVICE_INVALIDATED = 1<<31 | 2185<<16 | 0x004
    AUDCLNT_E_SERVICE_NOT_RUNNING = 1<<31 | 2185<<16 | 0x010
    AUDCLNT_E_UNSUPPORTED_FORMAT = 1<<31 | 2185<<16 | 0x008
    if hr == S_OK:
        return
    elif hr+2**32 == RPC_E_CHANGED_MODE:
        raise RuntimeError('A previous call to CoInitializeEx specified '
                           'the concurrency model for this thread as '
                           'multithread apartment (MTA). This could also '
                           'indicate that a change from neutral-threaded '
                           'apartment to single-threaded apartment '
                           'has occurred.')
    elif hr+2**23 == REGDB_E_CLASSNOTREG:
        raise RuntimeError('A specified class is not registered in the '
                           'registration database. Also can indicate '
                           'that the type of' 'server you requested in '
                           'the CLSCTX enumeration is not registered or '
                           'the values for the server types in the '
                           'registry are corrupt.')
    elif hr+2**32 == CLASS_E_NOAGGREGATION:
        raise RuntimeError('This class cannot be created as part of an '
                           'aggregate.')
    elif hr+2**32 == E_NOINTERFACE:
        raise RuntimeError('The specified class does not implement the '
                           'requested interface, or the controlling '
                           'IUnknown does not expose the requested '
                           'interface.')
    elif hr+2**32 == E_POINTER:
        raise RuntimeError('An argument is NULL.')
    elif hr+2**32 == E_INVALIDARG:
        raise RuntimeError("invalid argument")
    elif hr+2**32 == E_OUTOFMEMORY:
        raise RuntimeError("out of memory")
    elif hr+2**32 == AUDCLNT_E_DEVICE_INVALIDATED:
        RuntimeError('The user has removed either the audio endpoint '
                     'device or the adapter device that the endpoint '
                     'device connects to.')
    elif hr+2**32 == AUDCLNT_E_SERVICE_NOT_RUNNING:
        RuntimeError('The Windows audio service is not running.')
    else:
        raise RuntimeError('Error {}'.format(hex(hr+2**32)))

def CoInitialize():
    COINIT_MULTITHREADED = 0x0
    hr = combase.CoInitializeEx(_ffi.NULL, COINIT_MULTITHREADED)
    check_errors(hr)

def CoUninitialize():
    combase.CoUninitialize()

class _DeviceEnumerator:
    def __init__(self):
        self._ptr = _ffi.new('IMMDeviceEnumerator **')
        IID_MMDeviceEnumerator = guidof("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
        IID_IMMDeviceEnumerator = guidof("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
        # see shared/WTypesbase.h and um/combaseapi.h:
        CLSCTX_ALL = 23
        hr = combase.CoCreateInstance(IID_MMDeviceEnumerator, _ffi.NULL, CLSCTX_ALL,
                                  IID_IMMDeviceEnumerator, _ffi.cast("void **", self._ptr))
        check_errors(hr)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        Release(self._ptr)

    def __del__(self):
        Release(self._ptr)

    def _device_id(self, device_ptr):
        ppId = _ffi.new('LPWSTR *')
        hr = device_ptr[0][0].lpVtbl.GetId(device_ptr[0], ppId)
        check_errors(hr)
        return _ffi.string(ppId[0])

    def all_devices(self, kind):
        if kind == 'speaker':
            data_flow = mmdevapi.eRender
        elif kind == 'microphone':
            data_flow = mmdevapi.eCapture
        else:
            raise TypeError(f'Invalid kind: {kind}')

        DEVICE_STATE_ACTIVE = 0x1
        ppDevices = _ffi.new('IMMDeviceCollection **')
        hr = self._ptr[0][0].lpVtbl.EnumAudioEndpoints(self._ptr[0], data_flow, DEVICE_STATE_ACTIVE, ppDevices);
        check_errors(hr)

        for ppDevice in _DeviceCollection(ppDevices):
            device = _Device(self._device_id(ppDevice))
            Release(ppDevice)
            yield device

    def default_device(self, kind):
        if kind == 'speaker':
            data_flow = mmdevapi.eRender
        elif kind == 'microphone':
            data_flow = mmdevapi.eCapture
        else:
            raise TypeError(f'Invalid kind: {kind}')

        ppDevice = _ffi.new('IMMDevice **')
        eConsole = 0
        hr = self._ptr[0][0].lpVtbl.GetDefaultAudioEndpoint(self._ptr[0], data_flow, eConsole, ppDevice);
        check_errors(hr)
        device = _Device(self._device_id(ppDevice))
        Release(ppDevice)
        return device

    def device_ptr(self, devid):
        ppDevice = _ffi.new('IMMDevice **')
        devid = str2wstr(devid)
        hr = self._ptr[0][0].lpVtbl.GetDevice(self._ptr[0], _ffi.cast('wchar_t *', devid), ppDevice);
        check_errors(hr)
        return ppDevice

class _DeviceCollection:
    def __init__(self, ptr):
        self._ptr = ptr

    def __del__(self):
        Release(self._ptr)

    def __len__(self):
        pCount = _ffi.new('UINT *')
        hr = self._ptr[0][0].lpVtbl.GetCount(self._ptr[0], pCount)
        check_errors(hr)
        return pCount[0]

    def __getitem__(self, idx):
        if idx >= len(self):
            raise StopIteration()
        ppDevice = _ffi.new('IMMDevice **')
        hr = self._ptr[0][0].lpVtbl.Item(self._ptr[0], idx, ppDevice)
        check_errors(hr)
        return ppDevice

class _Device:
    def __init__(self, id):
        self._id = id

    def _device_ptr(self):
        with _DeviceEnumerator() as enum:
            return enum.device_ptr(self._id)

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        # um/coml2api.h:
        ppPropertyStore = _ffi.new('IPropertyStore **')
        ptr = self._device_ptr()
        hr = ptr[0][0].lpVtbl.OpenPropertyStore(ptr[0], 0, ppPropertyStore)
        Release(ptr)
        check_errors(hr)
        pPropVariant = combase.CoTaskMemAlloc(_ffi.sizeof('PROPVARIANT'))
        pPropVariant = _ffi.cast("PROPVARIANT *", pPropVariant)
        # um/functiondiscoverykeys_devpkey.h and https://msdn.microsoft.com/en-us/library/windows/desktop/dd370812(v=vs.85).aspx
        PKEY_Device_FriendlyName = _ffi.new("PROPERTYKEY *",
                                            [[0xa45c254e, 0xdf1c, 0x4efd, [0x80, 0x20, 0x67, 0xd1, 0x46, 0xa8, 0x50, 0xe0]],
                                            14])
        hr = ppPropertyStore[0][0].lpVtbl.GetValue(ppPropertyStore[0], PKEY_Device_FriendlyName, pPropVariant)
        check_errors(hr)
        if pPropVariant[0].vt != 31:
            raise RuntimeError('Property was expected to be a string, but is not a string')
        data = _ffi.cast("short*", pPropVariant[0].data)
        for idx in range(256):
            if data[idx] == 0:
                break
        devicename = ''.join(chr(c) for c in data[0:idx])
        PropVariantClear(pPropVariant)
        Release(ppPropertyStore)
        return devicename

    @property
    def channels(self):
        # um/coml2api.h:
        ppPropertyStore = _ffi.new('IPropertyStore **')
        ptr = self._device_ptr()
        hr = ptr[0][0].lpVtbl.OpenPropertyStore(ptr[0], 0, ppPropertyStore)
        Release(ptr)
        check_errors(hr)
        pPropVariant = combase.CoTaskMemAlloc(_ffi.sizeof('PROPVARIANT'))
        pPropVariant = _ffi.cast("PROPVARIANT *", pPropVariant)
        # um/functiondiscoverykeys_devpkey.h and https://msdn.microsoft.com/en-us/library/windows/desktop/dd370812(v=vs.85).aspx
        PKEY_AudioEngine_DeviceFormat = _ffi.new("PROPERTYKEY *",
                                                 [[0xf19f064d, 0x82c, 0x4e27, [0xbc, 0x73, 0x68, 0x82, 0xa1, 0xbb, 0x8e, 0x4c]],
                                                  0])
        hr = ppPropertyStore[0][0].lpVtbl.GetValue(ppPropertyStore[0], PKEY_AudioEngine_DeviceFormat, pPropVariant)
        Release(ppPropertyStore)
        check_errors(hr)
        if pPropVariant[0].vt != 65:
            raise RuntimeError('Property was expected to be a blob, but is not a blob')
        pPropVariantBlob = _ffi.cast("BLOB_PROPVARIANT *", pPropVariant)
        assert pPropVariantBlob[0].blob.cbSize == 40
        waveformat = _ffi.cast("WAVEFORMATEX *", pPropVariantBlob[0].blob.pBlobData)
        channels = waveformat[0].nChannels
        PropVariantClear(pPropVariant)
        return channels

    def activate(self):
        CLSCTX_ALL = 23
        ppAudioClient = _ffi.new("IAudioClient **")
        IID_IAudioClient = guidof("{1CB9AD4C-DBFA-4C32-B178-C2F568A703B2}")
        ptr = self._device_ptr()
        hr = ptr[0][0].lpVtbl.Activate(ptr[0], IID_IAudioClient, CLSCTX_ALL, _ffi.NULL, _ffi.cast("void**", ppAudioClient))
        Release(ptr)
        check_errors(hr)
        return ppAudioClient

class _Speaker(_Device):
    def __init__(self, device):
        self._id = device._id

    def __repr__(self):
        return f'<Speaker {self.name} ({self.channels} channels)>'

class _Microphone(_Device):
    def __init__(self, device):
        self._id = device._id

    def __repr__(self):
        return f'<Microphone {self.name} ({self.channels} channels)>'

def AudioClient_Initialize(self, samplerate, bufferlength):
    streamflags = 0x00100000 | 0x80000000 | 0x08000000 # rate-adjust | auto-convert-PCM | SRC-default-quality The
    ppMixFormat = _ffi.new('WAVEFORMATEX**')
    hr = self[0][0].lpVtbl.GetMixFormat(self[0], ppMixFormat) # fetch nChannels
    check_errors(hr)
    channels = ppMixFormat[0][0].nChannels
    ppMixFormat[0][0].wFormatTag = 0x0003 # IEEE float
    ppMixFormat[0][0].wBitsPerSample = 32
    ppMixFormat[0][0].nSamplesPerSec = int(samplerate)
    ppMixFormat[0][0].nBlockAlign = ppMixFormat[0][0].nChannels * ppMixFormat[0][0].wBitsPerSample // 8
    ppMixFormat[0][0].nAvgBytesPerSec = ppMixFormat[0][0].nSamplesPerSec * ppMixFormat[0][0].nBlockAlign
    ppMixFormat[0][0].cbSize = 0
    sharemode = 0 # shared (um/AudioSessionTypes:33)
    bufferduration = int(bufferlength * 1000_000_0) # in hecto-nanoseconds
    hr = self[0][0].lpVtbl.Initialize(self[0], sharemode, streamflags, bufferduration, 0, ppMixFormat[0], _ffi.NULL)
    check_errors(hr)
    combase.CoTaskMemFree(ppMixFormat[0])

def AudioClient_GetService_Render(self):
    iid = guidof("{F294ACFC-3146-4483-A7BF-ADDCA7C260E2}")
    ppRenderClient = _ffi.new("IAudioRenderClient**")
    hr = self[0][0].lpVtbl.GetService(self[0], iid, _ffi.cast("void**", ppRenderClient))
    check_errors(hr)
    return ppRenderClient

def AudioClient_GetService_Capture(self):
    iid = guidof("{C8ADBD64-E71E-48a0-A4DE-185C395CD317}")
    ppCaptureClient = _ffi.new("IAudioCaptureClient**")
    hr = self[0][0].lpVtbl.GetService(self[0], iid, _ffi.cast("void**", ppCaptureClient))
    check_errors(hr)
    return ppCaptureClient

def AudioClient_GetBufferSize(self):
    pBufferSize = _ffi.new("UINT32*")
    hr = self[0][0].lpVtbl.GetBufferSize(self[0], pBufferSize)
    check_errors(hr)
    return pBufferSize[0]

def AudioClient_GetDevicePeriod(self):
    pDefaultPeriod = _ffi.new("REFERENCE_TIME*")
    pMinimumPeriod = _ffi.new("REFERENCE_TIME*")
    hr = self[0][0].lpVtbl.GetDevicePeriod(self[0], pDefaultPeriod, pMinimumPeriod)
    check_errors(hr)
    return pDefaultPeriod[0], pMinimumPeriod[0]

def AudioClient_GetCurrentPadding(self):
    pPadding = _ffi.new("UINT32*")
    hr = self[0][0].lpVtbl.GetCurrentPadding(self[0], pPadding)
    check_errors(hr)
    return pPadding[0]

def AudioClient_Start(self):
    hr = self[0][0].lpVtbl.Start(self[0])
    check_errors(hr)

def AudioClient_Stop(self):
    hr = self[0][0].lpVtbl.Stop(self[0])
    check_errors(hr)

def RenderClient_GetBuffer(self, numframes):
    data = _ffi.new("BYTE**")
    hr = self[0][0].lpVtbl.GetBuffer(self[0], numframes, data)
    check_errors(hr)
    return data

def RenderClient_ReleaseBuffer(self, numframes):
    hr = self[0][0].lpVtbl.ReleaseBuffer(self[0], numframes, 0)
    check_errors(hr)

def PropVariantClear(pPropVariant):
    hr = ole32.PropVariantClear(pPropVariant)
    check_errors(hr)

def Release(self):
    if self[0] != _ffi.NULL:
        self[0][0].lpVtbl.Release(self[0])
        self[0] = _ffi.NULL

CoInitialize()
import atexit
atexit.register(CoUninitialize)

print('all speakers:', all_speakers())
print('all microphones:', all_microphones())
print('default speaker:', default_speaker())
print('default microphone:', default_microphone())
print('a speaker:', get_speaker('Lautsprecher'))
print('a microphone:', get_microphone('Mikrofon'))

import numpy as np
time = np.linspace(0, 1, 48000)
signal = np.sin(time*1000*2*np.pi)
stereo_signal = np.tile(signal, [2,1]).T.ravel()
stereo_signal = np.array(stereo_signal, 'float32')
# stereo_signal = np.array(np.random.rand(48000*2)*2-1, 'float32')

# ppDevice = DeviceCollection_Item(ppDevices, 0)
# Release(ppDevices)

# ppAudioClient = Device_Activate(ppDevice)
# Release(ppDevice)

# AudioClient_Initialize(ppAudioClient, 48000, 1024/48000)

# buffersize = AudioClient_GetBufferSize(ppAudioClient)
# print('buffersize', buffersize)
# deviceperiod, minimumperiod = AudioClient_GetDevicePeriod(ppAudioClient)
# print('deviceperiod', deviceperiod, 'minimum', minimumperiod)

# ppRenderClient = AudioClient_GetService_Render(ppAudioClient)

# buffer = RenderClient_GetBuffer(ppRenderClient, buffersize)
# data = np.ascontiguousarray(stereo_signal[:buffersize*2])
# idx = buffersize*2
# cdata = _ffi.cast("BYTE*", data.__array_interface__['data'][0])
# _ffi.memmove(buffer[0], cdata, buffersize*4*2)
# RenderClient_ReleaseBuffer(ppRenderClient, buffersize)

# AudioClient_Start(ppAudioClient)

# while idx < len(stereo_signal):
#     padding = AudioClient_GetCurrentPadding(ppAudioClient)
#     towrite = buffersize-padding
#     if towrite == 0:
#         continue
#     buffer = RenderClient_GetBuffer(ppRenderClient, towrite)
#     data = np.ascontiguousarray(stereo_signal[idx:idx+towrite*2])
#     idx += towrite*2
#     cdata = _ffi.cast("BYTE*", data.__array_interface__['data'][0])
#     _ffi.memmove(buffer[0], cdata, towrite*4*2)
#     RenderClient_ReleaseBuffer(ppRenderClient, towrite)
#     print(f"\r{towrite}, {idx/len(stereo_signal):4.2f}", end="")

# AudioClient_Stop(ppAudioClient)

# Release(ppRenderClient)
# Release(ppAudioClient)

# print('\ndone')

# Now I know the device, read further here: https://msdn.microsoft.com/en-us/library/windows/desktop/dd371455(v=vs.85).aspx
# TODO: Release all the funny data structures I fetch
