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
