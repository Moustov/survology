import argparse
import json
import os
import queue
import sys
import threading
import time
import tkinter
from datetime import datetime
from functools import partial
from tkinter import Label, Button, Frame, LabelFrame, Tk, Entry, StringVar
from tkinter.constants import *
from tkinter.ttk import Progressbar

import numpy
# https://python-sounddevice.readthedocs.io/en/0.4.5/examples.html
# https://gist.github.com/HudsonHuang/fbdf8e9af7993fe2a91620d3fb86a182
# https://github.com/spatialaudio/python-sounddevice/issues/97
import sounddevice as sd
import soundfile as sf
# punctuation: https://github.com/benob/recasepunc
# models : https://alphacephei.com/vosk/models
from vosk import Model, KaldiRecognizer

from components.labelable_text_area import LabelableTextArea
from components.labelable_text_area_listener import LabelableTextAreaListener
from components.transcription_store import TranscriptionStore
from components.transcription_treeview import TranscriptionTreeview


class LiveTranscript(tkinter.Tk, LabelableTextAreaListener):
    def __init__(self):
        super().__init__()
        self.transcription_name = None
        self.file_name_entry = None
        self.close_row = True
        self.current_rowID = None
        self.labelable_content_labelframe = None
        self.labelable_widget = None
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
        self.transcription_treeview = None
        self.save_button = None
        self.title_label = None
        self.transcript_button = None
        self.transcription_text = None
        self.listen_button = None
        self.progress_bar = None
        self.queue = queue.Queue()
        self.file_name_entryvar = StringVar(value="transcription_" + str(datetime.now()))
        self.transcription_store = TranscriptionStore(self.file_name_entryvar.get())

    def get_ui_frame(self, root: tkinter.Tk) -> Frame:
        self.frame = Frame(root)
        self.title_label = Label(self.frame, text="Live Transcription")
        self.title_label.pack(padx=5, pady=5)
        self.listen_button = Button(self.frame, text='Listen', command=self._do_listen)
        self.listen_button.pack(padx=5, pady=5)
        #
        self.progress_bar = Progressbar(self.frame, orient='horizontal', mode='indeterminate', length=280)
        self.progress_bar.pack(padx=5, pady=5)
        #
        self.transcription_content_labelframe = self.get_transcription_frame(self.frame)
        self.transcription_content_labelframe.pack(padx=5, pady=5)
        #
        self.labelable_widget = LabelableTextArea(self.frame, self)
        self.labelable_content_labelframe = self.labelable_widget.get_ui_content(self.frame)
        self.labelable_content_labelframe.pack(fill=BOTH, expand=1)
        #
        self.file_name_entry = Entry(self.frame, textvariable=self.file_name_entryvar)
        self.file_name_entry.pack(padx=5, pady=5)

        self.save_button = Button(self.frame, text='Stop & Save transcription', command=self._do_stop_transcription)
        self.save_button.pack(padx=5, pady=5)
        return self.frame

    def get_transcription_frame(self, frame: Frame) -> LabelFrame:
        self.transcription_content_widget = TranscriptionTreeview(frame)
        self.transcription_content_labelframe = self.transcription_content_widget.get_ui_content(frame)
        self.transcription_treeview = self.transcription_content_widget.transcription_treeview
        self.transcription_treeview.bind("<ButtonRelease-1>", self._on_transcription_select_row)
        return self.transcription_content_labelframe

    def _do_stop_transcription(self):
        self.capturing = False

    def _save_transcription(self):
        self.transcription_name = self.file_name_entryvar.get()
        self.transcription_store.transcription_name = self.transcription_name
        transcription = self.transcription_treeview.get_data()
        transcription_content = {"transcription": transcription, "parts_colors": {},
                                 "transcription_labels": {}, "labels": {}}
        self.transcription_store.set_transcription_data(transcription_content["transcription"])
        self.transcription_store.set_transcription_labels_data(transcription_content["transcription_labels"])
        self.transcription_store.set_labels_data(transcription_content["labels"])
        self.transcription_store.save()
        # save WAV (temp file)
        print("saving:", f"{self.transcription_store.get_audio_file_name()}.WAV", 'x',
              self.samplerate, sf.default_subtype("WAV"))
        with sf.SoundFile(f"{self.transcription_store.get_audio_file_name()}.WAV", mode='x', samplerate=self.samplerate,
                          channels=self.NUMBER_CHANNELS, subtype="PCM_16") as file:
            file.write(self.whole_record)
        # transform into MP3
        data, fs = sf.read(f"{self.transcription_store.get_audio_file_name()}.WAV")
        sf.write(self.transcription_store.get_audio_file_name(), data, fs)
        # remove temp file
        os.remove(f"{self.transcription_store.get_audio_file_name()}.WAV")

    def _on_transcription_select_row(self, event):
        tree = event.widget
        print("_on_update_widgets_from_selected_transcription_row", event)
        row = [tree.item(item)["values"] for item in tree.selection()]
        if row:
            self.transcription_treeview.rowID = tree.selection()[0]
            print("self.transcription_labels", "'", self.transcription_treeview.rowID, "'",
                  self.transcription_store.json_transcription_labels)
            transcription = row[0][1]
            print("****", transcription)
            if self.transcription_treeview.rowID in self.transcription_store.json_transcription_labels.keys():
                self.labelable_widget.set_text(transcription,
                                               self.transcription_store.json_transcription_labels[self.transcription_treeview.rowID],
                                               self.transcription_store.json_labels)
            else:
                self.labelable_widget.set_text(transcription, {}, self.transcription_store.json_labels)

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
                            self.update_transcription_thread((str(formatted_timecode), txt['text'], ""))
                            self.close_row = True
                    else:
                        partial_result = json.loads(rec.PartialResult())
                        if partial_result["partial"] == "":
                            chrono = datetime.now()
                            timecode_sec = (chrono - start_time).seconds
                        print(formatted_timecode,
                              str(time.strftime("%H:%M:%S", time.gmtime(timecode_sec))),
                              partial_result)
                        if self.close_row:
                            self.add_transcription_thread((str(time.strftime("%H:%M:%S",
                                                                             time.gmtime(
                                                                                 timecode_sec))),
                                                           partial_result["partial"],
                                                           ""))
                            self.close_row = False
                        else:
                            self.update_transcription_thread((str(time.strftime("%H:%M:%S",
                                                                                time.gmtime(
                                                                                    timecode_sec))),
                                                              partial_result["partial"],
                                                              ""))
        #
        except KeyboardInterrupt:
            print("\nDone")
            parser.exit(0)
        except Exception as e:
            print(type(e).__name__ + ": " + str(e))
            parser.exit(1)
        self.progress_bar.stop()
        self._save_transcription()

    def add_transcription_thread(self, values: tuple):
        listen_thread = threading.Thread(target=partial(self._do_add_transcription, values),
                                         name="_do_add_transcription")
        listen_thread.start()

    def _do_add_transcription(self, values: tuple):
        index = self.transcription_treeview.insert(parent="", index='end', text="", values=values)
        print("row added", index, values)
        self.current_rowID = index
        self.transcription_treeview.see(self.current_rowID)  # ensure new line is visible
        self.transcription_treeview.selection_set(self.current_rowID)
        Tk.update(self.frame)

    def update_transcription_thread(self, values: tuple):
        listen_thread = threading.Thread(target=partial(self._do_update_transcription, values),
                                         name="_do_update_transcription")
        listen_thread.start()

    def _do_update_transcription(self, values: tuple):
        print("updating row", self.current_rowID, values)
        if self.current_rowID:
            self.transcription_treeview.item(self.current_rowID, text="", values=values)
        else:
            self._do_add_transcription(values)
        print("row updated", self.current_rowID, values)
        Tk.update(self.frame)


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text
