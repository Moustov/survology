import json
import subprocess
import threading
import time
import tkinter
from time import sleep
from tkinter import Label, Button, Frame
from tkinter.constants import *
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Progressbar, Treeview

import pygame
from vosk import Model, KaldiRecognizer, SetLogLevel


# punctuation: https://github.com/benob/recasepunc
# models : https://alphacephei.com/vosk/models


class AudioFileTranscript(tkinter.Tk):
    def __init__(self):
        self.text_index = 0
        self.debug = False
        self.SAMPLE_RATE = 16000
        self.title_label = None
        self.transcript_button = None
        self.transcription_tree = None
        self.extract_button = None
        self.pause_status = False
        self.position_label = None
        self.save_button = None
        self.pause_button = None
        self.stop_button = None
        self.progress_bar = None
        self.file_to_transcript = None
        self.reading_rate = 9.29063607924922
        SetLogLevel(0)
        self.sound = None
        pygame.mixer.init()

    def display(self, root: tkinter.Tk):
        self.frame = Frame(root)
        self.frame.pack()
        self.title_label = Label(self.frame, text="File Transcription")
        self.title_label.grid(row=0, column=0)
        self.extract_button = Button(self.frame, text='Extract from file', command=self._do_extract_text)
        self.extract_button.grid(row=0, column=1)
        # img = PhotoImage(file="img.png")
        # self.play_button = Button(root, image=img, borderwidth=0, command=self._do_play)
        # self.play_button = Button(root, text='|>', command=self._do_play)
        # # self.play_button.grid(row=3, column=0, padx=10)
        # self.play_button.pack()

        self.progress_bar = Progressbar(self.frame, orient='horizontal', mode='indeterminate', length=280)
        self.progress_bar.grid(row=1, column=0, columnspan=2)
        #
        self.transcription_tree = Treeview(self.frame)
        self.transcription_tree.grid(row=2, column=0, columnspan=2, sticky='nsew')
        self.transcription_tree['columns'] = ('chrono', 'Text', 'tags')
        self.transcription_tree.column("#0", width=0, stretch=NO)
        self.transcription_tree.column('chrono', anchor=CENTER, width=30)
        self.transcription_tree.column('Text', anchor=W, width=120)
        self.transcription_tree.column('tags', anchor=CENTER, width=0, stretch=NO)
        self.transcription_tree.heading("#0", text="", anchor=CENTER)
        self.transcription_tree.heading('chrono', text="chrono", anchor=CENTER)
        self.transcription_tree.heading('Text', text="Text", anchor=W)
        self.transcription_tree.heading('tags', text="tags", anchor=CENTER)
        self.transcription_tree.bind("<ButtonRelease-1>", self._do_text_select)
        #
        self.save_button = Button(self.frame, text='Save transcription', command=self._do_save_transcription)
        self.save_button.grid(row=3, column=0)

    def _do_save_transcription(self):
        transcription = {}
        for i in self.transcription_tree.get_children():
            print(self.transcription_tree.item(i)['values'])
            data = self.transcription_tree.item(i)['values']
            transcription[data[0]] = data[1]

        with open("transcription.json", "w", encoding='utf-8') as file:
            json.dump(transcription, file, indent=4, ensure_ascii=False)

    def _do_text_select(self,  event):
        item = self.transcription_tree.item(self.transcription_tree.selection())['values']
        if item and item[1]:
            pass

    def _do_play(self):
        try:
            self.sound.play(loops=0)
            self._play_time()
        except Exception as err:
            print(err)

    def _play_time(self):
        timecode_ms = pygame.mixer.music.get_pos() / 1000
        pos = time.strftime("%H:%M:%S", time.gmtime(timecode_ms))
        print(pos)
        self.position_label.config(text=pos)
        self.position_label.after(1000, self._play_time)

    def _do_pause(self):
        if self.pause_status:
            self.pause_status = False
            self.sound.pause()
        else:
            self.pause_status = True
            self.sound.unpause()

    def _do_stop(self):
        self.sound.stop()

    def _do_extract_text(self):
        self.file_to_transcript = askopenfilename(title="Choose the file to open",
                                                  filetypes=[("MP3", ".mp3"), ("WAV", ".wav"), ("All files", ".*")])
        listen_thread = threading.Thread(target=self._transcript, name="_transcript")
        listen_thread.start()

    def _transcript(self):
        self.progress_bar.start()
        for row in self.transcription_tree.get_children():
            self.transcription_tree.delete(row)
        self.start_transcription(self.file_to_transcript)

    @staticmethod
    def time_code_to_chrono(timecode: int) -> str:
        h = timecode // 3600
        m = timecode // 60
        s = timecode % 60
        return format(f"{str(h).zfill(2)}:{str(m).zfill(2)}:{str(s).zfill(2)}")

    def start_transcription(self, file_path: str):
        model = Model(lang="fr")
        rec = KaldiRecognizer(model, self.SAMPLE_RATE)
        timecode = None
        print(self.file_to_transcript)
        duration = self.get_media_duration(self.file_to_transcript)
        print("duration:", duration)
        start = 0
        time_limit = 2  # seconds
        carry_on = True
        self.text_index = 0
        while carry_on:
            # print("start", start)
            with subprocess.Popen(
                    [r"ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg", "-loglevel", "quiet",
                     "-t", str(time_limit),
                     "-ss", str(start),
                     # f"-force_key_frames expr:gte(t,n_forced*{time_limit})",
                     "-i", file_path, "-ar", str(self.SAMPLE_RATE), "-ac", "1", "-f", "s16le",
                     "-"], stdout=subprocess.PIPE) \
                    as process:
                while True:
                    data = process.stdout.read(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        txt = json.loads(rec.Result())
                        if txt['text'] != "":
                            self.transcription_tree.insert(parent="", index='end', iid=self.text_index, text="",
                                                           values=(self.time_code_to_chrono(timecode), txt['text']))
                            self.text_index += 1
                    else:
                        partial = json.loads(rec.PartialResult())
                        if partial["partial"] == "":
                            timecode = start
                        if self.debug:
                            print(timecode, partial)
                carry_on = start <= duration
                start += time_limit
        self.progress_bar.stop()

    def get_media_duration(self, file: str) -> float:
        mm_file = file.replace("'", "\'")
        cmd = rf'ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg -i "{mm_file}" 2>&1 ffmpeg.log'
        if self.debug:
            print("cmd", cmd)
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        if self.debug:
            print("output", process.stdout)
        for l in str(process.stdout).split("\\n"):
            if self.debug:
                print(">>", l)
            if l.strip().startswith("Duration:"):
                d = l.split(",")
                duration = d[0].split(":")
                res = int(duration[1].strip()) * 3600 + int(duration[2]) * 60 + float(duration[3])
                return res


def run_command(command) -> str:
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    # Read stdout from subprocess until the buffer is empty !
    for line in iter(p.stdout.readline, b''):
        if line:  # Don't print blank lines
            print(line)
            yield str(line)
    # This ensures the process has completed, AND sets the 'returncode' attr
    while p.poll() is None:
        sleep(.1)  # Don't waste CPU-cycles
    # Empty STDERR buffer
    err = p.stderr.read()
    print(str(err))
    if p.returncode != 0:
        # The run_command() function is responsible for logging STDERR
        print("Error: " + str(err))
