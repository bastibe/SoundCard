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
    if hr == S_OK or S_FALSE:
        return bool(hr)
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
    else:
        raise RuntimeError('Error {}'.format(hex(hr+2**32)))

def CoInitializeEx():
    COINIT_MULTITHREADED = 0x0
    hr = combase.CoInitializeEx(_ffi.NULL, COINIT_MULTITHREADED)
    check_errors(hr)

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

def Device_OpenPropertyStore(self, flags='r'):
    # um/coml2api.h:
    STGM_READ = 0x00000000
    STGM_WRITE = 0x00000001
    STGM_READWRITE = 0x00000002

    if flags == 'r':
        bin_flags = STGM_READ
    elif flags == 'w':
        bin_flags = STGM_WRITE
    elif flags == 'rw':
        bin_flags = STGM_READWRITE
    else:
        raise TypeError(f'flags must be "r", "w", or "rw" (is {flags})')
    ppPropertyStore = _ffi.new('IPropertyStore **')
    hr = self[0][0].lpVtbl.OpenPropertyStore(self[0], bin_flags, ppPropertyStore)
    check_errors(hr)
    return ppPropertyStore

def PropertyStore_GetDeviceName(self):
    # um/functiondiscoverykeys_devpkey.h and https://msdn.microsoft.com/en-us/library/windows/desktop/dd370812(v=vs.85).aspx
    PKEY_Device_FriendlyName = _ffi.new("PROPERTYKEY *",
                                        [[0xa45c254e, 0xdf1c, 0x4efd, [0x80, 0x20, 0x67, 0xd1, 0x46, 0xa8, 0x50, 0xe0]],
                                         14])
    pPropVariant = _ffi.new('PROPVARIANT *')
    hr = self[0][0].lpVtbl.GetValue(self[0], PKEY_Device_FriendlyName, pPropVariant)
    check_errors(hr)
    if pPropVariant[0].vt != 31:
        raise RuntimeError('Property was expected to be a string, but is not a string')
    data = _ffi.cast("short*", pPropVariant[0].data)
    for idx in range(256):
        if data[idx] == 0:
            break
    return ''.join(chr(c) for c in data[0:idx])

def PropertyStore_GetChannels(self):
    PKEY_AudioEngine_DeviceFormat = _ffi.new("PROPERTYKEY *",
                                             [[0xf19f064d, 0x82c, 0x4e27, [0xbc, 0x73, 0x68, 0x82, 0xa1, 0xbb, 0x8e, 0x4c]],
                                              0])
    pPropVariant = _ffi.new('BLOB_PROPVARIANT *')
    pTmp = _ffi.cast("PROPVARIANT *", pPropVariant)
    hr = self[0][0].lpVtbl.GetValue(self[0], PKEY_AudioEngine_DeviceFormat, pTmp)
    check_errors(hr)
    if pPropVariant[0].vt != 65:
        raise RuntimeError('Property was expected to be a blob, but is not a blob')
    assert pPropVariant[0].blob.cbSize == 40
    waveformat = _ffi.cast("WAVEFORMATEX *", pPropVariant[0].blob.pBlobData)
    return waveformat[0].nChannels


CoInitializeEx()

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

# Get ID of the first device in the list.
ndevices = DeviceCollection_GetCount(ppDevices)
for devidx in range(ndevices):
    ppDevice = DeviceCollection_Item(ppDevices, devidx)
    devid = Device_GetId(ppDevice)
    ppPropertyStore = Device_OpenPropertyStore(ppDevice)
    devname = PropertyStore_GetDeviceName(ppPropertyStore)
    channels = PropertyStore_GetChannels(ppPropertyStore)
    print(f'device {devidx} has name {devname}, {channels} channels and id {devid}')


# Now I know the device, read further here: https://msdn.microsoft.com/en-us/library/windows/desktop/dd371455(v=vs.85).aspx
# TODO: Release all the funny data structures I fetch
