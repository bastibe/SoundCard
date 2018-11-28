import sys

if sys.platform == 'linux':
    from soundcard.pulseaudio import *

    # also load main classes if building documentation:
    if 'sphinx' in sys.modules:
        from soundcard.pulseaudio import _Speaker, _Microphone, _Player, _Recorder

elif sys.platform == 'darwin':
    from soundcard.coreaudio import *
elif sys.platform == 'win32':
    from soundcard.mediafoundation import *
else:
    raise NotImplementedError('SoundCard does not support {} yet'.format(sys.platform))
