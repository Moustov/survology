import json
import threading
import tkinter
from datetime import datetime
from tkinter import Text, Label, Button
from tkinter.ttk import Progressbar

import argparse
import queue
import sys
import sounddevice as sd

# models : https://alphacephei.com/vosk/models

from vosk import Model, KaldiRecognizer


class LiveTranscript(tkinter.Tk):
    def __init__(self):
        self.title_label = None
        self.transcript_button = None
        self.transcription_text = None
        self.listen_button = None
        self.progress_bar = None
        self.queue = queue.Queue()

    def display(self, root: tkinter.Tk):
        self.title_label = Label(root, text="Live Transcription")
        self.title_label.pack()
        self.listen_button = Button(root, text='Listen', command=self._do_listen)
        self.listen_button.pack()

        self.progress_bar = Progressbar(root, orient='horizontal', mode='indeterminate', length=280)
        self.progress_bar.pack()

        self.transcription_text = Text(root)
        self.transcription_text.pack()

    def _do_listen(self):
        listen_thread = threading.Thread(target=self._transcript, name="_transcript")
        listen_thread.start()

    def _transcript(self):
        self.progress_bar.start()
        self.start_transcription()

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.queue.put(bytes(indata))

    def start_transcription(self):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument(
            "-l", "--list-devices", action="store_true",
            help="show list of audio devices and exit")
        args, remaining = parser.parse_known_args()
        if args.list_devices:
            print(sd.query_devices())
            parser.exit(0)
        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[parser])
        parser.add_argument(
            "-f", "--filename", type=str, metavar="FILENAME",
            help="audio file to store recording to")
        parser.add_argument(
            "-d", "--device", type=int_or_str,
            help="input device (numeric ID or substring)")
        parser.add_argument(
            "-r", "--samplerate", type=int, help="sampling rate")
        parser.add_argument(
            "-m", "--model", type=str, help="language model; e.g. en-us, fr, nl; default is en-us")
        args = parser.parse_args(remaining)

        try:
            if args.samplerate is None:
                device_info = sd.query_devices(args.device, "input")
                # soundfile expects an int, sounddevice provides a float:
                args.samplerate = int(device_info["default_samplerate"])

            if args.model is None:
                model = Model(lang="fr")
            else:
                model = Model(lang=args.model)

            if args.filename:
                dump_fn = open(args.filename, "wb")
            else:
                dump_fn = None

            with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000, device=args.device,
                                   dtype="int16", channels=1, callback=self.callback):
                print("#" * 80)
                print("Press Ctrl+C to stop the recording")
                print("#" * 80)

                rec = KaldiRecognizer(model, args.samplerate)
                partial = {}
                timecode = ""
                while True:
                    data = self.queue.get()
                    if rec.AcceptWaveform(data):
                        txt = json.loads(rec.Result())
                        if txt['text'] != "":
                            self.transcription_text.insert('end', f"{timecode}: {txt['text']}\n\n")
                    else:
                        partial = json.loads(rec.PartialResult())
                        if partial["partial"] == "":
                            chrono = datetime.now()
                            timecode = chrono.strftime("%H:%M:%S.%f")
                        print(timecode, partial)
                    if dump_fn is not None:
                        dump_fn.write(data)

        except KeyboardInterrupt:
            print("\nDone")
            parser.exit(0)
        except Exception as e:
            parser.exit(type(e).__name__ + ": " + str(e))


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


