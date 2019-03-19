"""Re-Implementation of https://msdn.microsoft.com/en-us/library/windows/desktop/aa369729%28v=vs.85%29.aspx using the CFFI"""

import os
import cffi
import numpy
import time
import re
import collections

_ffi = cffi.FFI()
_package_dir, _ = os.path.split(__file__)
with open(os.path.join(_package_dir, 'mediafoundation.py.h'), 'rt') as f:
    _ffi.cdef(f.read())

_combase = _ffi.dlopen('combase')
_ole32 = _ffi.dlopen('ole32')

class _COMLibrary:
    """General functionality of the COM library.

    This class contains functionality related to the COM library, for:
    - initializing and uninitializing the library.
    - checking HRESULT codes.
    - decrementing the reference count of COM objects.

    """

    def __init__(self):
        COINIT_MULTITHREADED = 0x0
        hr = _combase.CoInitializeEx(_ffi.NULL, COINIT_MULTITHREADED)

        try:
            self.check_error(hr)

            # Flag to keep track if this class directly initialized
            # COM, required for un-initializing in destructor:
            self.com_loaded = True

        except RuntimeError as e:
            # Error 0x80010106
            RPC_E_CHANGED_MODE = 0x80010106
            if hr + 2 ** 32 == RPC_E_CHANGED_MODE:
                # COM was already initialized before (e.g. by the
                # debugger), therefore trying to initialize it again
                # fails we can safely ignore this error, but we have
                # to make sure that we don't try to unload it
                # afterwards therefore we set this flag to False:
                self.com_loaded = False
            else:
                raise e

    def __del__(self):
        # Don't un-initialize COM if COM was not initialized directly
        # by this class:
        if self.com_loaded:
            _combase.CoUninitialize()

    @staticmethod
    def check_error(hresult):
        """Check a given HRESULT for errors.

        Throws an error for non-S_OK HRESULTs.

        """
        # see shared/winerror.h:
        S_OK = 0
        E_NOINTERFACE = 0x80004002
        E_POINTER = 0x80004003
        E_OUTOFMEMORY = 0x8007000e
        E_INVALIDARG = 0x80070057
        AUDCLNT_E_UNSUPPORTED_FORMAT = 0x88890008
        if hresult == S_OK:
            return
        elif hresult+2**32 == E_NOINTERFACE:
            raise RuntimeError('The specified class does not implement the '
                               'requested interface, or the controlling '
                               'IUnknown does not expose the requested '
                               'interface.')
        elif hresult+2**32 == E_POINTER:
            raise RuntimeError('An argument is NULL.')
        elif hresult+2**32 == E_INVALIDARG:
            raise RuntimeError("invalid argument")
        elif hresult+2**32 == E_OUTOFMEMORY:
            raise RuntimeError("out of memory")
        elif hresult+2**32 == AUDCLNT_E_UNSUPPORTED_FORMAT:
            raise RuntimeError("unsupported format")
        else:
            raise RuntimeError('Error {}'.format(hex(hresult+2**32)))

    @staticmethod
    def release(ppObject):
        """Decrement reference count on COM object."""
        if ppObject[0] != _ffi.NULL:
            ppObject[0][0].lpVtbl.Release(ppObject[0])
            ppObject[0] = _ffi.NULL

_com = _COMLibrary()

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

def all_microphones(include_loopback=False):
    """A list of all connected microphones.

    By default, this does not include loopback (virtual microphones
    that record the output of a speaker).

    """

    with _DeviceEnumerator() as enum:
        if include_loopback:
            return [_Microphone(dev, isloopback=True) for dev in enum.all_devices('speaker')] + [_Microphone(dev) for dev in enum.all_devices('microphone')]
        else:
            return [_Microphone(dev) for dev in enum.all_devices('microphone')]

def default_microphone():
    """The default microphone of the system."""
    with _DeviceEnumerator() as enum:
        return _Microphone(enum.default_device('microphone'))

def get_microphone(id, include_loopback=False):
    """Get a specific microphone by a variety of means.

    id can be a WASAPI id, a substring of the microphone name, or a
    fuzzy-matched pattern for the microphone name.

    """
    return _match_device(id, all_microphones(include_loopback))

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

def _str2wstr(string):
    """Converts a Python str to a Windows WSTR_T."""
    return _ffi.new('int16_t[]', [ord(s) for s in string]+[0])

def _guidof(uuid_str):
    """Creates a Windows LPIID from a str."""
    IID = _ffi.new('LPIID')
    # convert to zero terminated wide string
    uuid = _str2wstr(uuid_str)
    hr = _combase.IIDFromString(_ffi.cast("char*", uuid), IID)
    _com.check_error(hr)
    return IID

class _DeviceEnumerator:
    """Wrapper class for an IMMDeviceEnumerator**.

    Provides methods for retrieving _Devices and pointers to the
    underlying IMMDevices.

    """

    def __init__(self):
        self._ptr = _ffi.new('IMMDeviceEnumerator **')
        IID_MMDeviceEnumerator = _guidof("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
        IID_IMMDeviceEnumerator = _guidof("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
        # see shared/WTypesbase.h and um/combaseapi.h:
        CLSCTX_ALL = 23
        hr = _combase.CoCreateInstance(IID_MMDeviceEnumerator, _ffi.NULL, CLSCTX_ALL,
                                  IID_IMMDeviceEnumerator, _ffi.cast("void **", self._ptr))
        _com.check_error(hr)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        _com.release(self._ptr)

    def __del__(self):
        _com.release(self._ptr)

    def _device_id(self, device_ptr):
        """Returns the WASAPI device ID for an IMMDevice**."""
        ppId = _ffi.new('LPWSTR *')
        hr = device_ptr[0][0].lpVtbl.GetId(device_ptr[0], ppId)
        _com.check_error(hr)
        return _ffi.string(ppId[0])

    def all_devices(self, kind):
        """Yields all sound cards of a given kind.

        Kind may be 'speaker' or 'microphone'.
        Sound cards are returned as _Device objects.

        """
        if kind == 'speaker':
            data_flow = 0 # render
        elif kind == 'microphone':
            data_flow = 1 # capture
        else:
            raise TypeError('Invalid kind: {}'.format(kind))

        DEVICE_STATE_ACTIVE = 0x1
        ppDevices = _ffi.new('IMMDeviceCollection **')
        hr = self._ptr[0][0].lpVtbl.EnumAudioEndpoints(self._ptr[0], data_flow, DEVICE_STATE_ACTIVE, ppDevices);
        _com.check_error(hr)

        for ppDevice in _DeviceCollection(ppDevices):
            device = _Device(self._device_id(ppDevice))
            _com.release(ppDevice)
            yield device

    def default_device(self, kind):
        """Returns the default sound card of a given kind.

        Kind may be 'speaker' or 'microphone'.
        Default sound card is returned as a _Device object.

        """
        if kind == 'speaker':
            data_flow = 0 # render
        elif kind == 'microphone':
            data_flow = 1 # capture
        else:
            raise TypeError('Invalid kind: {}'.format(kind))

        ppDevice = _ffi.new('IMMDevice **')
        eConsole = 0
        hr = self._ptr[0][0].lpVtbl.GetDefaultAudioEndpoint(self._ptr[0], data_flow, eConsole, ppDevice);
        _com.check_error(hr)
        device = _Device(self._device_id(ppDevice))
        _com.release(ppDevice)
        return device

    def device_ptr(self, devid):
        """Retrieve IMMDevice** for a WASAPI device ID."""
        ppDevice = _ffi.new('IMMDevice **')
        devid = _str2wstr(devid)
        hr = self._ptr[0][0].lpVtbl.GetDevice(self._ptr[0], _ffi.cast('wchar_t *', devid), ppDevice);
        _com.check_error(hr)
        return ppDevice

class _DeviceCollection:
    """Wrapper class for an IMMDeviceCollection**.

    Generator for IMMDevice** pointers.

    """
    def __init__(self, ptr):
        self._ptr = ptr

    def __del__(self):
        _com.release(self._ptr)

    def __len__(self):
        pCount = _ffi.new('UINT *')
        hr = self._ptr[0][0].lpVtbl.GetCount(self._ptr[0], pCount)
        _com.check_error(hr)
        return pCount[0]

    def __getitem__(self, idx):
        if idx >= len(self):
            raise StopIteration()
        ppDevice = _ffi.new('IMMDevice **')
        hr = self._ptr[0][0].lpVtbl.Item(self._ptr[0], idx, ppDevice)
        _com.check_error(hr)
        return ppDevice

class _PropVariant:
    """Wrapper class for a PROPVARIANT.

    Correctly allocates and frees a PROPVARIANT. Normal CFFI
    malloc/free is incompatible with PROPVARIANTs, since COM expects
    PROPVARIANTS to be freely reallocatable by its own allocator.

    Access the PROPVARIANT* pointer using .ptr.

    """
    def __init__(self):
        self.ptr = _combase.CoTaskMemAlloc(_ffi.sizeof('PROPVARIANT'))
        self.ptr = _ffi.cast("PROPVARIANT *", self.ptr)

    def __del__(self):
        hr = _ole32.PropVariantClear(self.ptr)
        _com.check_error(hr)

class _Device:
    """Wrapper class for an IMMDevice.

    Implements memory management and retrieval of the device name, the
    number of channels, and device activation.

    Subclassed by _Speaker and _Microphone for playback and recording.

    """

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
        _com.release(ptr)
        _com.check_error(hr)
        propvariant = _PropVariant()
        # um/functiondiscoverykeys_devpkey.h and https://msdn.microsoft.com/en-us/library/windows/desktop/dd370812(v=vs.85).aspx
        PKEY_Device_FriendlyName = _ffi.new("PROPERTYKEY *",
                                            [[0xa45c254e, 0xdf1c, 0x4efd, [0x80, 0x20, 0x67, 0xd1, 0x46, 0xa8, 0x50, 0xe0]],
                                            14])
        hr = ppPropertyStore[0][0].lpVtbl.GetValue(ppPropertyStore[0], PKEY_Device_FriendlyName, propvariant.ptr)
        _com.check_error(hr)
        if propvariant.ptr[0].vt != 31:
            raise RuntimeError('Property was expected to be a string, but is not a string')
        data = _ffi.cast("short*", propvariant.ptr[0].data)
        for idx in range(256):
            if data[idx] == 0:
                break
        devicename = ''.join(chr(c) for c in data[0:idx])
        _com.release(ppPropertyStore)
        return devicename

    @property
    def channels(self):
        # um/coml2api.h:
        ppPropertyStore = _ffi.new('IPropertyStore **')
        ptr = self._device_ptr()
        hr = ptr[0][0].lpVtbl.OpenPropertyStore(ptr[0], 0, ppPropertyStore)
        _com.release(ptr)
        _com.check_error(hr)
        propvariant = _PropVariant()
        # um/functiondiscoverykeys_devpkey.h and https://msdn.microsoft.com/en-us/library/windows/desktop/dd370812(v=vs.85).aspx
        PKEY_AudioEngine_DeviceFormat = _ffi.new("PROPERTYKEY *",
                                                 [[0xf19f064d, 0x82c, 0x4e27, [0xbc, 0x73, 0x68, 0x82, 0xa1, 0xbb, 0x8e, 0x4c]],
                                                  0])
        hr = ppPropertyStore[0][0].lpVtbl.GetValue(ppPropertyStore[0], PKEY_AudioEngine_DeviceFormat, propvariant.ptr)
        _com.release(ppPropertyStore)
        _com.check_error(hr)
        if propvariant.ptr[0].vt != 65:
            raise RuntimeError('Property was expected to be a blob, but is not a blob')
        pPropVariantBlob = _ffi.cast("BLOB_PROPVARIANT *", propvariant.ptr)
        assert pPropVariantBlob[0].blob.cbSize == 40
        waveformat = _ffi.cast("WAVEFORMATEX *", pPropVariantBlob[0].blob.pBlobData)
        channels = waveformat[0].nChannels
        return channels

    def _audio_client(self):
        CLSCTX_ALL = 23
        ppAudioClient = _ffi.new("IAudioClient **")
        IID_IAudioClient = _guidof("{1CB9AD4C-DBFA-4C32-B178-C2F568A703B2}")
        ptr = self._device_ptr()
        hr = ptr[0][0].lpVtbl.Activate(ptr[0], IID_IAudioClient, CLSCTX_ALL, _ffi.NULL, _ffi.cast("void**", ppAudioClient))
        _com.release(ptr)
        _com.check_error(hr)
        return ppAudioClient

class _Speaker(_Device):
    """A soundcard output. Can be used to play audio.

    Use the `play` method to play one piece of audio, or use the
    `player` method to get a context manager for playing continuous
    audio.

    Properties:
    - `channels`: the number of available channels.
    - `name`: the name of the sound card.
    - `id`: the WASAPI ID of the sound card.

    """

    def __init__(self, device):
        self._id = device._id

    def __repr__(self):
        return '<Speaker {} ({} channels)>'.format(self.name,self.channels)

    def player(self, samplerate, channels=None, blocksize=None):
        if channels is None:
            channels = self.channels
        return _Player(self._audio_client(), samplerate, channels, blocksize, False)

    def play(self, data, samplerate, channels=None, blocksize=None):
        with self.player(samplerate, channels, blocksize) as p:
            p.play(data)


class _Microphone(_Device):
    """A soundcard input. Can be used to record audio.

    Use the `record` method to record one piece of audio, or use the
    `recorder` method to get a context manager for recording
    continuous audio.

    Properties:
    - `channels`: the number of available channels.
    - `name`: the name of the sound card.
    - `id`: the WASAPI ID of the sound card.

    """

    def __init__(self, device, isloopback=False):
        self._id = device._id
        self.isloopback = isloopback

    def __repr__(self):
        if self.isloopback:
            return '<Loopback {} ({} channels)>'.format(self.name,self.channels)
        else:
            return '<Microphone {} ({} channels)>'.format(self.name,self.channels)

    def recorder(self, samplerate, channels=None, blocksize=None):
        if channels is None:
            channels = self.channels
        return _Recorder(self._audio_client(), samplerate, channels, blocksize, self.isloopback)

    def record(self, numframes, samplerate, channels=None, blocksize=None):
        with self.recorder(samplerate, channels, blocksize) as r:
            return r.record(numframes)

class _AudioClient:
    """Wrapper class for an IAudioClient** object.

    Implements memory management and various property retrieval for
    IAudioClient objects.

    Subclassed by _Player and _Recorder for playback and recording.

    """

    def __init__(self, ptr, samplerate, channels, blocksize, isloopback):
        self._ptr = ptr

        if isinstance(channels, int):
            self.channelmap = list(range(channels))
        elif isinstance(channels, collections.Iterable):
            self.channelmap = channels
        else:
            raise TypeError('channels must be iterable or integer')

        if list(range(len(set(self.channelmap)))) != sorted(list(set(self.channelmap))):
            raise TypeError('Due to limitations of WASAPI, channel maps on Windows '
                            'must be a combination of `range(0, x)`.')

        if blocksize is None:
            blocksize = self.deviceperiod[0]*samplerate

        ppMixFormat = _ffi.new('WAVEFORMATEXTENSIBLE**')
        hr = self._ptr[0][0].lpVtbl.GetMixFormat(self._ptr[0], ppMixFormat)
        _com.check_error(hr)

        # It's a WAVEFORMATEXTENSIBLE with room for KSDATAFORMAT_SUBTYPE_IEEE_FLOAT:
        assert ppMixFormat[0][0].Format.wFormatTag == 0xFFFE
        assert ppMixFormat[0][0].Format.cbSize == 22

        # The data format is float32:
        # These values were found empirically, and I don't know why they work.
        # The program crashes if these values are different
        assert ppMixFormat[0][0].SubFormat.Data1 == 0x100000
        assert ppMixFormat[0][0].SubFormat.Data2 == 0x0080
        assert ppMixFormat[0][0].SubFormat.Data3 == 0xaa00
        assert [int(x) for x in ppMixFormat[0][0].SubFormat.Data4[0:4]] == [0, 56, 155, 113]
        # the last four bytes seem to vary randomly

        channels = len(set(self.channelmap))
        channelmask = 0
        for ch in self.channelmap:
            channelmask |= 1<<ch
        ppMixFormat[0][0].Format.nChannels=channels
        ppMixFormat[0][0].Format.nSamplesPerSec=int(samplerate)
        ppMixFormat[0][0].Format.nAvgBytesPerSec=int(samplerate) * channels * 4
        ppMixFormat[0][0].Format.nBlockAlign=channels * 4
        ppMixFormat[0][0].Format.wBitsPerSample=32
        ppMixFormat[0][0].Samples=dict(wValidBitsPerSample=32)
        # does not work:
        # ppMixFormat[0][0].dwChannelMask=channelmask

        sharemode = _combase.AUDCLNT_SHAREMODE_SHARED
        #             resample   | remix      | better-SRC | nopersist
        streamflags = 0x00100000 | 0x80000000 | 0x08000000 | 0x00080000
        if isloopback:
            streamflags |= 0x00020000 #loopback
        bufferduration = int(blocksize/samplerate * 10000000) # in hecto-nanoseconds (1000_000_0)
        hr = self._ptr[0][0].lpVtbl.Initialize(self._ptr[0], sharemode, streamflags, bufferduration, 0, ppMixFormat[0], _ffi.NULL)
        _com.check_error(hr)
        _combase.CoTaskMemFree(ppMixFormat[0])

    @property
    def buffersize(self):
        pBufferSize = _ffi.new("UINT32*")
        hr = self._ptr[0][0].lpVtbl.GetBufferSize(self._ptr[0], pBufferSize)
        _com.check_error(hr)
        return pBufferSize[0]

    @property
    def deviceperiod(self):
        pDefaultPeriod = _ffi.new("REFERENCE_TIME*")
        pMinimumPeriod = _ffi.new("REFERENCE_TIME*")
        hr = self._ptr[0][0].lpVtbl.GetDevicePeriod(self._ptr[0], pDefaultPeriod, pMinimumPeriod)
        _com.check_error(hr)
        return pDefaultPeriod[0]/10000000, pMinimumPeriod[0]/10000000 # (1000_000_0)

    @property
    def currentpadding(self):
        pPadding = _ffi.new("UINT32*")
        hr = self._ptr[0][0].lpVtbl.GetCurrentPadding(self._ptr[0], pPadding)
        _com.check_error(hr)
        return pPadding[0]

class _Player(_AudioClient):
    """A context manager for an active output stream.

    Audio playback is available as soon as the context manager is
    entered. Audio data can be played using the `play` method.
    Successive calls to `play` will queue up the audio one piece after
    another. If no audio is queued up, this will play silence.

    This context manager can only be entered once, and can not be used
    after it is closed.

    """

    # https://msdn.microsoft.com/en-us/library/windows/desktop/dd316756(v=vs.85).aspx
    def _render_client(self):
        iid = _guidof("{F294ACFC-3146-4483-A7BF-ADDCA7C260E2}")
        ppRenderClient = _ffi.new("IAudioRenderClient**")
        hr = self._ptr[0][0].lpVtbl.GetService(self._ptr[0], iid, _ffi.cast("void**", ppRenderClient))
        _com.check_error(hr)
        return ppRenderClient

    def _render_buffer(self, numframes):
        data = _ffi.new("BYTE**")
        hr = self._ppRenderClient[0][0].lpVtbl.GetBuffer(self._ppRenderClient[0], numframes, data)
        _com.check_error(hr)
        return data

    def _render_release(self, numframes):
        hr = self._ppRenderClient[0][0].lpVtbl.ReleaseBuffer(self._ppRenderClient[0], numframes, 0)
        _com.check_error(hr)

    def _render_available_frames(self):
        return self.buffersize-self.currentpadding

    def __enter__(self):
        self._ppRenderClient = self._render_client()
        hr = self._ptr[0][0].lpVtbl.Start(self._ptr[0])
        _com.check_error(hr)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        hr = self._ptr[0][0].lpVtbl.Stop(self._ptr[0])
        _com.check_error(hr)
        _com.release(self._ppRenderClient)
        _com.release(self._ptr)

    def play(self, data):
        """Play some audio data.

        Internally, all data is handled as float32 and with the
        appropriate number of channels. For maximum performance,
        provide data as a `frames x channels` float32 numpy array.

        If single-channel or one-dimensional data is given, this data
        will be played on all available channels.

        This function will return *before* all data has been played,
        so that additional data can be provided for gapless playback.
        The amount of buffering can be controlled through the
        blocksize of the player object.

        If data is provided faster than it is played, later pieces
        will be queued up and played one after another.

        """

        data = numpy.array(data, dtype='float32', order='C')
        if data.ndim == 1:
            data = data[:, None] # force 2d
        if data.ndim != 2:
            raise TypeError('data must be 1d or 2d, not {}d'.format(data.ndim))
        if data.shape[1] == 1 and len(set(self.channelmap)) != 1:
            data = numpy.tile(data, [1, len(set(self.channelmap))])

        # internally, channel numbers are always ascending:
        sortidx = sorted(range(len(self.channelmap)), key=lambda k: self.channelmap[k])
        data = data[:, sortidx]

        if data.shape[1] != len(set(self.channelmap)):
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
    """A context manager for an active input stream.

    Audio recording is available as soon as the context manager is
    entered. Recorded audio data can be read using the `record`
    method. If no audio data is available, `record` will block until
    the requested amount of audio data has been recorded.

    This context manager can only be entered once, and can not be used
    after it is closed.

    """

    # https://msdn.microsoft.com/en-us/library/windows/desktop/dd370800(v=vs.85).aspx
    def _capture_client(self):
        iid = _guidof("{C8ADBD64-E71E-48a0-A4DE-185C395CD317}")
        ppCaptureClient = _ffi.new("IAudioCaptureClient**")
        hr = self._ptr[0][0].lpVtbl.GetService(self._ptr[0], iid, _ffi.cast("void**", ppCaptureClient))
        _com.check_error(hr)
        return ppCaptureClient

    def _capture_buffer(self):
        data = _ffi.new("BYTE**")
        toread = _ffi.new('UINT32*')
        flags = _ffi.new('DWORD*')
        hr = self._ppCaptureClient[0][0].lpVtbl.GetBuffer(self._ppCaptureClient[0], data, toread, flags, _ffi.NULL, _ffi.NULL)
        _com.check_error(hr)
        return data[0], toread[0], flags[0]

    def _capture_release(self, numframes):
        hr = self._ppCaptureClient[0][0].lpVtbl.ReleaseBuffer(self._ppCaptureClient[0], numframes)
        _com.check_error(hr)

    def _capture_available_frames(self):
        pSize = _ffi.new("UINT32*")
        hr = self._ppCaptureClient[0][0].lpVtbl.GetNextPacketSize(self._ppCaptureClient[0], pSize)
        _com.check_error(hr)
        return pSize[0]

    def __enter__(self):
        self._ppCaptureClient = self._capture_client()
        hr = self._ptr[0][0].lpVtbl.Start(self._ptr[0])
        _com.check_error(hr)
        self._pending_chunk = numpy.zeros([0])
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        hr = self._ptr[0][0].lpVtbl.Stop(self._ptr[0])
        _com.check_error(hr)
        _com.release(self._ppCaptureClient)
        _com.release(self._ptr)

    def _record_chunk(self):
        """Record one chunk of audio data, as returned by WASAPI

        The data will be returned as a 1D numpy array, which will be used by
        the `record` method. This function is the interface of the `_Recorder`
        object with WASAPI.

        """

        while not self._capture_available_frames():
            time.sleep(0.001)
        data_ptr, nframes, flags = self._capture_buffer()
        if data_ptr != _ffi.NULL:
            chunk = numpy.fromstring(_ffi.buffer(data_ptr, nframes*4*len(set(self.channelmap))), dtype='float32')
        else:
            raise RuntimeError('Could not create capture buffer')
        if nframes > 0:
            self._capture_release(nframes)
            return chunk
        else:
            return numpy.zeros([0])

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
            recorded_data = [self._pending_chunk, self._record_chunk()]
            self._pending_chunk = numpy.zeros([0])
        else:
            recorded_frames = len(self._pending_chunk)
            recorded_data = [self._pending_chunk]
            self._pending_chunk = numpy.zeros([0])
            required_frames = numframes*len(set(self.channelmap))
            while recorded_frames < required_frames:
                chunk = self._record_chunk()
                recorded_data.append(chunk)
                recorded_frames += len(chunk)
            if recorded_frames > required_frames:
                to_split = -(recorded_frames-required_frames)
                recorded_data[-1], self._pending_chunk = numpy.split(recorded_data[-1], [to_split])

        data = numpy.reshape(numpy.concatenate(recorded_data), [-1, len(set(self.channelmap))])
        return data[:, self.channelmap]

    def flush(self):
        """Return the last pending chunk
        After using the record method, this will return the last incomplete
        chunk and delete it.

        """
        last_chunk = numpy.reshape(self._pending_chunk, [-1, len(set(self.channelmap))])
        self._pending_chunk = numpy.zeros([0])
        return last_chunk
