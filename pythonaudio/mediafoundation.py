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

def CoCreateInstance(rclsid, pUnkOuter, riid, ppv):
    # see shared/WTypesbase.h and um/combaseapi.h:
    CLSCTX_ALL = 23
    hr = combase.CoCreateInstance(rclsid, pUnkOuter, CLSCTX_ALL, riid, ppv)
    check_errors(hr)

def DeviceEnumerator_EnumAudioEndpoints(self, dataFlow):
    DEVICE_STATE_ACTIVE = 0x1
    ppDevices = _ffi.new('IMMDeviceCollection **')
    hr = self[0][0].lpVtbl.EnumAudioEndpoints(self[0], dataFlow, DEVICE_STATE_ACTIVE, ppDevices);
    check_errors(hr)
    return ppDevices

def DeviceCollection_Item(self, nDevice):
    ppDevice = _ffi.new('IMMDevice **')
    hr = self[0][0].lpVtbl.Item(self[0], nDevice, ppDevice)
    check_errors(hr)
    return ppDevice

def DeviceCollection_GetCount(self):
    pcDevices = _ffi.new('UINT *')
    hr = self[0][0].lpVtbl.GetCount(self[0], pcDevices)
    check_errors(hr)
    return pcDevices[0]

def Device_GetId(self):
    ppId = _ffi.new('LPWSTR *')
    hr = self[0][0].lpVtbl.GetId(self[0], ppId)
    check_errors(hr)
    return _ffi.string(ppId[0])

def Device_GetName(self):
    # um/coml2api.h:
    ppPropertyStore = _ffi.new('IPropertyStore **')
    hr = self[0][0].lpVtbl.OpenPropertyStore(self[0], 0, ppPropertyStore)
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

def Device_GetChannels(self):
    # um/coml2api.h:
    ppPropertyStore = _ffi.new('IPropertyStore **')
    hr = self[0][0].lpVtbl.OpenPropertyStore(self[0], 0, ppPropertyStore)
    check_errors(hr)
    pPropVariant = combase.CoTaskMemAlloc(_ffi.sizeof('PROPVARIANT'))
    pPropVariant = _ffi.cast("PROPVARIANT *", pPropVariant)
    # um/functiondiscoverykeys_devpkey.h and https://msdn.microsoft.com/en-us/library/windows/desktop/dd370812(v=vs.85).aspx
    PKEY_AudioEngine_DeviceFormat = _ffi.new("PROPERTYKEY *",
                                             [[0xf19f064d, 0x82c, 0x4e27, [0xbc, 0x73, 0x68, 0x82, 0xa1, 0xbb, 0x8e, 0x4c]],
                                              0])
    hr = ppPropertyStore[0][0].lpVtbl.GetValue(ppPropertyStore[0], PKEY_AudioEngine_DeviceFormat, pPropVariant)
    check_errors(hr)
    if pPropVariant[0].vt != 65:
        raise RuntimeError('Property was expected to be a blob, but is not a blob')
    pPropVariantBlob = _ffi.cast("BLOB_PROPVARIANT *", pPropVariant)
    assert pPropVariantBlob[0].blob.cbSize == 40
    waveformat = _ffi.cast("WAVEFORMATEX *", pPropVariantBlob[0].blob.pBlobData)
    channels = waveformat[0].nChannels
    PropVariantClear(pPropVariant)
    Release(ppPropertyStore)
    return channels

def Device_Activate(self):
    CLSCTX_ALL = 23
    ppAudioClient = _ffi.new("IAudioClient **")
    IID_IAudioClient = guidof("{1CB9AD4C-DBFA-4C32-B178-C2F568A703B2}")
    hr = self[0][0].lpVtbl.Activate(self[0], IID_IAudioClient, CLSCTX_ALL, _ffi.NULL, _ffi.cast("void**", ppAudioClient))
    check_errors(hr)
    return ppAudioClient

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
    self[0][0].lpVtbl.Release(self[0])
    self[0] = _ffi.NULL

CoInitialize()

# Create the device enumerator.
ppEnum = _ffi.new('IMMDeviceEnumerator **')
IID_MMDeviceEnumerator = guidof("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
IID_IMMDeviceEnumerator = guidof("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
CoCreateInstance(IID_MMDeviceEnumerator, _ffi.NULL,
                 IID_IMMDeviceEnumerator, _ffi.cast("void **", ppEnum))

# Enumerate the rendering devices.
# https://msdn.microsoft.com/en-us/library/windows/desktop/dd370812(v=vs.85).aspx
ppDevices = DeviceEnumerator_EnumAudioEndpoints(ppEnum, mmdevapi.eAll)
# NOTE: use mmdevapi.aRender and mmdevapi.eCapture to search for playback/recording devices
Release(ppEnum)

# Get ID of the first device in the list.
ndevices = DeviceCollection_GetCount(ppDevices)
for devidx in range(ndevices):
    ppDevice = DeviceCollection_Item(ppDevices, devidx)
    devid = Device_GetId(ppDevice)
    devname = Device_GetName(ppDevice)
    channels = Device_GetChannels(ppDevice)
    print(f'device {devidx} has name {devname}, {channels} channels and id {devid}')
    Release(ppDevice)

import numpy as np
time = np.linspace(0, 1, 48000)
signal = np.sin(time*1000*2*np.pi)
stereo_signal = np.tile(signal, [2,1]).T.ravel()
stereo_noise = np.array(np.random.rand(48000*2)*2-1, 'float32')

ppDevice = DeviceCollection_Item(ppDevices, 0)
Release(ppDevices)

ppAudioClient = Device_Activate(ppDevice)
Release(ppDevice)

AudioClient_Initialize(ppAudioClient, 48000, 1024/48000)

buffersize = AudioClient_GetBufferSize(ppAudioClient)
print('buffersize', buffersize)
deviceperiod, minimumperiod = AudioClient_GetDevicePeriod(ppAudioClient)
print('deviceperiod', deviceperiod, 'minimum', minimumperiod)

ppRenderClient = AudioClient_GetService_Render(ppAudioClient)

buffer = RenderClient_GetBuffer(ppRenderClient, buffersize)
data = np.ascontiguousarray(stereo_noise[:buffersize*2])
idx = buffersize*2
cdata = _ffi.cast("BYTE*", data.__array_interface__['data'][0])
_ffi.memmove(buffer[0], cdata, buffersize*4*2)
RenderClient_ReleaseBuffer(ppRenderClient, buffersize)

AudioClient_Start(ppAudioClient)

while idx < len(stereo_noise):
    padding = AudioClient_GetCurrentPadding(ppAudioClient)
    towrite = buffersize-padding
    if towrite == 0:
        continue
    buffer = RenderClient_GetBuffer(ppRenderClient, towrite)
    data = np.ascontiguousarray(stereo_noise[idx:idx+towrite*2])
    idx += towrite*2
    cdata = _ffi.cast("BYTE*", data.__array_interface__['data'][0])
    _ffi.memmove(buffer[0], cdata, towrite*4*2)
    RenderClient_ReleaseBuffer(ppRenderClient, towrite)
    print(idx)

AudioClient_Stop(ppAudioClient)

Release(ppRenderClient)
Release(ppAudioClient)

print('done')

CoUninitialize()
# Now I know the device, read further here: https://msdn.microsoft.com/en-us/library/windows/desktop/dd371455(v=vs.85).aspx
# TODO: Release all the funny data structures I fetch
