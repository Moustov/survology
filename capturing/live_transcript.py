import os

import numpy
import argparse
import json
import queue
import sys
import threading
import time
import tkinter
from datetime import datetime
from tkinter import Text, Label, Button, Frame, LabelFrame, Scrollbar
from tkinter.constants import *
from tkinter.ttk import Progressbar

# https://python-sounddevice.readthedocs.io/en/0.4.5/examples.html
# https://gist.github.com/HudsonHuang/fbdf8e9af7993fe2a91620d3fb86a182
# https://github.com/spatialaudio/python-sounddevice/issues/97
import sounddevice as sd
import soundfile as sf
# punctuation: https://github.com/benob/recasepunc
# models : https://alphacephei.com/vosk/models
from vosk import Model, KaldiRecognizer

from widgets.transcription_treeview import TranscriptionTreeview


class LiveTranscript(tkinter.Tk):
    def __init__(self):
        self.transcription_content_widget = None
        self.horscrlbar = None
        self.verscrlbar = None
        self.transcription_content_labelframe = None
        self.NUMBER_CHANNELS = 1
        self.MIC_CHANNEL = 1  # sounddevice.query_devices() provides the ID for the microphone
        self.audio_file = None
        self.capturing = None
        self.samplerate = None
        self.whole_record = None
        self.file_name = None
        self.sentences = None
        self.save_button = None
        self.title_label = None
        self.transcript_button = None
        self.transcription_text = None
        self.listen_button = None
        self.progress_bar = None
        self.queue = queue.Queue()

    def display(self, root: tkinter.Tk, grid_row: int = 0, grid_col: int = 0):
        self.frame = Frame(root)
        self.frame.grid(row=grid_row, column=grid_col)
        self.title_label = Label(self.frame, text="Live Transcription")
        self.title_label.pack(padx=5, pady=5)
        self.listen_button = Button(self.frame, text='Listen', command=self._do_listen)
        self.listen_button.pack(padx=5, pady=5)
        #
        self.progress_bar = Progressbar(self.frame, orient='horizontal', mode='indeterminate', length=280)
        self.progress_bar.pack(padx=5, pady=5)
        #
        self.display_transcription_frame()
        #
        self.transcription_text = Text(self.frame, height=5)
        self.transcription_text.pack(padx=5, pady=5)
        #
        self.save_button = Button(self.frame, text='Stop & Save transcription', command=self._do_stop_transcription)
        self.save_button.pack(padx=5, pady=5)

    def display_transcription_frame(self):
        self.transcription_content_widget = TranscriptionTreeview(self.frame)
        self.transcription_content_labelframe = self.transcription_content_widget.get_frame_pack(fill=BOTH, expand=1)
        self.sentences = self.transcription_content_widget.transcription_tree
        # http://tkinter.fdex.eu/doc/event.html#events
        # https://stackoverflow.com/questions/32289175/list-of-all-tkinter-events
        self.sentences.bind("<ButtonRelease-1>", self._on_sentence_select)

    def _do_stop_transcription(self):
        self.capturing = False

    def _save_transcription(self):
        transcription = self.sentences.get_data()
        transcription_content = {"transcription": transcription, "parts_colors": {},
                                 "transcription_labels": {}, "labels": {}}
        if not self.file_name:
            self.file_name = "audio samples/" + str(datetime.now())
            self.file_name = self.file_name.replace(':', '-')
        with open(self.file_name + ".MP3.json", "w", encoding='utf-8') as file:
            json.dump(transcription_content, file, indent=4, ensure_ascii=False)
        # save WAV
        print("saving:", f"{self.file_name}.WAV", 'x', self.samplerate, sf.default_subtype("WAV"))
        with sf.SoundFile(f"{self.file_name}.WAV", mode='x', samplerate=self.samplerate,
                          channels=self.NUMBER_CHANNELS, subtype="PCM_16") as file:
            file.write(self.whole_record)
        # transform into MP3
        data, fs = sf.read(f"{self.file_name}.WAV")
        sf.write(f"{self.file_name}.MP3", data, fs)
        os.remove(f"{self.file_name}.WAV")

    def _on_sentence_select(self, event):
        item = self.sentences.item(self.sentences.selection())['values']
        self.transcription_text.delete('1.0', END)
        self.transcription_text.insert('end', f"{item[1]}")

    def _do_listen(self):
        listen_thread = threading.Thread(target=self._transcript, name="_transcript")
        listen_thread.start()

    def _transcript(self):
        self.progress_bar.start()
        self._start_transcription_thread()

    def _mic_consumer_callback(self, indata, frames, time_i, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.queue.put(bytes(indata))

    def _start_transcription_thread(self):
        timecode_sec = 0
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
        print(args)
        print("sf.default_subtype('WAV')", sf.default_subtype("WAV"))

        try:
            if args.samplerate is None:
                device_info = sd.query_devices(args.device, "input")
                # soundfile expects an int, sounddevice provides a float:
                self.samplerate = int(device_info["default_samplerate"])
            else:
                self.samplerate = args.samplerate
            print(sd.query_devices(args.device, "input"))
            if args.model is None:
                model = Model(lang="fr")
            else:
                model = Model(lang=args.model)
            self.whole_record = numpy.array([], numpy.int16)
            with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000, device=args.device,
                                   dtype="int16", channels=self.MIC_CHANNEL, callback=self._mic_consumer_callback):
                print("#" * 80)
                print("Press Ctrl+C to stop the recording")
                print("#" * 80)
                #
                rec = KaldiRecognizer(model, self.samplerate)
                formatted_timecode = ""
                index = 0
                start_time = datetime.now()
                #
                self.capturing = True
                while self.capturing:
                    data = self.queue.get()
                    self.whole_record = numpy.concatenate((self.whole_record, numpy.frombuffer(data, numpy.int16)))
                    if rec.AcceptWaveform(data):
                        txt = json.loads(rec.Result())
                        if txt['text'] != "":
                            formatted_timecode = time.strftime("%H:%M:%S", time.gmtime(timecode_sec))
                            row_id = self.sentences.insert(parent="", index='end', iid=index, text="",
                                                           values=(str(formatted_timecode), txt['text']))
                            self.sentences.see(index)   # ensure new line is visible
                            self.sentences.selection_set(row_id)
                            index += 1
                    else:
                        partial = json.loads(rec.PartialResult())
                        if partial["partial"] == "":
                            chrono = datetime.now()
                            timecode_sec = (chrono - start_time).seconds
                        print(formatted_timecode, partial)
        #
        except KeyboardInterrupt:
            print("\nDone")
            parser.exit(0)
        except Exception as e:
            parser.exit(type(e).__name__ + ": " + str(e))
        self.progress_bar.stop()
        self._save_transcription()


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text
