import sys

if sys.platform == 'linux':
    from pulseaudio import *
else:
    raise NotImplementedError('Python-Audio does not support {} yet'.format(sys.platform))
