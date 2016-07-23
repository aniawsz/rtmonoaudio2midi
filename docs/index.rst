=====================================================
Welcome to RealTime mono audio to MIDI documentation!
=====================================================

The main objective of this project is to correctly identify musical notes and
play them through a MIDI synthetizer.


How to use
==========

The repository has the following modules:

 * :mod:`app_setup` where the different variables for the rest of the project
   can be specified

 * :mod:`audiostream` is the main file, executing this module will open the
   microphone, and start processing frames

 * :mod:`midi` contains several midi protocol related utilities

 * :mod:`synth` has a class to play notes.
