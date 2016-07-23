import time

import fluidsynth
import numpy as np

from app_setup import SAMPLE_RATE, SOUNDFONT, AUDIO_DRIVER


class FluidSynth(object):
    def play_note(self, note):
        fs = fluidsynth.Synth()
        fs.start(driver=AUDIO_DRIVER)

        sfid = fs.sfload(SOUNDFONT)
        fs.program_select(0, sfid, 0, 0)

        fs.noteon(0, note.value, note.velocity)
        time.sleep(note.duration)

        fs.noteoff(0, note.value)
        time.sleep(0.1)

        fs.delete()

    def get_audio_stream_for_note(self, note):
        """
        noteon -> channel, key, velocity
        """
        self.initialize()

        stream = []
        self.fs.noteon(0, note.value, note.velocity)
        # note duration is in sec
        stream = np.append(stream,
                           self.fs.get_samples(SAMPLE_RATE * note.duration))
        self.fs.noteoff(0, note.value)
        # 1 sec decay of the note
        stream = np.append(stream, self.fs.get_samples(SAMPLE_RATE * 1))

        self.finish()

        return fluidsynth.raw_audio_string(stream)


def test_playing():
    fs = fluidsynth.Synth()
    fs.start(driver=AUDIO_DRIVER)

    sfid = fs.sfload(SOUNDFONT)
    fs.program_select(0, sfid, 0, 0)

    fs.noteon(0, 60, 30)
    fs.noteon(0, 67, 30)
    fs.noteon(0, 76, 30)
    time.sleep(1.0)

    fs.noteoff(0, 60)
    fs.noteoff(0, 67)
    fs.noteoff(0, 76)
    time.sleep(1.0)

    fs.delete()


def test_returning_data():
    fs = fluidsynth.Synth()
    sfid = fs.sfload(SOUNDFONT)
    fs.program_select(0, sfid, 0, 0)

    fs.noteon(0, 60, 30)
    fs.noteon(0, 67, 30)
    fs.noteon(0, 76, 30)
    time.sleep(1.0)

    fs.noteoff(0, 60)
    fs.noteoff(0, 67)
    fs.noteoff(0, 76)
    time.sleep(1.0)

    samples = fs.get_samples(1024)
    fs.delete()
    return fluidsynth.raw_audio_string(samples)


if __name__ == '__main__':
    test_playing()
