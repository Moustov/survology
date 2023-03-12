import json
import subprocess
import threading
import tkinter
from time import sleep
from tkinter import Label, Button, Frame, Scrollbar, StringVar, LabelFrame
from tkinter.constants import *
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Progressbar

import pygame
from moustovtkwidgets_lib.mtk_edit_table import mtkEditTable
from vosk import Model, KaldiRecognizer, SetLogLevel


# punctuation: https://github.com/benob/recasepunc
# models : https://alphacephei.com/vosk/models


class AudioFileTranscript(tkinter.Tk):
    PROGRESS_BAR_ROW_POSTION = 2
    model = Model(lang="fr")
    SAMPLE_RATE = 16000
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    def __init__(self):
        # UI
        self.audio_file_label = None
        self.audio_file_text = StringVar(value="(no audio file)")
        self.play_button = None
        self.transcription_content_labelframe = None
        self.progression_labelframe = None
        self.file_labelframe = None
        self.duration_text = StringVar(value="duration unknown")
        self.duration_label = None
        self.transcription_frame = None
        self.verscrlbar = None
        self.title_label = None
        self.transcript_button = None
        self.transcription_tree = None
        self.extract_button = None
        self.position_label = None
        self.save_button = None
        self.pause_button = None
        self.stop_button = None
        self.progress_bar = None
        # controllers
        self.carry_on = None
        self.debug = False
        self.pause_status = False
        # transcription
        self.timecode = None
        self.text_index = 0
        self.file_to_transcript = None
        # sound
        SetLogLevel(0)
        self.sound = None
        #
        pygame.mixer.init()

    def display(self, root: tkinter.Tk, grid_row: int = 0, grid_col: int = 0):
        """

        :param root:
        :param grid_row: pos in the root
        :param grid_col: pos in the root
        :return:
        todo: merge lines
        todo: tag lines (ex. Question / Answer or Part) -> involves the TreeView part
        todo: play/pause audio file from a line
        """
        self.frame = Frame(root)
        self.frame.grid(row=grid_row, column=grid_col, columnspan=5, sticky='nsew')
        #
        self.display_audio_file_frame()
        # img = PhotoImage(file="img.png")
        # self.play_button = Button(root, image=img, borderwidth=0, command=self._do_play)
        # self.play_button = Button(root, text='|>', command=self._do_play)
        # # self.play_button.grid(row=3, column=0, padx=10)
        # self.play_button.pack()
        self.display_progression_frame()
        #
        self.display_transcription_frame()
        #
        self.save_button = Button(self.frame, text='Save transcription', command=self._do_save_transcription)
        self.save_button.pack()

    def _do_play(self):
        self.carry_on = True
        listen_thread = threading.Thread(target=self._transcript, name="_transcript")
        listen_thread.start()

    def _do_save_transcription(self):
        transcription = self.transcription_tree.get_data()
        with open(f"{self.file_to_transcript}.json", "w", encoding='utf-8') as file:
            json.dump(transcription, file, indent=4, ensure_ascii=False)

    def _do_stop(self):
        self.carry_on = False

    def _do_extract_text(self):
        self.file_to_transcript = askopenfilename(title="Choose the file to open",
                                                  filetypes=[("MP3", ".mp3"), ("WAV", ".wav"), ("All files", ".*")])
        self.audio_file_text.set("file: " + self.file_to_transcript)
        for row in self.transcription_tree.get_children():
            self.transcription_tree.delete(row)
        self.timecode = None
        print(self.file_to_transcript)
        self.duration = self.get_media_duration(self.file_to_transcript)
        self.duration_text.set("duration: " + self.time_code_to_chrono(self.duration))
        self.progress_bar['maximum'] = self.duration
        self.progress_bar.step(2)
        self.progress_bar['value'] = 0
        # self.progress_bar.start()
        print("duration:", self.duration)
        self.carry_on = True
        self.text_index = 0
        self.start = 0
        listen_thread = threading.Thread(target=self._transcript, name="_transcript")
        listen_thread.start()

    def _transcript(self):
        self.start_transcription(self.file_to_transcript)

    @staticmethod
    def time_code_to_chrono(timecode: float) -> str:
        h = int(timecode // 3600)
        m = int(timecode // 60) % 60
        s = int(timecode % 60)
        return format(f"{str(h).zfill(2)}:{str(m).zfill(2)}:{str(s).zfill(2)}")

    def start_transcription(self, file_path: str):
        time_limit = 2  # seconds
        while self.carry_on and self.start <= self.duration:
            # print("start", start)
            with subprocess.Popen(
                    [r"ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg", "-loglevel", "quiet",
                     "-t", str(time_limit),
                     "-ss", str(self.start),
                     # f"-force_key_frames expr:gte(t,n_forced*{time_limit})",
                     "-i", file_path, "-ar", str(self.SAMPLE_RATE), "-ac", "1", "-f", "s16le",
                     "-"], stdout=subprocess.PIPE) \
                    as process:
                while True:
                    data = process.stdout.read(4000)
                    if len(data) == 0:
                        break
                    if self.rec.AcceptWaveform(data):
                        txt = json.loads(self.rec.Result())
                        if txt['text'] != "":
                            self.transcription_tree.insert(parent="", index='end', iid=self.text_index, text="",
                                                           values=(
                                                               self.time_code_to_chrono(self.timecode), txt['text']))
                            self.text_index += 1
                            self.transcription_tree.yview_moveto(1.0)
                    else:
                        partial = json.loads(self.rec.PartialResult())
                        if partial["partial"] == "":
                            self.timecode = self.start
                        if self.debug:
                            print(self.timecode, partial)
                self.start += time_limit
                self.progress_bar['value'] += time_limit
        # self.progress_bar.stop()

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

    def display_audio_file_frame(self):
        self.file_labelframe = LabelFrame(self.frame, text='File')
        self.file_labelframe.pack(fill=BOTH, expand=1)
        self.title_label = Label(self.file_labelframe, text="Audio file")
        self.title_label.grid(row=0, column=0)
        self.extract_button = Button(self.file_labelframe, text='Select file', command=self._do_extract_text)
        self.extract_button.grid(row=0, column=1)
        self.audio_file_label = Label(self.file_labelframe, textvariable=self.audio_file_text)
        self.audio_file_label.grid(row=0, column=2)

    def display_progression_frame(self):
        self.progression_labelframe = LabelFrame(self.frame, text='Transcription controls')
        self.progression_labelframe.pack(fill=BOTH, expand=1)
        self.progress_bar = Progressbar(self.progression_labelframe, orient='horizontal', mode='determinate',
                                        length=280)
        self.progress_bar.grid(row=0, column=0, columnspan=3)
        self.stop_button = Button(self.progression_labelframe, text='freeze', command=self._do_stop)
        self.stop_button.grid(row=1, column=0)
        self.play_button = Button(self.progression_labelframe, text='run', command=self._do_play)
        self.play_button.grid(row=1, column=1)
        self.duration_label = Label(self.progression_labelframe, textvariable=self.duration_text)
        self.duration_label.grid(row=1, column=2)

    def display_transcription_frame(self):
        self.transcription_content_labelframe = LabelFrame(self.frame, text='Transcription')
        self.transcription_content_labelframe.pack(fill=BOTH, expand=1)
        col_ids = ('chrono', 'Text', 'tags')
        col_titles = ('chrono', 'Text', 'tags')
        self.transcription_tree = mtkEditTable(self.transcription_content_labelframe, columns=col_ids,
                                               column_titles=col_titles)
        self.transcription_tree.debug = True
        # self.transcription_tree['columns'] = ('chrono', 'Text', 'tags')
        # self.transcription_tree.column("#0", width=0, stretch=NO)
        self.transcription_tree.column('chrono', anchor=CENTER, width=30)
        self.transcription_tree.column('Text', anchor=W, width=120)
        self.transcription_tree.column('tags', anchor=CENTER, width=0, stretch=NO)
        # self.transcription_tree.heading("#0", text="", anchor=CENTER)
        # self.transcription_tree.heading('chrono', text="chrono", anchor=CENTER)
        # self.transcription_tree.heading('Text', text="Text", anchor=W)
        # self.transcription_tree.heading('tags', text="tags", anchor=CENTER)
        self.transcription_tree.pack(fill=BOTH, expand=1, side=LEFT)
        #
        self.verscrlbar = Scrollbar(self.transcription_content_labelframe,
                                    orient="vertical",
                                    command=self.transcription_tree.yview)
        self.verscrlbar.pack(side=LEFT)
        # self.horscrlbar = Scrollbar(self.frame,
        #                             orient="horizontal", width=20,
        #                             command=self.transcription_tree.xview)
        # self.horscrlbar.grid(row=3, column=0, sticky='nsew', columnspan=2)
        # self.transcription_tree.configure(xscrollcommand=self.horscrlbar.set)
        #


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
