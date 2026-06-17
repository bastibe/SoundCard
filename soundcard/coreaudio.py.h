// All files are found in /System/Library/Frameworks

// CoreFoundation/CFBase.h:
typedef unsigned char           Boolean;
typedef unsigned char           UInt8;
typedef signed char             SInt8;
typedef unsigned short          UInt16;
typedef signed short            SInt16;
typedef unsigned int            UInt32;
typedef signed int              SInt32;
typedef uint64_t		        UInt64;
typedef int64_t		            SInt64;
typedef SInt32                  OSStatus;
typedef float                   Float32;
typedef double                  Float64;
typedef unsigned short          UniChar;
typedef unsigned long           UniCharCount;
typedef unsigned char *         StringPtr;
typedef const unsigned char *   ConstStringPtr;
typedef unsigned char           Str255[256];
typedef const unsigned char *   ConstStr255Param;
typedef SInt16                  OSErr;
typedef SInt16                  RegionCode;
typedef SInt16                  LangCode;
typedef SInt16                  ScriptCode;
typedef UInt32                  FourCharCode;
typedef FourCharCode            OSType;
typedef UInt8                   Byte;
typedef SInt8                   SignedByte;
typedef UInt32                  UTF32Char;
typedef UInt16                  UTF16Char;
typedef UInt8                   UTF8Char;
typedef signed long long CFIndex;
typedef const void * CFStringRef;
typedef unsigned long long      CFHashCode;
typedef const void *            CFAllocatorRef;

// CoreFoundation/CFString.h
typedef UInt32 CFStringEncoding;
CFIndex CFStringGetLength(CFStringRef theString);
Boolean CFStringGetCString(CFStringRef theString, char *buffer, CFIndex bufferSize, CFStringEncoding encoding);
extern CFStringRef CFStringCreateWithCString(CFAllocatorRef alloc, const char *cStr, CFStringEncoding encoding);

// CoreFoundation/CFDictionary.h
typedef const void *            CFDictionaryRef;
typedef const void *            CFMutableDictionaryRef;
typedef const void *	        (*CFDictionaryRetainCallBack)(CFAllocatorRef allocator, const void *value);
typedef void		            (*CFDictionaryReleaseCallBack)(CFAllocatorRef allocator, const void *value);
typedef CFStringRef	            (*CFDictionaryCopyDescriptionCallBack)(const void *value);
typedef Boolean		            (*CFDictionaryEqualCallBack)(const void *value1, const void *value2);
typedef CFHashCode	            (*CFDictionaryHashCallBack)(const void *value);

typedef struct {
    CFIndex				version;
    CFDictionaryRetainCallBack		retain;
    CFDictionaryReleaseCallBack		release;
    CFDictionaryCopyDescriptionCallBack	copyDescription;
    CFDictionaryEqualCallBack		equal;
    CFDictionaryHashCallBack		hash;
} CFDictionaryKeyCallBacks;

typedef struct {
    CFIndex				version;
    CFDictionaryRetainCallBack		retain;
    CFDictionaryReleaseCallBack		release;
    CFDictionaryCopyDescriptionCallBack	copyDescription;
    CFDictionaryEqualCallBack		equal;
} CFDictionaryValueCallBacks;

extern CFMutableDictionaryRef CFDictionaryCreateMutable(
        CFAllocatorRef allocator,
        CFIndex capacity,
        const CFDictionaryKeyCallBacks *keyCallBacks,
        const CFDictionaryValueCallBacks *valueCallBacks);
extern void CFDictionaryAddValue(
        CFMutableDictionaryRef theDict,
        const void *key,
        const void *value);


// objc/objc.h
typedef struct objc_object *id;
typedef struct objc_selector *SEL;
extern SEL sel_registerName(const char *str);

// objc/message.h
extern id objc_msgSend(id self, SEL op, ...);

// objc/runtime.h
extern id objc_getClass(const char *name);


// CoreFoundation/CFRunLoop.h
typedef struct __CFRunLoop * CFRunLoopRef;

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
OSStatus AudioObjectSetPropertyData(AudioObjectID inObjectID,
                                    const AudioObjectPropertyAddress* inAddress,
                                    UInt32 inQualifierDataSize,
                                    const void* inQualifierData,
                                    UInt32 inDataSize,
                                    const void* inData);

extern OSStatus AudioHardwareCreateAggregateDevice(CFDictionaryRef inDescription,
                                                   AudioObjectID  *outDeviceID);
extern OSStatus AudioHardwareDestroyAggregateDevice(AudioObjectID inDeviceID);


// CoreAudio/AudioHardwareTapping.h
extern OSStatus AudioHardwareCreateProcessTap(id inDescription,
                                              AudioObjectID *outTapID);
extern OSStatus AudioHardwareDestroyProcessTap(AudioObjectID inTapID);


// CoreAudioTypes.h
typedef UInt32	AudioFormatID;
typedef UInt32	AudioFormatFlags;
struct AudioStreamBasicDescription
{
    Float64             mSampleRate;
    AudioFormatID       mFormatID;
    AudioFormatFlags    mFormatFlags;
    UInt32              mBytesPerPacket;
    UInt32              mFramesPerPacket;
    UInt32              mBytesPerFrame;
    UInt32              mChannelsPerFrame;
    UInt32              mBitsPerChannel;
    UInt32              mReserved;
};
typedef struct AudioStreamBasicDescription  AudioStreamBasicDescription;
struct  AudioStreamPacketDescription
{
    SInt64  mStartOffset;
    UInt32  mVariableFramesInPacket;
    UInt32  mDataByteSize;
};
typedef struct AudioStreamPacketDescription AudioStreamPacketDescription;

// AudioToolbox/AudioQueue.h

// data structures:

struct SMPTETime
{
    SInt16  mSubframes;
    SInt16  mSubframeDivisor;
    UInt32  mCounter;
    UInt32  mType;
    UInt32  mFlags;
    SInt16  mHours;
    SInt16  mMinutes;
    SInt16  mSeconds;
    SInt16  mFrames;
};
typedef struct SMPTETime    SMPTETime;
struct AudioTimeStamp
{
    Float64         mSampleTime;
    UInt64          mHostTime;
    Float64         mRateScalar;
    UInt64          mWordClockTime;
    SMPTETime       mSMPTETime;
    UInt32          mFlags;
    UInt32          mReserved;
};
typedef struct AudioTimeStamp   AudioTimeStamp;

// AudioComponent.h

typedef struct AudioComponentDescription {
    OSType              componentType;
    OSType              componentSubType;
    OSType              componentManufacturer;
    UInt32              componentFlags;
    UInt32              componentFlagsMask;
} AudioComponentDescription;
typedef struct OpaqueAudioComponent *   AudioComponent;
typedef struct ComponentInstanceRecord *        AudioComponentInstance;
AudioComponent AudioComponentFindNext(AudioComponent inComponent,
                                      const AudioComponentDescription *inDesc);
OSStatus AudioComponentInstanceNew(AudioComponent inComponent,
                                   AudioComponentInstance *outInstance);
OSStatus AudioComponentInstanceDispose(AudioComponentInstance inInstance);
OSStatus AudioComponentCopyName(AudioComponent inComponent,
                                CFStringRef *outName);
OSStatus AudioComponentGetDescription(AudioComponent inComponent,
                                      AudioComponentDescription *outDesc);

// AUComponent.h

typedef AudioComponentInstance AudioUnit;
typedef UInt32 AudioUnitPropertyID;
typedef UInt32 AudioUnitScope;
typedef UInt32 AudioUnitElement;

OSStatus AudioUnitInitialize(AudioUnit inUnit);
OSStatus AudioUnitGetPropertyInfo(AudioUnit	inUnit,
                                  AudioUnitPropertyID inID,
                                  AudioUnitScope inScope,
                                  AudioUnitElement inElement,
                                  UInt32 *outDataSize,
                                  Boolean *outWritable);
OSStatus AudioUnitGetProperty(AudioUnit inUnit,
                              AudioUnitPropertyID inID,
                              AudioUnitScope inScope,
                              AudioUnitElement inElement,
                              void *outData,
                              UInt32 *ioDataSize);
OSStatus AudioUnitSetProperty(AudioUnit inUnit,
                              AudioUnitPropertyID inID,
                              AudioUnitScope inScope,
                              AudioUnitElement inElement,
                              const void *inData,
                              UInt32 inDataSize);

OSStatus AudioOutputUnitStart(AudioUnit	ci);
OSStatus AudioOutputUnitStop(AudioUnit ci);

typedef UInt32 AudioUnitRenderActionFlags;

struct AudioBuffer
{
    UInt32 mNumberChannels;
    UInt32 mDataByteSize;
    void* mData;
};
typedef struct AudioBuffer  AudioBuffer;

struct AudioBufferList
{
    UInt32      mNumberBuffers;
    AudioBuffer mBuffers[]; // this is a variable length array of mNumberBuffers elements
};
typedef struct AudioBufferList  AudioBufferList;

OSStatus AudioUnitProcess(AudioUnit inUnit,
                          AudioUnitRenderActionFlags * ioActionFlags,
                          const AudioTimeStamp *inTimeStamp,
                          UInt32 inNumberFrames,
                          AudioBufferList *ioData);
OSStatus AudioUnitRender(AudioUnit inUnit,
                         AudioUnitRenderActionFlags * ioActionFlags,
                         const AudioTimeStamp * inTimeStamp,
                         UInt32 inOutputBusNumber,
                         UInt32 inNumberFrames,
                         AudioBufferList *ioData);

typedef OSStatus (*AURenderCallback)(void * inRefCon,
                                     AudioUnitRenderActionFlags *ioActionFlags,
                                     const AudioTimeStamp *inTimeStamp,
                                     UInt32 inBusNumber,
                                     UInt32 inNumberFrames,
                                     AudioBufferList *ioData);

typedef struct AURenderCallbackStruct {
	AURenderCallback inputProc;
	void *inputProcRefCon;
} AURenderCallbackStruct;

struct AudioValueRange
{
    Float64 mMinimum;
    Float64 mMaximum;
};
typedef struct AudioValueRange  AudioValueRange;


// AudioConverter.h
typedef struct OpaqueAudioConverter *   AudioConverterRef;
typedef UInt32                          AudioConverterPropertyID;

OSStatus AudioConverterNew(const AudioStreamBasicDescription *inSourceFormat,
                           const AudioStreamBasicDescription *inDestinationFormat,
                           AudioConverterRef *outAudioConverter);
OSStatus AudioConverterDispose(AudioConverterRef inAudioConverter);
typedef OSStatus (*AudioConverterComplexInputDataProc)(
    AudioConverterRef inAudioConverter,
    UInt32 *ioNumberDataPackets,
    AudioBufferList *ioData,
    AudioStreamPacketDescription **outDataPacketDescription,
    void *inUserData);
extern OSStatus AudioConverterFillComplexBuffer(
    AudioConverterRef inAudioConverter,
    AudioConverterComplexInputDataProc inInputDataProc,
    void *inInputDataProcUserData,
    UInt32 *ioOutputDataPacketSize,
    AudioBufferList *outOutputData,
    AudioStreamPacketDescription *outPacketDescription);
extern OSStatus AudioConverterSetProperty(
    AudioConverterRef inAudioConverter,
    AudioConverterPropertyID inPropertyID,
    UInt32 inPropertyDataSize,
    const void *inPropertyData);
extern OSStatus AudioConverterGetProperty(
    AudioConverterRef inAudioConverter,
    AudioConverterPropertyID inPropertyID,
    UInt32 *ioPropertyDataSize,
    void *outPropertyData);
