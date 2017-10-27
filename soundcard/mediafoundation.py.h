// see um/winnt.h:
typedef long HRESULT;
typedef wchar_t *LPWSTR;
typedef long long LONGLONG;

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
void CoTaskMemFree(LPVOID pv);
LPVOID CoTaskMemAlloc(size_t cb);
void CoUninitialize(void);

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

// um/propsys.h
typedef struct IPropertyStore IPropertyStore;
// um/combaseapi.h
typedef struct tag_inner_PROPVARIANT PROPVARIANT;
// shared/wtypes.h
typedef unsigned short VARTYPE;
// um/propidl.h
struct tag_inner_PROPVARIANT {
    VARTYPE vt;
    WORD wReserved1;
    WORD wReserved2;
    WORD wReserved3;
    void * data;
};
void PropVariantInit(PROPVARIANT *p);
HRESULT PropVariantClear(PROPVARIANT *p);

typedef struct IMMDeviceVtbl {
    HRESULT ( __stdcall *QueryInterface )(IMMDevice * This, REFIID riid, void **ppvObject);
    ULONG ( __stdcall *AddRef )(IMMDevice * This);
    ULONG ( __stdcall *Release )(IMMDevice * This);
    HRESULT ( __stdcall *Activate )(IMMDevice * This, REFIID iid, DWORD dwClsCtx, PROPVARIANT *pActivationParams, void **ppInterface);
    HRESULT ( __stdcall *OpenPropertyStore )(IMMDevice * This, DWORD stgmAccess, IPropertyStore **ppProperties);
    HRESULT ( __stdcall *GetId )(IMMDevice * This, LPWSTR *ppstrId);
    HRESULT ( __stdcall *GetState )(IMMDevice * This, DWORD *pdwState);
} IMMDeviceVtbl;

struct IMMDevice {
    const struct IMMDeviceVtbl *lpVtbl;
};

// um/propkeydef.h
typedef struct {
  GUID  fmtid;
  DWORD pid;
} PROPERTYKEY;

const PROPERTYKEY PKEY_Device_FriendlyName = {{0xa45c254e, 0xdf1c, 0x4efd, {0x80, 0x20, 0x67, 0xd1, 0x46, 0xa8, 0x50, 0xe0}}, 14};
const PROPERTYKEY PKEY_AudioEngine_DeviceFormat = {{0xf19f064d, 0x82c, 0x4e27, {0xbc, 0x73, 0x68, 0x82, 0xa1, 0xbb, 0x8e, 0x4c}}, 0};

typedef struct IPropertyStoreVtbl {
    HRESULT ( __stdcall *QueryInterface )(IPropertyStore * This, REFIID riid, void **ppvObject);
    ULONG ( __stdcall *AddRef )(IPropertyStore * This);
    ULONG ( __stdcall *Release )(IPropertyStore * This);
    HRESULT ( __stdcall *GetCount )(IPropertyStore * This, DWORD *cProps);
    HRESULT ( __stdcall *GetAt )(IPropertyStore * This, DWORD iProp, PROPERTYKEY *pkey);
    HRESULT ( __stdcall *GetValue )(IPropertyStore * This, const PROPERTYKEY *key, PROPVARIANT *pv);
    HRESULT ( __stdcall *SetValue )(IPropertyStore * This, const PROPERTYKEY *key, const PROPVARIANT *propvar);
    HRESULT ( __stdcall *Commit )(IPropertyStore * This);
} IPropertyStoreVtbl;

struct IPropertyStore {
    const struct IPropertyStoreVtbl *lpVtbl;
};

// shared/WTypesbase.h
typedef struct tagBLOB {
    ULONG cbSize;
    BYTE *pBlobData;
} BLOB;


typedef struct tag_inner_BLOB_PROPVARIANT BLOB_PROPVARIANT;
struct tag_inner_BLOB_PROPVARIANT {
    VARTYPE vt;
    WORD wReserved1;
    WORD wReserved2;
    WORD wReserved3;
    BLOB blob;
};

typedef struct WAVEFORMATEX {
    WORD    wFormatTag;        /* format type */
    WORD    nChannels;         /* number of channels (i.e. mono, stereo...) */
    DWORD   nSamplesPerSec;    /* sample rate */
    DWORD   nAvgBytesPerSec;   /* for buffer estimation */
    WORD    nBlockAlign;       /* block size of data */
    WORD    wBitsPerSample;    /* Number of bits per sample of mono data */
    WORD    cbSize;            /* The count in bytes of the size of
                                    extra information (after cbSize) */
} WAVEFORMATEX;

typedef struct {
    WAVEFORMATEX Format;
    union {
        WORD wValidBitsPerSample;       /* bits of precision  */
        WORD wSamplesPerBlock;          /* valid if wBitsPerSample==0 */
        WORD wReserved;                 /* If neither applies, set to zero. */
    } Samples;
    DWORD           dwChannelMask;      /* which channels are */
                                        /* present in stream  */
    GUID            SubFormat;
} WAVEFORMATEXTENSIBLE, *PWAVEFORMATEXTENSIBLE;

// um/AudioSessionTypes.h
typedef enum _AUDCLNT_SHAREMODE
{
    AUDCLNT_SHAREMODE_SHARED,
    AUDCLNT_SHAREMODE_EXCLUSIVE
} AUDCLNT_SHAREMODE;

// um/dsound.h
typedef const GUID *LPCGUID;

// um/Audioclient.h
typedef LONGLONG REFERENCE_TIME;

typedef struct IAudioClient IAudioClient;

typedef struct IAudioClientVtbl {
    HRESULT ( __stdcall *QueryInterface )(IAudioClient * This, REFIID riid, void **ppvObject);
    ULONG ( __stdcall *AddRef )(IAudioClient * This);
    ULONG ( __stdcall *Release )(IAudioClient * This);
    HRESULT ( __stdcall *Initialize )(IAudioClient * This, AUDCLNT_SHAREMODE ShareMode, DWORD StreamFlags, REFERENCE_TIME hnsBufferDuration, REFERENCE_TIME hnsPeriodicity, const WAVEFORMATEXTENSIBLE *pFormat, LPCGUID AudioSessionGuid);
    HRESULT ( __stdcall *GetBufferSize )(IAudioClient * This, UINT32 *pNumBufferFrames);
    HRESULT ( __stdcall *GetStreamLatency )(IAudioClient * This, REFERENCE_TIME *phnsLatency);
    HRESULT ( __stdcall *GetCurrentPadding )(IAudioClient * This, UINT32 *pNumPaddingFrames);
    HRESULT ( __stdcall *IsFormatSupported )(IAudioClient * This, AUDCLNT_SHAREMODE ShareMode, const WAVEFORMATEXTENSIBLE *pFormat, WAVEFORMATEXTENSIBLE **ppClosestMatch);
    HRESULT ( __stdcall *GetMixFormat )(IAudioClient * This, WAVEFORMATEXTENSIBLE **ppDeviceFormat);
    HRESULT ( __stdcall *GetDevicePeriod )(IAudioClient * This, REFERENCE_TIME *phnsDefaultDevicePeriod, REFERENCE_TIME *phnsMinimumDevicePeriod);
    HRESULT ( __stdcall *Start )(IAudioClient * This);
    HRESULT ( __stdcall *Stop )(IAudioClient * This);
    HRESULT ( __stdcall *Reset )(IAudioClient * This);
    HRESULT ( __stdcall *SetEventHandle )(IAudioClient * This, HANDLE eventHandle);
    HRESULT ( __stdcall *GetService )(IAudioClient * This, REFIID riid, void **ppv);
} IAudioClientVtbl;

struct IAudioClient {
    const struct IAudioClientVtbl *lpVtbl;
};

typedef struct IAudioRenderClient IAudioRenderClient;

typedef struct IAudioRenderClientVtbl {
        HRESULT ( __stdcall *QueryInterface )(IAudioRenderClient * This, REFIID riid, void **ppvObject);
        ULONG ( __stdcall *AddRef )(IAudioRenderClient * This);
        ULONG ( __stdcall *Release )(IAudioRenderClient * This);
        HRESULT ( __stdcall *GetBuffer )(IAudioRenderClient * This, UINT32 NumFramesRequested, BYTE **ppData);
        HRESULT ( __stdcall *ReleaseBuffer )(IAudioRenderClient * This, UINT32 NumFramesWritten, DWORD dwFlags);
} IAudioRenderClientVtbl;

struct IAudioRenderClient {
    const struct IAudioRenderClientVtbl *lpVtbl;
};

typedef struct IAudioCaptureClient IAudioCaptureClient;

typedef struct IAudioCaptureClientVtbl {
        HRESULT ( __stdcall *QueryInterface )(IAudioCaptureClient * This, REFIID riid, void **ppvObject);
        ULONG ( __stdcall *AddRef )(IAudioCaptureClient * This);
        ULONG ( __stdcall *Release )(IAudioCaptureClient * This);
        HRESULT ( __stdcall *GetBuffer )(IAudioCaptureClient * This, BYTE **ppData, UINT32 *pNumFramesToRead, DWORD *pdwFlags, UINT64 *pu64DevicePosition, UINT64 *pu64QPCPosition);
        HRESULT ( __stdcall *ReleaseBuffer )(IAudioCaptureClient * This, UINT32 NumFramesRead);
        HRESULT ( __stdcall *GetNextPacketSize )(IAudioCaptureClient * This, UINT32 *pNumFramesInNextPacket);
} IAudioCaptureClientVtbl;

struct IAudioCaptureClient {
        const struct IAudioCaptureClientVtbl *lpVtbl;
};
