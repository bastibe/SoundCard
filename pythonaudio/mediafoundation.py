"""Re-Implementation of https://msdn.microsoft.com/en-us/library/windows/desktop/aa369729%28v=vs.85%29.aspx using the CFFI"""

import os
import cffi
import numpy
import time

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
    E_NOINTERFACE = 0x80004002
    E_POINTER = 0x80004003
    E_OUTOFMEMORY = 0x8007000e
    E_INVALIDARG = 0x80070057
    if hr == S_OK:
        return
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

def PropVariantClear(pPropVariant):
    hr = ole32.PropVariantClear(pPropVariant)
    check_errors(hr)

def Release(ptrptr):
    if ptrptr[0] != _ffi.NULL:
        ptrptr[0][0].lpVtbl.Release(ptrptr[0])
        ptrptr[0] = _ffi.NULL

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

    def _audioClient(self):
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

    def player(self, samplerate, blocksize=None):
        return _Player(self._audioClient(), samplerate, blocksize)

    def play(self, data, samplerate):
        with self.player(samplerate) as p:
            p.play(data)

class _Microphone(_Device):
    def __init__(self, device):
        self._id = device._id

    def __repr__(self):
        return f'<Microphone {self.name} ({self.channels} channels)>'

    def recorder(self, samplerate, blocksize=None):
        return _Recorder(self._audioClient(), samplerate, blocksize)

    def record(self, samplerate, length):
        with self.recorder(samplerate) as r:
            return r.record(length)

class _AudioClient:
    def __init__(self, ptr, samplerate, blocksize):
        self._ptr = ptr
        if blocksize is None:
            blocksize = self.deviceperiod[0]*samplerate
        streamflags = 0x00100000 | 0x80000000 | 0x08000000 # rate-adjust | auto-convert-PCM | SRC-default-quality The
        ppMixFormat = _ffi.new('WAVEFORMATEX**')
        hr = self._ptr[0][0].lpVtbl.GetMixFormat(self._ptr[0], ppMixFormat) # fetch nChannels
        check_errors(hr)
        self.channels = ppMixFormat[0][0].nChannels
        ppMixFormat[0][0].wFormatTag = 0x0003 # IEEE float
        ppMixFormat[0][0].wBitsPerSample = 32
        ppMixFormat[0][0].nSamplesPerSec = int(samplerate)
        ppMixFormat[0][0].nBlockAlign = ppMixFormat[0][0].nChannels * ppMixFormat[0][0].wBitsPerSample // 8
        ppMixFormat[0][0].nAvgBytesPerSec = ppMixFormat[0][0].nSamplesPerSec * ppMixFormat[0][0].nBlockAlign
        ppMixFormat[0][0].cbSize = 0
        sharemode = 0 # shared (um/AudioSessionTypes:33)
        bufferduration = int(blocksize/samplerate * 1000_000_0) # in hecto-nanoseconds
        hr = self._ptr[0][0].lpVtbl.Initialize(self._ptr[0], sharemode, streamflags, bufferduration, 0, ppMixFormat[0], _ffi.NULL)
        check_errors(hr)
        combase.CoTaskMemFree(ppMixFormat[0])

    @property
    def buffersize(self):
        pBufferSize = _ffi.new("UINT32*")
        hr = self._ptr[0][0].lpVtbl.GetBufferSize(self._ptr[0], pBufferSize)
        check_errors(hr)
        return pBufferSize[0]

    @property
    def deviceperiod(self):
        pDefaultPeriod = _ffi.new("REFERENCE_TIME*")
        pMinimumPeriod = _ffi.new("REFERENCE_TIME*")
        hr = self._ptr[0][0].lpVtbl.GetDevicePeriod(self._ptr[0], pDefaultPeriod, pMinimumPeriod)
        check_errors(hr)
        return pDefaultPeriod[0]/1000_000_0, pMinimumPeriod[0]/1000_000_0

    @property
    def currentpadding(self):
        pPadding = _ffi.new("UINT32*")
        hr = self._ptr[0][0].lpVtbl.GetCurrentPadding(self._ptr[0], pPadding)
        check_errors(hr)
        return pPadding[0]

class _Player(_AudioClient):
    # https://msdn.microsoft.com/en-us/library/windows/desktop/dd316756(v=vs.85).aspx
    def _render_client(self):
        iid = guidof("{F294ACFC-3146-4483-A7BF-ADDCA7C260E2}")
        ppRenderClient = _ffi.new("IAudioRenderClient**")
        hr = self._ptr[0][0].lpVtbl.GetService(self._ptr[0], iid, _ffi.cast("void**", ppRenderClient))
        check_errors(hr)
        return ppRenderClient

    def _render_buffer(self, numframes):
        data = _ffi.new("BYTE**")
        hr = self._ppRenderClient[0][0].lpVtbl.GetBuffer(self._ppRenderClient[0], numframes, data)
        check_errors(hr)
        return data

    def _render_release(self, numframes):
        hr = self._ppRenderClient[0][0].lpVtbl.ReleaseBuffer(self._ppRenderClient[0], numframes, 0)
        check_errors(hr)

    def _render_available_frames(self):
        return self.buffersize-self.currentpadding

    def __enter__(self):
        self._ppRenderClient = self._render_client()
        hr = self._ptr[0][0].lpVtbl.Start(self._ptr[0])
        check_errors(hr)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        hr = self._ptr[0][0].lpVtbl.Stop(self._ptr[0])
        check_errors(hr)
        Release(self._ppRenderClient)

    def play(self, data):
        data = numpy.array(data, dtype='float32')
        if data.ndim == 1:
            data = data[:, None] # force 2d
        if data.ndim != 2:
            raise TypeError('data must be 1d or 2d, not {}d'.format(data.ndim))
        if data.shape[1] == 1 and self.channels != 1:
            data = numpy.tile(data, [1, self.channels])
        if data.shape[1] != self.channels:
            raise TypeError('second dimension of data must be equal to the number of channels, not {}'.format(data.shape[1]))

        while data.nbytes > 0:
            towrite = self._render_available_frames()
            if towrite == 0:
                time.sleep(0.001)
                continue
            bytes = data[:towrite].ravel().tostring()
            buffer = self._render_buffer(towrite)
            _ffi.memmove(buffer[0], bytes, len(bytes))
            self._render_release(towrite)
            data = data[towrite:]

class _Recorder(_AudioClient):
    # https://msdn.microsoft.com/en-us/library/windows/desktop/dd370800(v=vs.85).aspx
    def _capture_client(self):
        iid = guidof("{C8ADBD64-E71E-48a0-A4DE-185C395CD317}")
        ppCaptureClient = _ffi.new("IAudioCaptureClient**")
        hr = self._ptr[0][0].lpVtbl.GetService(self._ptr[0], iid, _ffi.cast("void**", ppCaptureClient))
        check_errors(hr)
        return ppCaptureClient

    def _capture_buffer(self):
        data = _ffi.new("BYTE**")
        toread = _ffi.new('UINT32*')
        flags = _ffi.new('DWORD*')
        hr = self._ppCaptureClient[0][0].lpVtbl.GetBuffer(self._ppCaptureClient[0], data, toread, flags, _ffi.NULL, _ffi.NULL)
        check_errors(hr)
        return data[0], toread[0], flags[0]

    def _capture_release(self, numframes):
        hr = self._ppCaptureClient[0][0].lpVtbl.ReleaseBuffer(self._ppCaptureClient[0], numframes)
        check_errors(hr)

    def _capture_available_frames(self):
        pSize = _ffi.new("UINT32*")
        hr = self._ppCaptureClient[0][0].lpVtbl.GetNextPacketSize(self._ppCaptureClient[0], pSize)
        check_errors(hr)
        return pSize[0]

    def __enter__(self):
        self._ppCaptureClient = self._capture_client()
        hr = self._ptr[0][0].lpVtbl.Start(self._ptr[0])
        check_errors(hr)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        hr = self._ptr[0][0].lpVtbl.Stop(self._ptr[0])
        check_errors(hr)
        Release(self._ppCaptureClient)

    def record(self, num_frames):
        captured_frames = 0
        captured_data = []
        while captured_frames < num_frames:
            toread = self._capture_available_frames()
            if toread > 0:
                data_ptr, nframes, flags = self._capture_buffer()
                if data_ptr != _ffi.NULL:
                    chunk = numpy.fromstring(_ffi.buffer(data_ptr, nframes*4*self.channels), dtype='float32')
                if nframes > 0:
                    self._capture_release(nframes)
                    captured_data.append(chunk)
                    captured_frames += nframes
            else:
                time.sleep(0.001)
        return numpy.reshape(numpy.concatenate(captured_data), [-1, self.channels])

CoInitialize()

import atexit
atexit.register(CoUninitialize)
