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

kAudioEndPointInputChannelsKey = "channels-in"
kAudioEndPointOutputChannelsKey = "channels-out"

kAudioQueueProperty_IsRunning = int.from_bytes(b'aqrn', byteorder='big') # value is UInt32

kAudioQueueDeviceProperty_SampleRate = int.from_bytes(b'aqsr', byteorder='big') # value is Float64
kAudioQueueDeviceProperty_NumberChannels = int.from_bytes(b'aqdc', byteorder='big') # value is UInt32
kAudioQueueProperty_CurrentDevice = int.from_bytes(b'aqcd', byteorder='big') # value is CFStringRef

kAudioQueueProperty_MagicCookie = int.from_bytes(b'aqmc', byteorder='big') # value is void*
kAudioQueueProperty_MaximumOutputPacketSize = int.from_bytes(b'xops', byteorder='big') # value is UInt32
kAudioQueueProperty_StreamDescription = int.from_bytes(b'aqft', byteorder='big') # value is AudioStreamBasicDescription

kCFStringEncodingUTF8 = 0x08000100
kAudioObjectPropertyElementMaster = 0


kAudioUnitType_Output = int.from_bytes(b'auou', byteorder='big')
kAudioUnitManufacturer_Apple = int.from_bytes(b'appl', byteorder='big')
kAudioUnitSubType_GenericOutput	= int.from_bytes(b'genr', byteorder='big')
kAudioUnitSubType_HALOutput = int.from_bytes(b'ahal', byteorder='big')
# The audio unit can do input from the device as well as output to the
# device. Bus 0 is used for the output side, bus 1 is used to get audio
# input from the device.
outputbus = 0
inputbus = 1

kAudioUnitErr_InvalidProperty	       = -10879
kAudioUnitErr_InvalidParameter	       = -10878
kAudioUnitErr_InvalidElement	       = -10877
kAudioUnitErr_NoConnection	       = -10876
kAudioUnitErr_FailedInitialization     = -10875
kAudioUnitErr_TooManyFramesToProcess   = -10874
kAudioUnitErr_InvalidFile	       = -10871
kAudioUnitErr_UnknownFileType	       = -10870
kAudioUnitErr_FileNotSpecified	       = -10869
kAudioUnitErr_FormatNotSupported       = -10868
kAudioUnitErr_Uninitialized	       = -10867
kAudioUnitErr_InvalidScope	       = -10866
kAudioUnitErr_PropertyNotWritable      = -10865
kAudioUnitErr_CannotDoInCurrentContext = -10863
kAudioUnitErr_InvalidPropertyValue     = -10851
kAudioUnitErr_PropertyNotInUse	       = -10850
kAudioUnitErr_Initialized	       = -10849
kAudioUnitErr_InvalidOfflineRender     = -10848
kAudioUnitErr_Unauthorized	       = -10847
kAudioComponentErr_InstanceInvalidated = -66749
kAudioUnitErr_RenderTimeout	       = -66745

kAudioUnitProperty_StreamFormat	       = 8

kAudioOutputUnitProperty_CurrentDevice = 2000
kAudioOutputUnitProperty_EnableIO = 2003

kAudioFormatLinearPCM = int.from_bytes(b'lpcm', byteorder='big')
kAudioFormatFlagIsFloat = 0x1

kAudioUnitProperty_StreamFormat = 8
kAudioUnitProperty_CPULoad = 6
kAudioUnitProperty_Latency = 12
kAudioUnitProperty_SupportedNumChannels = 13
kAudioUnitProperty_MaximumFramesPerSlice = 14
kAudioUnitProperty_LastRenderError = 22
kAudioUnitProperty_SetRenderCallback = 23

kAudioUnitScope_Global = 0 # The context for audio unit characteristics that apply to the audio unit as a whole
kAudioUnitScope_Input = 1 # The context for audio data coming into an audio unit
kAudioUnitScope_Output = 2 # The context for audio data leaving an audio unit
