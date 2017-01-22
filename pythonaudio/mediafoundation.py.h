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

typedef struct tWAVEFORMATEX {
    WORD    wFormatTag;        /* format type */
    WORD    nChannels;         /* number of channels (i.e. mono, stereo...) */
    DWORD   nSamplesPerSec;    /* sample rate */
    DWORD   nAvgBytesPerSec;   /* for buffer estimation */
    WORD    nBlockAlign;       /* block size of data */
    WORD    wBitsPerSample;    /* Number of bits per sample of mono data */
    WORD    cbSize;            /* The count in bytes of the size of
                                    extra information (after cbSize) */
} WAVEFORMATEX;
