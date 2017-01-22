import sys

if sys.platform == 'linux':
    from pythonaudio.pulseaudio import *
elif sys.platform == 'darwin':
    from pythonaudio.coreaudio import *
elif sys.platform == 'win32':
    from pythonaudio.mediafoundation import *
else:
    raise NotImplementedError('Python-Audio does not support {} yet'.format(sys.platform))
