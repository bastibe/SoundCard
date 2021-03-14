SoundCard
=========

|version| |python| |status| |license|

|contributors| |downloads|

SoundCard is a library for playing and recording audio without resorting to a
CPython extension. Instead, it is implemented using the wonderful `CFFI
<http://cffi.readthedocs.io/en/latest/>`__ and the native audio libraries of
Linux, Windows and macOS.

SoundCard is cross-platform, and supports Linux/pulseaudio, Mac/coreaudio, and
Windows/WASAPI. While the programming interface is identical across platforms,
sound card naming schemes and default block sizes can vary between devices and
platforms.

SoundCard is still in development. All major features work on all platforms, but
there are a few known issues that still need to be fixed. If you find a bug,
please open an Issue, and I will try to fix it. Or open a Pull Request, and I
will try to include your fix into SoundCard.

However, please be aware that this is a hobby project of mine that I am
developing for free, and in my spare time. While I try to be as accomodating as
possible, I can not guarantee a timely response to issues. Publishing Open
Source Software on Github does not imply an obligation to *fix your problem
right now*. Please be civil.

| SoundCard is licensed under the terms of the BSD 3-clause license
| (c) 2016 Bastian Bechtold


|open-issues| |closed-issues| |open-prs| |closed-prs|

.. |status| image:: https://img.shields.io/pypi/status/soundcard.svg
.. |contributors| image:: https://img.shields.io/github/contributors/bastibe/soundcard.svg
.. |version| image:: https://img.shields.io/pypi/v/soundcard.svg
.. |python| image:: https://img.shields.io/pypi/pyversions/soundcard.svg
.. |license| image:: https://img.shields.io/github/license/bastibe/soundcard.svg
.. |downloads| image:: https://img.shields.io/pypi/dm/soundcard.svg
.. |open-issues| image:: https://img.shields.io/github/issues/bastibe/soundcard.svg
.. |closed-issues| image:: https://img.shields.io/github/issues-closed/bastibe/soundcard.svg
.. |open-prs| image:: https://img.shields.io/github/issues-pr/bastibe/soundcard.svg
.. |closed-prs| image:: https://img.shields.io/github/issues-pr-closed/bastibe/soundcard.svg

Tutorial
--------

Here is how you get to your Speakers and Microphones:

.. code:: python

    import soundcard as sc

    # get a list of all speakers:
    speakers = sc.all_speakers()
    # get the current default speaker on your system:
    default_speaker = sc.default_speaker()
    # get a list of all microphones:
    mics = sc.all_microphones()
    # get the current default microphone on your system:
    default_mic = sc.default_microphone()

    # search for a sound card by substring:
    >>> sc.get_speaker('Scarlett')
    <Speaker Focusrite Scarlett 2i2 (2 channels)>
    >>> one_mic = sc.get_microphone('Scarlett')
    <Microphone Focusrite Scalett 2i2 (2 channels)>
    # fuzzy-search to get the same results:
    one_speaker = sc.get_speaker('FS2i2')
    one_mic = sc.get_microphone('FS2i2')


All of these functions return ``Speaker`` and ``Microphone`` objects, which can
be used for playback and recording. All data passed in and out of these objects
are *frames × channels* Numpy arrays.

.. code:: python

    import numpy

    >>> print(default_speaker)
    <Speaker Focusrite Scarlett 2i2 (2 channels)>
    >>> print(default_mic)
    <Microphone Focusrite Scarlett 2i2 (2 channels)>

    # record and play back one second of audio:
    data = default_mic.record(samplerate=48000, numframes=48000)
    default_speaker.play(data/numpy.max(data), samplerate=48000)

    # alternatively, get a `Recorder` and `Player` object
    # and play or record continuously:
    with default_mic.recorder(samplerate=48000) as mic, \
          default_speaker.player(samplerate=48000) as sp:
        for _ in range(100):
            data = mic.record(numframes=1024)
            sp.play(data)

Latency
-------

By default, SoundCard records and plays at the operating system's default
configuration. Particularly on laptops, this configuration might have extreme
latencies, up to multiple seconds.

In order to request lower latencies, pass a ``blocksize`` to ``player`` or
``recorder``. This tells the operating system your desired latency, and it will
try to honor your request as best it can. On Windows/WASAPI, setting
``exclusive_mode=True`` might help, too (this is currently experimental).

Another source of latency is in the ``record`` function, which buffers output up
to the requested ``numframes``. In general, for optimal latency, you should use
a ``numframes`` significantly lower than the ``blocksize`` above, maybe by a
factor of two or four.

To get the audio data as quickly as absolutely possible, you can use
``numframes=None``, which will return whatever audio data is available right
now, without any buffering. Note that this might receive different numbers of
frames each time.

With the above settings, block sizes of 256 samples or ten milliseconds are
usually no problem. The total latency of playback and recording is dependent on
how these buffers are handled by the operating system, though, and might be
significantly higher.

Additionally, it might help to experiment with advice from here: https://askubuntu.com/questions/707171/how-can-i-fix-choppy-audio and edit your /etc/pulse/default.pa file to replace the line saying ::

    load-module module-udev-detect

with ::

    load-module module-udev-detect tsched=0

and then do not forget to restart pulseaudio with ::

    pulseaudio -k


Channel Maps
------------

Some professional sound cards have large numbers of channels. If you want to
record or play only a subset of those channels, you can specify a channel map.
For playback, a channel map of ``[0, 3, 4]`` will play three-channel audio data
on the physical channels one, four, and five. For recording, a channel map of
``[0, 3, 4]`` will return three-channel audio data recorded from the physical
channels one, four, and five.

In addition, pulseaudio/Linux defines channel ``-1`` as the mono mix of all
channels for both playback and recording. CoreAudio/macOS defines channel ``-1``
as silence for both playback and recording.

FAQ
---
Q: How to make it work on a headless Raspberry Pi?

A: PulseAudio is not installed by default on the Raspberry Pi OS Lite distribution (https://www.raspberrypi.org/software/operating-systems/). In order to use ``soundcard``, you have to install PulseAudio first, and edit the configuration (with a fix to avoid the main output to be in mono-only). ::

    sudo apt install -y python3-pip python3-numpy pulseaudio
    sudo nano /usr/share/pulseaudio/alsa-mixer/profile-sets/default.conf
    # comment the block [Mapping analog-mono] with ';'
    pulseaudio -D
    python3 -m pip install soundcard


Known Issues:
-------------

* Windows/WASAPI currently records garbage if you record only a single channel.
  The reason for this is yet unknown. Multi-channel and channel maps work,
  though.
* Windows/WASAPI silently ignores the blocksize in some cases. Apparently, it
  only supports variable block sizes in exclusive mode.
* Error messages often report some internal CFFI/backend errors. This will be
  improved in the future.

Changelog
---------

- 2018-04-25 implements fixed block sizes when recording
  (thank you, Pariente Manuel!)
- 2018-05-10 adds a test suite and various fixes for Windows
- 2018-05-11 various fixes for macOS
- 2018-06-27 Adds latency property to Linux/pulseaudio
  (Thank you, Pariente Manuel!)
- 2018-07-17 adds loopback support for Windows
  (Thank you, Jan Leskovec!)
- 2018-10-16 adds bug fix for IPython on Windows
  (Thank you, Sebastian Michel!)
- 2018-11-28 adds Sphinx/Readthedocs documentation
- 2019-03-25 adds support for Python 3.5
  (Thank you, Daniel R. Kumor!)
- 2019-04-29 adds experimental support for exclusive mode on Windows
- 2019-05-13 fixes sample rate conversion on macOS
- 2019-05-15 fixes silence recording on macOS
- 2019-06-11 fixes exception when monitoring default device on Linux
  (Thank you, Inti Pelupessy!)
- 2019-06-18 fixes crash when opening many streams on Linux
- 2019-08-23 fixes attribute error when accessing stream state on Linux
  (Thank you, Davíð Sindri Pétursson!)
- 2019-10-08 fixes inconsistent dtypes when recording on Linux
- 2020-01-06 fixes silent recordings on Windows
- 2020-04-28 get and set the pulseaudio program name on Linux
  (Thank you, Philipp A.!)
- 2020-05-14 fixes error with unicode soundcard names on Windows
  (Thank you, BAKEZQ!)
- 2020-05-18 adds support for pyinstaller (v4)
  (Thank you, Bob Thomas!)
- 2020-05-19 adds compatibility with Windows 7
  (Thank you, demberto!)
- 2020-07-22 fixes freezing bug on Linux during startup
  (Thank you, zhujisheng!)
- 2020-08-01 improves error reporting on Linux
  (Thank you, Rik van Riel!)
- 2020-08-13 fixes crash due to use-after-free on Linux
  (Thank you, Rik van Riel!)
- 2021-01-13 fixes unicode error on Windows
  (Thank you, paulzzh!)
