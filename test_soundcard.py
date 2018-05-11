import sys
import soundcard
import numpy
import pytest

silence = numpy.zeros([1024, 2])
ones = numpy.ones(1024)

signal = numpy.concatenate([[ones], [-ones]]).T
priming_silence = numpy.zeros([48000//5, 2])

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

@pytest.fixture
def loopback_speaker():
    import sys
    if sys.platform == 'win32':
        # must install https://www.vb-audio.com/Cable/index.htm
        return soundcard.get_speaker('Cable')
    elif sys.platform == 'darwin':
        # must install soundflower
        return soundcard.get_speaker('Soundflower64')

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

@pytest.fixture
def loopback_recorder(loopback_microphone):
    with loopback_microphone.recorder(48000, channels=2, blocksize=512) as recorder:
        yield recorder

def test_loopback_playback(loopback_player, loopback_recorder):
    loopback_player.play(priming_silence)
    loopback_recorder.record(len(priming_silence))
    loopback_player.play(signal)
    loopback_player.play(silence)
    recording = loopback_recorder.record(1024*10)
    assert recording.shape[1] == 2
    left, right = recording.T
    assert left.mean() > 0
    assert right.mean() < 0
    assert (left > 0.5).sum() == len(signal)
    assert (right < -0.5).sum() == len(signal)

def test_loopback_reverse_recorder_channelmap(loopback_player, loopback_microphone):
    with loopback_microphone.recorder(48000, channels=[1, 0], blocksize=512) as loopback_recorder:
        loopback_player.play(priming_silence)
        loopback_recorder.record(len(priming_silence))
        loopback_player.play(signal)
        loopback_player.play(silence)
        recording = loopback_recorder.record(1024*12)
    assert recording.shape[1] == 2
    left, right = recording.T
    assert right.mean() > 0
    assert left.mean() < 0
    assert (right > 0.5).sum() == len(signal)
    assert (left < -0.5).sum() == len(signal)

def test_loopback_reverse_player_channelmap(loopback_speaker, loopback_recorder):
    with loopback_speaker.player(48000, channels=[1, 0], blocksize=512) as loopback_player:
        loopback_player.play(priming_silence)
        loopback_recorder.record(len(priming_silence))
        loopback_player.play(signal)
        loopback_player.play(silence)
        recording = loopback_recorder.record(1024*12)
    assert recording.shape[1] == 2
    left, right = recording.T
    assert right.mean() > 0
    assert left.mean() < 0
    assert (right > 0.5).sum() == len(signal)
    assert (left < -0.5).sum() == len(signal)

def test_loopback_mono_player_channelmap(loopback_speaker, loopback_recorder):
    with loopback_speaker.player(48000, channels=[0], blocksize=512) as loopback_player:
        loopback_player.play(priming_silence[:,0])
        loopback_recorder.record(len(priming_silence))
        loopback_player.play(signal[:,0])
        loopback_player.play(silence[:,0])
        recording = loopback_recorder.record(1024*12)
    assert recording.shape[1] == 2
    left, right = recording.T
    assert left.mean() > 0
    if sys.platform != 'darwin': # macOS plays mono on all channels
        assert abs(right.mean()) < 0.01 # something like zero
    assert (left > 0.5).sum() == len(signal)

def test_loopback_mono_recorder_channelmap(loopback_player, loopback_microphone):
    with loopback_microphone.recorder(48000, channels=[0], blocksize=512) as loopback_recorder:
        loopback_player.play(priming_silence)
        loopback_recorder.record(len(priming_silence))
        loopback_player.play(signal)
        loopback_player.play(silence)
        recording = loopback_recorder.record(1024*12)
    assert len(recording.shape) == 1 or recording.shape[1] == 1
    assert recording.mean() > 0
    assert (recording > 0.5).sum() == len(signal)

# TODO: test more complex channel maps
# out = soundcard.default_microphone().record(44100, 44100, [0, 1, 0])

if __name__ == '__main__':
    with loopback_microphone().recorder(48000, channels=2, blocksize=512) as loopback_recorder:
        with loopback_speaker().player(48000, channels=2, blocksize=512) as loopback_player:
            test_loopback_playback(loopback_player, loopback_recorder)
