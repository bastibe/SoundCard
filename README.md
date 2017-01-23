# Python-Audio

Python-Audio is a library for playing and recording audio without resorting to a CPython extension. Instead, it is implemented using the wonderful [CFFI](http://cffi.readthedocs.io/en/latest/) and the native audio libraries of Linux, Windows and macOS.

Python-Audio is meant to be cross-platform, but as of this moment, only a Linux/pulseaudio and the Mac/coreaudio version has been implemented. Work has begun on the Windows/wasapi version, but it is not in a usable state yet.

## Tutorial

Here is how you get to your Speakers and Microphones:

```python
import pythonaudio as pa

speakers = pa.all_speakers()
default_speaker = pa.default_speaker()
mics = pa.all_microphones()
default_mic = pa.default_microphone()
# search by substring:
one_speaker = pa.get_speaker('Scarlett')
one_mic = pa.get_mic('Scarlett')
# fuzzy-search:
one_speker = pa.get_speaker('FS2i2')
one_mic = pa.get_microphone('FS2i2')
```

All of these functions return `Speaker` and `Microphone` objects, which can be used for playback and recording. All data passed in and out of these objects are *frames × channels* Numpy arrays.

```python
import numpy

print(default_speaker)
>>> <Speaker alsa_output.usb-Focuswrite_Scarlett_2i2_USB-00-USB.analog-stereo (2 channels)>
print(default_mic)
>>> <Microphone alsa_input.usb-Focuswrite_Scarlett_2i2_USB-00-USB.analog-stereo (2 channels)>

# record and play back one second of audio:
data = default_mic.record(samplerate=44100, length=44100)
default_speaker.play(data/numpy.max(data), samplerate=44100)

# alternatively, get a `recorder` and `player` object and play or record continuously:
with default_microphone.recorder(samplerate=44100) as mic, default_speaker.player(samplerate=44100) as sp:
    for _ in range(100):
        data = mic.record(length=1024)
        sp.play(data)
```

Due to some idiosyncracies of Linux/pulseaudio, `record` will not always return the exact number of samples that were asked. Similarly, while it is possible to specify a block size, Linux/pulseaudio will only honor it approximately.

Due to some limitations of Mac/coreaudio, you can not change the samplerate of `record` on a Mac. This will be solved by manually resampling either using coreaudio, or within this library.
