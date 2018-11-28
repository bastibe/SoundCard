.. SoundCard documentation master file, created by
   sphinx-quickstart on Tue Nov 27 16:22:51 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. include:: ../README.rst

.. default-role::

API Documentation
=================

The following functions are your entry point to the SoundCard library.
All of them return instances of :class:`soundcard._Speaker` or
:class:`soundcard._Microphone`. These are lightweight objects that
reference a sound card, but don't do any actual work.

Since audio hardware can change frequently when new audio devices are
plugged in or out, it is a good idea to always retrieve new instances
of :class:`soundcard._Speaker` and :class:`soundcard._Microphone`
instead of keeping old references around for a long time.

.. automodule:: soundcard
   :imported-members:
   :members:
   :undoc-members:

Sound Card Handles
------------------

The following classes are lightweight references to sound cards. They
are not meant to be constructed by hand, but are returned by
:func:`default_speaker`, :func:`get_speaker`, :func:`all_speakers`,
:func:`default_microphone`, :func:`get_microphone`,
:func:`all_microphones`.

The real work of interfacing with the hardware and playing or
recording audio is delegated to the :class:`_Player` and
:class:`_Recorder` objects, which are created by
:func:`_Speaker.play`, :func:`_Speaker.player`,
:func:`_Microphone.record`, and :func:`_Microphone.recorder`.

.. autoclass:: soundcard._Speaker
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: soundcard._Microphone
   :members:
   :inherited-members:
   :undoc-members:

Sound Streams
-------------

The following classes are the context managers that do the heavy
lifting of interacting with the backend drivers and sound cards. They
are not meant to be constructed by hand, but are returned by
:func:`_Speaker.player`, and :func:`_Microphone.recorder`.

.. autoclass:: soundcard._Player
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: soundcard._Recorder
   :members:
   :inherited-members:
   :undoc-members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
