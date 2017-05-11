# Python-Audio

Python-Audio is a library for playing and recording audio without resorting to a CPython extension. Instead, it is implemented using the wonderful [CFFI](http://cffi.readthedocs.io/en/latest/) and the native audio libraries of Linux, Windows and macOS.

Python-Audio is cross-platform, and supports Linux/pulseaudio, Mac/coreaudio, and Windows/WASAPI. While the interface is identical across platforms, naming schemes and block sizes can vary between devices and platforms.

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
one_mic = pa.get_microphone('Scarlett')
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
with default_mic.recorder(samplerate=44100) as mic, default_speaker.player(samplerate=44100) as sp:
    for _ in range(100):
        data = mic.record(length=1024)
        sp.play(data)
```

## Known Issues:

* At the moment, you can not change the samplerate of `record` on macOS/coreaudio yet. This will be implemented in the future.
* At the moment, macOS/coreaudio does not support searching for a soundcard yet. This will be implemented in the future.
* At the moment, linux/pulseaudio does not give human-readable soundcard names yet. This will be implemented in the future.
