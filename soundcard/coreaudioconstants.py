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

kAudioDevicePropertyNominalSampleRate = int.from_bytes(b'nsrt', byteorder='big')
kAudioDevicePropertyBufferFrameSize = int.from_bytes(b'fsiz', byteorder='big')
kAudioDevicePropertyBufferFrameSizeRange = int.from_bytes(b'fsz#', byteorder='big')
kAudioDevicePropertyUsesVariableBufferFrameSizes = int.from_bytes(b'vfsz', byteorder='big')
kAudioDevicePropertyStreamConfiguration = int.from_bytes(b'slay', byteorder='big')

kCFStringEncodingUTF8 = 0x08000100
kAudioObjectPropertyElementMaster = 0

kAudioUnitType_Output = int.from_bytes(b'auou', byteorder='big')
kAudioUnitManufacturer_Apple = int.from_bytes(b'appl', byteorder='big')
kAudioUnitSubType_GenericOutput = int.from_bytes(b'genr', byteorder='big')
kAudioUnitSubType_HALOutput = int.from_bytes(b'ahal', byteorder='big')
kAudioUnitSubType_DefaultOutput = int.from_bytes(b'def ', byteorder='big')
# The audio unit can do input from the device as well as output to the
# device. Bus 0 is used for the output side, bus 1 is used to get audio
# input from the device.
outputbus = 0
inputbus = 1

def error_number_to_string(num):
    if num == kAudioUnitErr_InvalidProperty:
        return "The property is not supported"
    elif num == kAudioUnitErr_InvalidParameter:
        return "The parameter is not supported"
    elif num == kAudioUnitErr_InvalidElement:
        return "The specified element is not valid"
    elif num == kAudioUnitErr_NoConnection:
        return "There is no connection (generally an audio unit is asked to render but it has" \
               " not input from which to gather data)"
    elif num == kAudioUnitErr_FailedInitialization:
        return "The audio unit is unable to be initialized"
    elif num == kAudioUnitErr_TooManyFramesToProcess:
        return "When an audio unit is initialized it has a value which specifies the max" \
               " number of frames it will be asked to render at any given time. If an audio" \
               " unit is asked to render more than this, this error is returned."
    elif num == kAudioUnitErr_InvalidFile:
        return "If an audio unit uses external files as a data source, this error is returned" \
               " if a file is invalid (Apple's DLS synth returns this error)"
    elif num == kAudioUnitErr_UnknownFileType:
        return "If an audio unit uses external files as a data source, this error is returned" \
               " if a file is invalid (Apple's DLS synth returns this error)"
    elif num == kAudioUnitErr_FileNotSpecified:
        return "If an audio unit uses external files as a data source, this error is returned" \
               " if a file hasn't been set on it (Apple's DLS synth returns this error)"
    elif num == kAudioUnitErr_FormatNotSupported:
        return "Returned if an input or output format is not supported"
    elif num == kAudioUnitErr_Uninitialized:
        return "Returned if an operation requires an audio unit to be initialized and it is not."
    elif num == kAudioUnitErr_InvalidScope:
        return "The specified scope is invalid"
    elif num == kAudioUnitErr_PropertyNotWritable:
        return "The property cannot be written"
    elif num == kAudioUnitErr_CannotDoInCurrentContext:
        return "Returned when an audio unit is in a state where it can't perform the requested" \
               " action now - but it could later. Its usually used to guard a render operation" \
               " when a reconfiguration of its internal state is being performed."
    elif num == kAudioUnitErr_InvalidPropertyValue:
        return "The property is valid, but the value of the property being provided is not"
    elif num == kAudioUnitErr_PropertyNotInUse:
        return "Returned when a property is valid, but it hasn't been set to a valid value at this time."
    elif num == kAudioUnitErr_Initialized:
        return "Indicates the operation cannot be performed because the audio unit is initialized."
    elif num == kAudioUnitErr_InvalidOfflineRender:
        return "Used to indicate that the offline render operation is invalid. For instance," \
               " when the audio unit needs to be pre-flighted, but it hasn't been."
    elif num == kAudioUnitErr_Unauthorized:
        return "Returned by either Open or Initialize, this error is used to indicate that the" \
               " audio unit is not authorised, that it cannot be used. A host can then present" \
               " a UI to notify the user the audio unit is not able to be used in its current state."
    elif num == kAudioComponentErr_InstanceInvalidated:
        return "the component instance's implementation is not available, most likely because the process" \
               " that published it is no longer running"
    else:
        return "error number {}".format(num)

kAudioUnitErr_InvalidProperty = -10879
kAudioUnitErr_InvalidParameter = -10878
kAudioUnitErr_InvalidElement = -10877
kAudioUnitErr_NoConnection = -10876
kAudioUnitErr_FailedInitialization = -10875
kAudioUnitErr_TooManyFramesToProcess = -10874
kAudioUnitErr_InvalidFile = -10871
kAudioUnitErr_UnknownFileType = -10870
kAudioUnitErr_FileNotSpecified = -10869
kAudioUnitErr_FormatNotSupported = -10868
kAudioUnitErr_Uninitialized = -10867
kAudioUnitErr_InvalidScope = -10866
kAudioUnitErr_PropertyNotWritable = -10865
kAudioUnitErr_CannotDoInCurrentContext = -10863
kAudioUnitErr_InvalidPropertyValue = -10851
kAudioUnitErr_PropertyNotInUse = -10850
kAudioUnitErr_Initialized = -10849
kAudioUnitErr_InvalidOfflineRender = -10848
kAudioUnitErr_Unauthorized = -10847
kAudioComponentErr_InstanceInvalidated = -66749
kAudioUnitErr_RenderTimeout = -66745

kAudioOutputUnitProperty_CurrentDevice = 2000
kAudioOutputUnitProperty_EnableIO = 2003 # scope output, element 0 == output,
kAudioOutputUnitProperty_HasIO = 2006    # scope input, element 1 == input
kAudioOutputUnitProperty_IsRunning = 2001
kAudioOutputUnitProperty_ChannelMap = 2002

kAudioFormatLinearPCM = int.from_bytes(b'lpcm', byteorder='big')
kAudioFormatFlagIsFloat = 0x1

kAudioUnitProperty_StreamFormat = 8
kAudioUnitProperty_CPULoad = 6
kAudioUnitProperty_Latency = 12
kAudioUnitProperty_SupportedNumChannels = 13
kAudioUnitProperty_MaximumFramesPerSlice = 14
kAudioUnitProperty_SetRenderCallback = 23
kAudioOutputUnitProperty_SetInputCallback = 2005
kAudioUnitProperty_StreamFormat = 8
kAudioUnitProperty_SampleRate = 2
kAudioUnitProperty_ContextName = 25
kAudioUnitProperty_ElementName = 30
kAudioUnitProperty_NickName = 54

kAudioUnitScope_Global = 0 # The context for audio unit characteristics that apply to the audio unit as a whole
kAudioUnitScope_Input = 1 # The context for audio data coming into an audio unit
kAudioUnitScope_Output = 2 # The context for audio data leaving an audio unit
