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
.. |status| image:: https://img.shields.io/pypi/status/soundcard.svg

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

Known Issues:
-------------

* Windows/WASAPI currently records garbage if you record only a single channel.
  The reason for this is yet unknown. Multi-channel and channel maps work,
  though.
* Windows/WASAPI silently ignores the blocksize. Apparently, it only supports
  variable block sizes in exclusive mode, which is not yet supported.
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
