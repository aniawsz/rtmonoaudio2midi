import time
import itertools
from collections import deque

import numpy as np
from pyaudio import PyAudio, paContinue, paInt16

from app_setup import (
    RING_BUFFER_SIZE,
    SAMPLE_RATE,
    THRESHOLD_MULTIPLIER,
    THRESHOLD_WINDOW_SIZE,
    WINDOW_SIZE)
from midi import hz_to_midi, RTNote
from mingus.midi import fluidsynth
from app_setup import SOUNDFONT


class SpectralAnalyser(object):

    # guitar frequency range
    FREQUENCY_RANGE = (80, 1200)

    def __init__(self, window_size, segments_buf=None):
        self._window_size = window_size
        if segments_buf is None:
            segments_buf = int(SAMPLE_RATE / window_size)
        self._segments_buf = segments_buf

        self._thresholding_window_size = THRESHOLD_WINDOW_SIZE
        assert self._thresholding_window_size <= segments_buf

        self._last_spectrum = np.zeros(window_size, dtype=np.int16)
        self._last_flux = deque(
            np.zeros(segments_buf, dtype=np.int16), segments_buf)
        self._last_prunned_flux = 0

        self._hanning_window = np.hanning(window_size)
        # The zeros which will be used to double each segment size
        self._inner_pad = np.zeros(window_size)

        # To ignore the first peak just after starting the application
        self._first_peak = True

    def _get_flux_for_thresholding(self):
        return list(itertools.islice(
            self._last_flux,
            self._segments_buf - self._thresholding_window_size,
            self._segments_buf))

    def find_onset(self, spectrum):
        """
        Calculates the difference between the current and last spectrum,
        then applies a thresholding function and checks if a peak occurred.
        """
        last_spectrum = self._last_spectrum
        flux = sum([max(spectrum[n] - last_spectrum[n], 0)
            for n in xrange(self._window_size)])
        self._last_flux.append(flux)

        thresholded = np.mean(
            self._get_flux_for_thresholding()) * THRESHOLD_MULTIPLIER
        prunned = flux - thresholded if thresholded <= flux else 0
        peak = prunned if prunned > self._last_prunned_flux else 0
        self._last_prunned_flux  = prunned
        return peak

    def find_fundamental_freq(self, samples):
        cepstrum = self.cepstrum(samples)
        # search for maximum between 0.08ms (=1200Hz) and 12.5ms (=80Hz)
        # as it's about the recorder's frequency range of one octave
        min_freq, max_freq = self.FREQUENCY_RANGE
        start = int(SAMPLE_RATE / max_freq)
        end = int(SAMPLE_RATE / min_freq)
        narrowed_cepstrum = cepstrum[start:end]

        peak_ix = narrowed_cepstrum.argmax()
        freq0 = SAMPLE_RATE / (start + peak_ix)

        if freq0 < min_freq or freq0 > max_freq:
            # Ignore the note out of the desired frequency range
            return

        return freq0

    def process_data(self, data):
        spectrum = self.autopower_spectrum(data)

        onset = self.find_onset(spectrum)
        self._last_spectrum = spectrum

        if self._first_peak:
            self._first_peak = False
            return

        if onset:
            freq0 = self.find_fundamental_freq(data)
            return freq0

    def autopower_spectrum(self, samples):
        """
        Calculates a power spectrum of the given data using the Hamming window.
        """
        # TODO: check the length of given samples; treat differently if not
        # equal to the window size

        windowed = samples * self._hanning_window
        # Add 0s to double the length of the data
        padded = np.append(windowed, self._inner_pad)
        # Take the Fourier Transform and scale by the number of samples
        spectrum = np.fft.fft(padded) / self._window_size
        autopower = np.abs(spectrum * np.conj(spectrum))
        return autopower[:self._window_size]

    def cepstrum(self, samples):
        """
        Calculates the complex cepstrum of a real sequence.
        """
        spectrum = np.fft.fft(samples)
        log_spectrum = np.log(np.abs(spectrum))
        cepstrum = np.fft.ifft(log_spectrum).real
        return cepstrum


class StreamProcessor(object):

    FREQS_BUF_SIZE = 11

    def __init__(self):
        self._spectral_analyser = SpectralAnalyser(
            window_size=WINDOW_SIZE,
            segments_buf=RING_BUFFER_SIZE)
        fluidsynth.init(SOUNDFONT)

    def run(self):
        pya = PyAudio()
        self._stream = pya.open(
            format=paInt16,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=WINDOW_SIZE,
            stream_callback=self._process_frame,
        )
        self._stream.start_stream()

        while self._stream.is_active() and not raw_input():
            time.sleep(0.1)

        self._stream.stop_stream()
        self._stream.close()
        pya.terminate()

    def _process_frame(self, data, frame_count, time_info, status_flag):
        data_array = np.fromstring(data, dtype=np.int16)
        freq0 = self._spectral_analyser.process_data(data_array)
        if freq0:
            # Onset detected
            print("Note detected; fundamental frequency: ", freq0)
            midi_note_value = int(hz_to_midi(freq0)[0])
            print("Midi note value: ", midi_note_value)
            fluidsynth.play_Note(midi_note_value,0,100)
        return (data, paContinue)


if __name__ == '__main__':
    stream_proc = StreamProcessor()
    stream_proc.run()
