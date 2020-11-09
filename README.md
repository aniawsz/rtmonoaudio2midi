# rtmonoaudio2midi
Real-time note recognition in monophonic audio stream

Please install all the dependencies from `requirements.txt` file by executing:
`pip install -r requirements.txt`

To run the app:
* Download a SoundFont file and update a path to it in the `app_setup.py` file
* Execute ` python audiostream.py`

Troubleshooting
I get an error about fluidsynth :
   ImportError: Couldn't find the FluidSynth library
   https://github.com/FluidSynth/fluidsynth/issues/657
