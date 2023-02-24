import argparse
import json
import queue
import sys
import threading
import time
import tkinter
from datetime import datetime
from tkinter import Text, Label, Button
from tkinter.constants import NO, CENTER, W, END
from tkinter.ttk import Progressbar, Treeview

import sounddevice as sd
from vosk import Model, KaldiRecognizer


# punctuation: https://github.com/benob/recasepunc
# models : https://alphacephei.com/vosk/models


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

        self.sentences = Treeview(root)
        self.sentences['columns'] = ('Timecode', 'Text')
        self.sentences.column("#0", width=0, stretch=NO)
        self.sentences.column('Timecode', anchor=CENTER, width=60)
        self.sentences.column('Text', anchor=W, width=380)

        self.sentences.heading("#0", text="", anchor=CENTER)
        self.sentences.heading('Timecode', text="Timecode", anchor=CENTER)
        self.sentences.heading('Text', text="Text", anchor=CENTER)
        # http://tkinter.fdex.eu/doc/event.html#events
        self.sentences.bind("<ButtonRelease-1>", self._on_sentence_select)
        self.sentences.pack()

        self.transcription_text = Text(root, height=5)
        self.transcription_text.pack()

    def _on_sentence_select(self, event):
        item = self.sentences.item(self.sentences.selection())['values']
        self.transcription_text.delete('1.0', END)
        self.transcription_text.insert('end', f"{item[1]}")

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
                formatted_timecode = ""
                index = 0
                start_time = datetime.now()
                while True:
                    data = self.queue.get()
                    if rec.AcceptWaveform(data):
                        txt = json.loads(rec.Result())
                        if txt['text'] != "":
                            formatted_timecode = time.strftime("%H:%M:%S", time.gmtime(timecode_sec))
                            self.sentences.insert(parent="", index='end', iid=index, text="",
                                                  values=(str(formatted_timecode), txt['text']))
                            index += 1
                    else:
                        partial = json.loads(rec.PartialResult())
                        if partial["partial"] == "":
                            chrono = datetime.now()
                            timecode_sec = (chrono - start_time).seconds
                        print(formatted_timecode, partial)
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
