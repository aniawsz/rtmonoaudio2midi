import numpy as np

from collections import namedtuple

from mido import Message, MetaMessage, MidiFile
from mido.midifiles import MidiTrack


Note = namedtuple('Note', ['value', 'velocity', 'position_in_sec', 'duration'])
RTNote = namedtuple('RTNote', ['value', 'velocity', 'duration'])


def hz_to_midi(frequencies):
    return 12 * (np.log2(np.atleast_1d(frequencies)) - np.log2(440.0)) + 69


def add_notes(track, notes, sec_per_tick):
    times_in_ticks = [n.position_in_sec / sec_per_tick for n in notes]
    for ix, note in enumerate(notes):
        time_delta_in_ticks = int(
            times_in_ticks[ix] - (times_in_ticks[ix-1] if ix > 0 else 0))
        track.append(
            Message(
                'note_on',
                note=note.value,
                velocity=note.velocity,
                time=max(time_delta_in_ticks - note.duration, 0)
            )
        )
        track.append(
            Message(
                'note_off',
                note=note.value,
                velocity=note.velocity,
                time=note.duration
            )
        )


def create_midi_file_with_notes(filename, notes, bpm):
    with MidiFile() as midifile:
        track = MidiTrack()
        midifile.tracks.append(track)

        track.append(Message('program_change', program=12, time=0))

        tempo = int((60.0 / bpm) * 1000000)
        track.append(MetaMessage('set_tempo', tempo=tempo))

        sec_per_tick = tempo / 1000000.0 / midifile.ticks_per_beat
        add_notes(track, notes, sec_per_tick)

        midifile.save('{}.mid'.format(filename))
