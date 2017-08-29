import sys

if sys.platform == 'linux':
    from soundcard.pulseaudio import *
elif sys.platform == 'darwin':
    from soundcard.coreaudio import *
elif sys.platform == 'win32':
    from soundcard.mediafoundation import *
else:
    raise NotImplementedError('SoundCard does not support {} yet'.format(sys.platform))
