import json
import subprocess
import sys
import threading
import tkinter
from datetime import datetime
from tkinter import Text, Label, Button
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Progressbar

from vosk import Model, KaldiRecognizer, SetLogLevel


# punctuation: https://github.com/benob/recasepunc
# models : https://alphacephei.com/vosk/models


class AudioFileTranscript(tkinter.Tk):
    def __init__(self):
        self.SAMPLE_RATE = 16000
        self.title_label = None
        self.transcript_button = None
        self.transcription_text = None
        self.extract_button = None
        self.progress_bar = None
        self.file = None
        SetLogLevel(0)

    def display(self, root: tkinter.Tk):
        self.title_label = Label(root, text="File Transcription")
        self.title_label.pack()
        self.extract_button = Button(root, text='Extract from file', command=self._do_extract_text)
        self.extract_button.pack()

        self.progress_bar = Progressbar(root, orient='horizontal', mode='indeterminate', length=280)
        self.progress_bar.pack()

        self.transcription_text = Text(root)
        self.transcription_text.pack()

    def _do_extract_text(self):
        self.file = askopenfilename(title="Choose the file to open",
                               filetypes=[("WAV", ".wav"), ("MP3", ".mp3"), ("All files", ".*")])
        listen_thread = threading.Thread(target=self._transcript, name="_transcript")
        listen_thread.start()

    def _transcript(self):
        self.progress_bar.start()
        self.start_transcription(self.file)

    def start_transcription(self, file_path: str):
        model = Model(lang="fr")
        rec = KaldiRecognizer(model, self.SAMPLE_RATE)
        timecode = None
        print(self.file)
        with subprocess.Popen([r"C:\dev\survology\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg", "-loglevel", "quiet", "-i", file_path,
                               "-ar", str(self.SAMPLE_RATE), "-ac", "1", "-f", "s16le", "-"],
                              stdout=subprocess.PIPE) as process:
            while True:
                data = process.stdout.read(4000)
                if len(data) == 0:
                    break
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
