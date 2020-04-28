import sys
import soundcard
import numpy
import pytest

skip_if_not_linux = pytest.mark.skipif(sys.platform != 'linux', reason='Only implemented for PulseAudio so far')

ones = numpy.ones(1024)
signal = numpy.concatenate([[ones], [-ones]]).T

def test_speakers():
    for speaker in soundcard.all_speakers():
        assert isinstance(speaker.name, str)
        assert hasattr(speaker, 'id')
        assert isinstance(speaker.channels, int)
        assert speaker.channels > 0

def test_microphones():
    for microphone in soundcard.all_microphones():
        assert isinstance(microphone.name, str)
        assert hasattr(microphone, 'id')
        assert isinstance(microphone.channels, int)
        assert microphone.channels > 0

def test_default_playback():
    soundcard.default_speaker().play(signal, 44100, channels=2)

def test_default_record():
    recording = soundcard.default_microphone().record(1024, 44100)
    assert len(recording == 1024)

def test_default_blockless_record():
    recording = soundcard.default_microphone().record(None, 44100)

@skip_if_not_linux
def test_name():
    # The default is the application name, so when run from pytest,
    # it’s “pytest” or “_jb_pytest_runner.py” or so.
    assert 'pytest' in soundcard.get_name()
    soundcard.set_name('testapp')
    assert soundcard.get_name() == 'testapp'

@skip_if_not_linux
@pytest.mark.parametrize("argv,progname", [
    (["./script.py"], "script.py"),  # chmod +x script.py; ./script.py
    (["path/to/script.py"], "script.py"),  # python path/to/script.py or
                                           # python -m path.to.script
    (["module/__main__.py"], "module"),  # python -m module
    (["-m", "module.submodule"], "module.submodule"),  # rare unresolved case
    (["-c", "import soundcard; soundcard.foo()"], "import soundcard; soundcard.fo..."),
])
def test_infer_name(monkeypatch, argv, progname):
    infer = soundcard.pulseaudio._PulseAudio._infer_program_name
    monkeypatch.setattr(sys, "argv", argv)
    assert infer() == progname

@pytest.fixture
def loopback_speaker():
    import sys
    if sys.platform == 'win32':
        # must install https://www.vb-audio.com/Cable/index.htm
        return soundcard.get_speaker('Cable')
    elif sys.platform == 'darwin':
        # must install soundflower
        return soundcard.get_speaker('Soundflower64')
    elif sys.platform == 'linux':
        # pacmd load-module module-null-sink channels=6 rate=48000
        return soundcard.get_speaker('Null')
    else:
        raise RuntimeError('Unknown platform {}'.format(sys.platform))

@pytest.fixture
def loopback_player(loopback_speaker):
    with loopback_speaker.player(48000, channels=2, blocksize=512) as player:
        yield player

@pytest.fixture
def loopback_microphone():
    if sys.platform == 'win32':
        # must install https://www.vb-audio.com/Cable/index.htm
        return soundcard.get_microphone('Cable')
    elif sys.platform == 'darwin':
        # must install soundflower
        return soundcard.get_microphone('Soundflower64')
    elif sys.platform == 'linux':
        return soundcard.get_microphone('Null', include_loopback=True)
    else:
        raise RuntimeError('Unknown platform {}'.format(sys.platform))

@pytest.fixture
def loopback_recorder(loopback_microphone):
    with loopback_microphone.recorder(48000, channels=2, blocksize=512) as recorder:
        yield recorder

def test_loopback_playback(loopback_player, loopback_recorder):
    loopback_player.play(signal)
    recording = loopback_recorder.record(1024*10)
    assert recording.shape[1] == 2
    left, right = recording.T
    assert left.mean() > 0
    assert right.mean() < 0
    assert (left > 0.5).sum() == len(signal)
    assert (right < -0.5).sum() == len(signal)

def test_loopback_reverse_recorder_channelmap(loopback_player, loopback_microphone):
    with loopback_microphone.recorder(48000, channels=[1, 0], blocksize=512) as loopback_recorder:
        loopback_player.play(signal)
        recording = loopback_recorder.record(1024*12)
    assert recording.shape[1] == 2
    left, right = recording.T
    assert right.mean() > 0
    assert left.mean() < 0
    assert (right > 0.5).sum() == len(signal)
    assert (left < -0.5).sum() == len(signal)

def test_loopback_reverse_player_channelmap(loopback_speaker, loopback_recorder):
    with loopback_speaker.player(48000, channels=[1, 0], blocksize=512) as loopback_player:
        loopback_player.play(signal)
        recording = loopback_recorder.record(1024*12)
    assert recording.shape[1] == 2
    left, right = recording.T
    assert right.mean() > 0
    assert left.mean() < 0
    assert (right > 0.5).sum() == len(signal)
    assert (left < -0.5).sum() == len(signal)

def test_loopback_mono_player_channelmap(loopback_speaker, loopback_recorder):
    with loopback_speaker.player(48000, channels=[0], blocksize=512) as loopback_player:
        loopback_player.play(signal[:,0])
        recording = loopback_recorder.record(1024*12)
    assert recording.shape[1] == 2
    left, right = recording.T
    assert left.mean() > 0
    if sys.platform == 'linux':
        # unmapped channels on linux are filled with the mean of other channels
        assert right.mean() < left.mean()
    else:
        assert abs(right.mean()) < 0.01 # something like zero
    assert (left > 0.5).sum() == len(signal)

def test_loopback_mono_recorder_channelmap(loopback_player, loopback_microphone):
    with loopback_microphone.recorder(48000, channels=[0], blocksize=512) as loopback_recorder:
        loopback_player.play(signal)
        recording = loopback_recorder.record(1024*12)
    assert len(recording.shape) == 1 or recording.shape[1] == 1
    assert recording.mean() > 0
    assert (recording > 0.5).sum() == len(signal)

def test_loopback_multichannel_channelmap(loopback_speaker, loopback_microphone):
    with loopback_speaker.player(48000, channels=[2, 0], blocksize=512) as loopback_player:
        with loopback_microphone.recorder(48000, channels=[2, 0], blocksize=512) as loopback_recorder:
            loopback_player.play(signal)
            recording = loopback_recorder.record(1024*12)
    assert len(recording.shape) == 2
    left, right = recording.T
    assert left.mean() > 0
    assert right.mean() < 0
    assert (left > 0.5).sum() == len(signal)
    assert (right < -0.5).sum() == len(signal)
