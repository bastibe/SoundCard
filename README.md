# Python-Audio

Python-Audio is a library for playing and recording audio without resorting to a CPython extension. Instead, it is implemented using the wonderful [CFFI](http://cffi.readthedocs.io/en/latest/) and the native audio libraries of Linux, Windows and macOS.

Python-Audio is cross-platform, and supports Linux/pulseaudio, Mac/coreaudio, and Windows/WASAPI. While the interface is identical across platforms, naming schemes and block sizes can vary between devices and platforms.

Python-Audio is still very early in its development. All major building blocks are in place, but I fully expect there to be bugs and possibly crashes. If you find a bug, please open an Issue, and I will try to fix it. Or open a Pull Request, and I will try to include your fix into Python-Audio.

However, please be aware that this is a hobby project of mine that I am developing for free, and in my spare time. While I try to be as accomodating as possible, I can not guarantee a timely response to issues. Publishing Open Source Software on Github does not imply an obligation to *fix your problem right now*. Please be civil.

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

* macOS/coreaudio currently does not record the first block correctly. The reason for this is still unknown.
* At the moment, linux/pulseaudio does not give human-readable soundcard names yet. This will be implemented in the future.


## License

Copyright (c) 2016 Bastian Bechtold
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the
   distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived
   from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
