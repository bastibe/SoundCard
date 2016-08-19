"""Re-Implementation of https://msdn.microsoft.com/en-us/library/windows/desktop/aa369729%28v=vs.85%29.aspx using the CFFI"""

from cffi import FFI

ffi = FFI()

ffi.cdef("""
// see um/winnt.h:
typedef long HRESULT;
typedef wchar_t *LPWSTR;

// originally, struct=interface, see um/combaseapi.h

// see shared/rpcndr.h:
typedef unsigned char byte;

// see shared/guiddef.h:
typedef struct {
    unsigned long  Data1;
    unsigned short Data2;
    unsigned short Data3;
    byte           Data4[ 8 ];
} GUID;
typedef GUID IID;
typedef IID *LPIID;

// see um/mmdeviceapi.h:
typedef struct IMMDeviceEnumerator IMMDeviceEnumerator;
typedef struct IMMDeviceCollection IMMDeviceCollection;
typedef struct IMMDevice IMMDevice;
typedef struct IMMNotificationClient IMMNotificationClient;

// see um/mfidl.h:
typedef struct IMFMediaSink IMFMediaSink;

// see um/mfobjects.h:
typedef struct IMFAttributes IMFAttributes;

// see um/Unknwn.h:
typedef struct IUnknown IUnknown;
typedef IUnknown *LPUNKNOWN;

// see shared/wtypes.h:
typedef unsigned long DWORD;
typedef const char *LPCSTR;

// see shared/WTypesbase.h:
typedef void *LPVOID;
typedef LPCSTR LPCOLESTR;
typedef IID *REFIID;

// see um/combaseapi.h:
HRESULT CoCreateInstance(const GUID* rclsid, LPUNKNOWN pUnkOuter, DWORD dwClsContext, const GUID* riid, LPVOID * ppv);
HRESULT IIDFromString(LPCOLESTR lpsz, LPIID lpiid);
HRESULT CoInitializeEx(LPVOID pvReserved, DWORD dwCoInit);

// see um/mmdeviceapi.h:
typedef enum EDataFlow {eRender, eCapture, eAll, EDataFlow_enum_count} EDataFlow;

typedef enum ERole {eConsole, eMultimedia, eCommunications, ERole_enum_count} ERole;

typedef struct IMMDeviceEnumeratorVtbl
{
    HRESULT ( __stdcall *QueryInterface )(IMMDeviceEnumerator * This, const GUID *riid, void **ppvObject);
    ULONG ( __stdcall *AddRef )(IMMDeviceEnumerator * This);
    ULONG ( __stdcall *Release )(IMMDeviceEnumerator * This);
    HRESULT ( __stdcall *EnumAudioEndpoints )(IMMDeviceEnumerator * This, EDataFlow dataFlow, DWORD dwStateMask, IMMDeviceCollection **ppDevices);
    HRESULT ( __stdcall *GetDefaultAudioEndpoint )(IMMDeviceEnumerator * This, EDataFlow dataFlow, ERole role, IMMDevice **ppEndpoint);
    HRESULT ( __stdcall *GetDevice )(IMMDeviceEnumerator * This, LPCWSTR pwstrId, IMMDevice **ppDevice);
/* I hope I won't need these
    HRESULT ( __stdcall *RegisterEndpointNotificationCallback )(IMMDeviceEnumerator * This, IMMNotificationClient *pClient);
    HRESULT ( __stdcall *UnregisterEndpointNotificationCallback )(IMMDeviceEnumerator * This, IMMNotificationClient *pClient);
*/
} IMMDeviceEnumeratorVtbl;

struct IMMDeviceEnumerator
{
    const struct IMMDeviceEnumeratorVtbl *lpVtbl;
};

typedef struct IMMDeviceCollectionVtbl
{
    HRESULT ( __stdcall *QueryInterface )(IMMDeviceCollection * This, REFIID riid, void **ppvObject);
    ULONG ( __stdcall *AddRef )(IMMDeviceCollection * This);
    ULONG ( __stdcall *Release )(IMMDeviceCollection * This);
    HRESULT ( __stdcall *GetCount )(IMMDeviceCollection * This, UINT *pcDevices);
    HRESULT ( __stdcall *Item )(IMMDeviceCollection * This, UINT nDevice, IMMDevice **ppDevice);
} IMMDeviceCollectionVtbl;

struct IMMDeviceCollection
{
    const struct IMMDeviceCollectionVtbl *lpVtbl;
};

// see um/mfobjects.h:

typedef struct IMFAttributesVtbl
    {
        BEGIN_INTERFACE

        HRESULT ( STDMETHODCALLTYPE *QueryInterface )(
            __RPC__in IMFAttributes * This,
            /* [in] */ __RPC__in REFIID riid,
            /* [annotation][iid_is][out] */
            _COM_Outptr_  void **ppvObject);

        ULONG ( STDMETHODCALLTYPE *AddRef )(
            __RPC__in IMFAttributes * This);

        ULONG ( STDMETHODCALLTYPE *Release )(
            __RPC__in IMFAttributes * This);

        HRESULT ( STDMETHODCALLTYPE *GetItem )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [full][out][in] */ __RPC__inout_opt PROPVARIANT *pValue);

        HRESULT ( STDMETHODCALLTYPE *GetItemType )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [out] */ __RPC__out MF_ATTRIBUTE_TYPE *pType);

        HRESULT ( STDMETHODCALLTYPE *CompareItem )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            __RPC__in REFPROPVARIANT Value,
            /* [out] */ __RPC__out BOOL *pbResult);

        HRESULT ( STDMETHODCALLTYPE *Compare )(
            __RPC__in IMFAttributes * This,
            __RPC__in_opt IMFAttributes *pTheirs,
            MF_ATTRIBUTES_MATCH_TYPE MatchType,
            /* [out] */ __RPC__out BOOL *pbResult);

        HRESULT ( STDMETHODCALLTYPE *GetUINT32 )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [out] */ __RPC__out UINT32 *punValue);

        HRESULT ( STDMETHODCALLTYPE *GetUINT64 )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [out] */ __RPC__out UINT64 *punValue);

        HRESULT ( STDMETHODCALLTYPE *GetDouble )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [out] */ __RPC__out double *pfValue);

        HRESULT ( STDMETHODCALLTYPE *GetGUID )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [out] */ __RPC__out GUID *pguidValue);

        HRESULT ( STDMETHODCALLTYPE *GetStringLength )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [out] */ __RPC__out UINT32 *pcchLength);

        HRESULT ( STDMETHODCALLTYPE *GetString )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [size_is][out] */ __RPC__out_ecount_full(cchBufSize) LPWSTR pwszValue,
            UINT32 cchBufSize,
            /* [full][out][in] */ __RPC__inout_opt UINT32 *pcchLength);

        HRESULT ( STDMETHODCALLTYPE *GetAllocatedString )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [size_is][size_is][out] */ __RPC__deref_out_ecount_full_opt(( *pcchLength + 1 ) ) LPWSTR *ppwszValue,
            /* [out] */ __RPC__out UINT32 *pcchLength);

        HRESULT ( STDMETHODCALLTYPE *GetBlobSize )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [out] */ __RPC__out UINT32 *pcbBlobSize);

        HRESULT ( STDMETHODCALLTYPE *GetBlob )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [size_is][out] */ __RPC__out_ecount_full(cbBufSize) UINT8 *pBuf,
            UINT32 cbBufSize,
            /* [full][out][in] */ __RPC__inout_opt UINT32 *pcbBlobSize);

        HRESULT ( STDMETHODCALLTYPE *GetAllocatedBlob )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [size_is][size_is][out] */ __RPC__deref_out_ecount_full_opt(*pcbSize) UINT8 **ppBuf,
            /* [out] */ __RPC__out UINT32 *pcbSize);

        HRESULT ( STDMETHODCALLTYPE *GetUnknown )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            __RPC__in REFIID riid,
            /* [iid_is][out] */ __RPC__deref_out_opt LPVOID *ppv);

        HRESULT ( STDMETHODCALLTYPE *SetItem )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            __RPC__in REFPROPVARIANT Value);

        HRESULT ( STDMETHODCALLTYPE *DeleteItem )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey);

        HRESULT ( STDMETHODCALLTYPE *DeleteAllItems )(
            __RPC__in IMFAttributes * This);

        HRESULT ( STDMETHODCALLTYPE *SetUINT32 )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            UINT32 unValue);

        HRESULT ( STDMETHODCALLTYPE *SetUINT64 )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            UINT64 unValue);

        HRESULT ( STDMETHODCALLTYPE *SetDouble )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            double fValue);

        HRESULT ( STDMETHODCALLTYPE *SetGUID )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            __RPC__in REFGUID guidValue);

        HRESULT ( STDMETHODCALLTYPE *SetString )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [string][in] */ __RPC__in_string LPCWSTR wszValue);

        HRESULT ( STDMETHODCALLTYPE *SetBlob )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [size_is][in] */ __RPC__in_ecount_full(cbBufSize) const UINT8 *pBuf,
            UINT32 cbBufSize);

        HRESULT ( STDMETHODCALLTYPE *SetUnknown )(
            __RPC__in IMFAttributes * This,
            __RPC__in REFGUID guidKey,
            /* [in] */ __RPC__in_opt IUnknown *pUnknown);

        HRESULT ( STDMETHODCALLTYPE *LockStore )(
            __RPC__in IMFAttributes * This);

        HRESULT ( STDMETHODCALLTYPE *UnlockStore )(
            __RPC__in IMFAttributes * This);

        HRESULT ( STDMETHODCALLTYPE *GetCount )(
            __RPC__in IMFAttributes * This,
            /* [out] */ __RPC__out UINT32 *pcItems);

        HRESULT ( STDMETHODCALLTYPE *GetItemByIndex )(
            __RPC__in IMFAttributes * This,
            UINT32 unIndex,
            /* [out] */ __RPC__out GUID *pguidKey,
            /* [full][out][in] */ __RPC__inout_opt PROPVARIANT *pValue);

        HRESULT ( STDMETHODCALLTYPE *CopyAllItems )(
            __RPC__in IMFAttributes * This,
            /* [in] */ __RPC__in_opt IMFAttributes *pDest);

        END_INTERFACE
    } IMFAttributesVtbl;

    interface IMFAttributes
    {
        CONST_VTBL struct IMFAttributesVtbl *lpVtbl;
    };

""")

mmdefapi = ffi.dlopen('MMDevAPI')
combase = ffi.dlopen('combase')

def str2wstr(string):
    return ffi.new('int16_t[39]', [ord(s) for s in string]+[0])

def guidof(uuid_str):
    IID = ffi.new('LPIID')
    # convert to zero terminated wide string
    uuid = str2wstr(uuid_str)
    hr = combase.IIDFromString(ffi.cast("char*", uuid), IID)
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
        raise RuntimeError('The ppv parameter is NULL.')
    elif hr+2**32 == E_INVALIDARG:
        raise RuntimeError("invalid argument")
    elif hr+2**32 == E_OUTOFMEMORY:
        raise RuntimeError("out of memory")
    else:
        raise RuntimeError('Error {}'.format(hex(hr+2**32)))

def CoInitializeEx():
    COINIT_MULTITHREADED = 0x0
    hr = combase.CoInitializeEx(ffi.NULL, COINIT_MULTITHREADED)
    check_errors(hr)

def CoCreateInstance(rclsid, pUnkOuter, riid, ppv):
    # see shared/WTypesbase.h and um/combaseapi.h:
    CLSCTX_ALL = 23
    hr = combase.CoCreateInstance(rclsid, pUnkOuter, CLSCTX_ALL, riid, ppv)
    check_errors(hr)

def DeviceEnumerator_EnumAudioEndpoints(self, dataFlow):
    DEVICE_STATE_ACTIVE = 0x1
    ppDevices = ffi.new('IMMDeviceCollection **')
    hr = self[0][0].lpVtbl.EnumAudioEndpoints(self[0], mmdefapi.eRender, DEVICE_STATE_ACTIVE, ppDevices);
    check_errors(hr)
    return ppDevices

def DeviceCollection_Item(self, nDevice):
    ppDevice = ffi.new('IMMDevice **')
    hr = self[0][0].lpVtbl.Item(self[0], nDevice, ppDevice)
    check_errors(hr)
    return ppDevice

CoInitializeEx()

# Create the device enumerator.
ppEnum = ffi.new('IMMDeviceEnumerator **')
IID_MMDeviceEnumerator = guidof("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
IID_IMMDeviceEnumerator = guidof("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
CoCreateInstance(IID_MMDeviceEnumerator, ffi.NULL,
                 IID_IMMDeviceEnumerator, ffi.cast("void **", ppEnum))

# Enumerate the rendering devices.
ppDevices = DeviceEnumerator_EnumAudioEndpoints(ppEnum, mmdefapi.eRender)

# Get ID of the first device in the list.
ppDevice = DeviceCollection_Item(ppDevices, 0)

# Create an attribute store and set the device ID attribute.
