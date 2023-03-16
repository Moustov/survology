import json
import os
import subprocess
import threading
import tkinter
from functools import partial
from tkinter import Label, Button, Frame, Scrollbar, StringVar, LabelFrame, DoubleVar, Scale, Tk
from tkinter.constants import *
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Progressbar

import pygame
from moustovtkwidgets_lib.mtk_edit_table import mtkEditTable
# punctuation: https://github.com/benob/recasepunc
# models : https://alphacephei.com/vosk/models
from vosk import Model, KaldiRecognizer, SetLogLevel



# https://stackoverflow.com/questions/73089784/problem-mixer-music-get-pos-after-set-position-by-mixer-music-set-pos
from widgets.tagged_text_area import TaggedTextArea
from widgets.transcription_treeview import TranscriptionTreeview


def time_code_to_chrono(timecode: float) -> str:
    h = int(timecode // 3600)
    m = int(timecode // 60) % 60
    s = int(timecode % 60)
    return format(f"{str(h).zfill(2)}:{str(m).zfill(2)}:{str(s).zfill(2)}")


def chrono_to_time_code(hh_mm_ss: str) -> int:
    """
    converts hhh:mm:ss.mmm in to nb of seconds
    :param hh_mm_ss:
    :return:
    """
    # print("chrono_to_time_code", hh_mm_ss)
    try:
        parts = hh_mm_ss.split(":")
        # print("parts", parts)
        h = int(parts[0]) * 3600
        m = int(parts[1]) * 60
        s = int(parts[2])
        return h + m + s
    except Exception as e:
        return -1


def get_media_duration(file: str) -> float:
    """

    :param file: multimedia file
    :return: number of seconds
    """
    mm_file = file.replace("'", "\'")
    cmd = rf'ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg -i "{mm_file}" 2>&1 ffmpeg.log'
    print("cmd", cmd)
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    print("output", process.stdout)
    for l in str(process.stdout).split("\\n"):
        if l.strip().startswith("Duration:"):
            d = l.split(",")
            duration = d[0].split(":")
            res = int(duration[1].strip()) * 3600 + int(duration[2]) * 60 + float(duration[3])
            return res


class AudioFileTranscript(tkinter.Tk):
    PROGRESS_BAR_ROW_POSTION = 2
    model = Model(lang="fr")
    SAMPLE_RATE = 16000
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    def __init__(self):
        # UI
        self.labelable_labelframe = None
        self.labelable_widget = None
        self.time_line = None
        self.transcription_content_widget = None
        self.horscrlbar = None
        self.transcription_file_text = None
        self.start_transcription_button = None
        self.player_slider_scale = None
        self.player_slider_value = None
        self.stop_button = None
        self.unpause_button = None
        self.play_button = None
        self.audio_file_label = None
        self.audio_file_text = StringVar(value="(no audio file)")
        self.resume_transcription_button = None
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
        self.select_file_button = None
        self.position_label = None
        self.save_button = None
        self.pause_button = None
        self.freeze_transcription_button = None
        self.progress_bar = None
        # controllers
        self.carry_on = None
        self.debug = True
        self.pause_status = True
        self.duration = 1
        self.refresh_player_position_job = None
        self.current_timecode = None    # in ms
        self.current_timecode_offset = 0
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
        self.frame.grid(row=grid_row, column=grid_col, columnspan=5, sticky='nsew', padx=5, pady=5)
        self.display_audio_file_frame()
        self.display_transcription_controls_frame()
        self.display_transcription_frame()
        self.display_labelable_text_frame()
        self.display_player_frame()
        self.save_button = Button(self.frame, text='Save transcription', command=self._do_save_transcription)
        self.save_button.pack(padx=5, pady=5)

    def _do_transcription_resume(self):
        self.carry_on = True
        listen_thread = threading.Thread(target=self._do_launch_transcription, name="_transcript")
        listen_thread.start()

    def _do_save_transcription(self):
        transcription = self.transcription_tree.get_data()
        with open(f"{self.file_to_transcript}.json", "w", encoding='utf-8') as file:
            json.dump(transcription, file, indent=4, ensure_ascii=False)

    def _do_transcription_freeze(self):
        self.carry_on = False

    def _do_load_audio_file(self):
        self.file_to_transcript = askopenfilename(title="Choose the file to open",
                                                  filetypes=[("MP3", ".mp3"), ("WAV", ".wav"), ("All files", ".*")])
        self.audio_file_text.set("file: " + self.file_to_transcript)
        self.transcription_file_text = self.file_to_transcript + ".json"
        if self.debug:
            print(self.transcription_file_text)
        if os.path.exists(self.transcription_file_text):
            with open(self.transcription_file_text, "r", encoding='utf-8') as json_file:
                transcription = json.load(json_file)
                if self.debug:
                    print("transcription file", transcription)
                self.transcription_content_widget.set_data(transcription)
                self.time_line = self.transcription_content_widget.get_timeline()
        else:
            if self.debug:
                print("No existing transcription found")
        self.duration = get_media_duration(self.file_to_transcript)
        self.duration_text.set("duration: " + time_code_to_chrono(self.duration))
        self.player_slider_scale.configure(to=self.duration)
        self.player_slider_scale.configure(tickinterval=self.duration // 10)
        self._do_player_play()
        self._do_player_pause()
        Tk.update(self.frame)

    def _do_transcription_start(self):
        self.transcription_tree.clear_data()
        self.timecode = None
        self.progress_bar['maximum'] = self.duration
        self.progress_bar.step(2)
        self.progress_bar['value'] = 0
        # self.progress_bar.start()
        print("duration:", self.duration)
        self.carry_on = True
        self.text_index = 0
        self.start = 0
        listen_thread = threading.Thread(target=self._do_launch_transcription, name="_transcript")
        listen_thread.start()

    def _do_launch_transcription(self):
        self.start_transcription_thread(self.file_to_transcript)

    def start_transcription_thread(self, file_path: str):
        time_limit = 2  # seconds
        while self.carry_on and self.start <= self.duration:
            # print("start", start)
            # todo try the ffmpeg may be replaced with SoundFile: https://python-sounddevice.readthedocs.io/en/0.4.5/examples.html
            # todo try import ffmpeg
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
                                                           values=(time_code_to_chrono(self.timecode), txt['text']))
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
        self.time_line = self.transcription_content_widget.get_timeline()
        # self.progress_bar.stop()

    def display_audio_file_frame(self):
        self.file_labelframe = LabelFrame(self.frame, text='File')
        self.file_labelframe.pack(fill=BOTH, expand=1, padx=5, pady=5)
        self.title_label = Label(self.file_labelframe, text="Audio file")
        self.title_label.grid(row=0, column=0, padx=5, pady=5)
        self.select_file_button = Button(self.file_labelframe, text='Select file', command=self._do_load_audio_file)
        self.select_file_button.grid(row=0, column=1, padx=5, pady=5)
        self.audio_file_label = Label(self.file_labelframe, textvariable=self.audio_file_text)
        self.audio_file_label.grid(row=0, column=2, padx=5, pady=5)

    def display_transcription_controls_frame(self):
        self.progression_labelframe = LabelFrame(self.frame, text='Transcription controls')
        self.progression_labelframe.pack(fill=BOTH, expand=1, padx=5, pady=5)
        self.progress_bar = Progressbar(self.progression_labelframe, orient='horizontal', mode='determinate',
                                        length=280)
        self.progress_bar.grid(row=0, column=0, columnspan=3, padx=5, pady=5)
        self.start_transcription_button = Button(self.progression_labelframe, text='start',
                                                 command=self._do_transcription_start)
        self.start_transcription_button.grid(row=1, column=0, padx=5, pady=5)
        self.freeze_transcription_button = Button(self.progression_labelframe, text='freeze',
                                                  command=self._do_transcription_freeze)
        self.freeze_transcription_button.grid(row=1, column=1, padx=5, pady=5)
        self.resume_transcription_button = Button(self.progression_labelframe, text='resume',
                                                  command=self._do_transcription_resume)
        self.resume_transcription_button.grid(row=1, column=2, padx=5, pady=5)
        self.duration_label = Label(self.progression_labelframe, textvariable=self.duration_text)
        self.duration_label.grid(row=1, column=3,padx=5, pady=5)

    def display_labelable_text_frame(self):
        self.labelable_widget = TaggedTextArea(self.frame)
        self.labelable_labelframe = self.labelable_widget.get_frame_pack(fill=BOTH, expand=1)

    def display_transcription_frame(self):
        self.transcription_content_widget = TranscriptionTreeview(self.frame)
        self.transcription_content_labelframe = self.transcription_content_widget.\
            get_transcription_frame_pack(fill=BOTH, expand=1)
        self.transcription_tree = self.transcription_content_widget.transcription_tree
        # http://tkinter.fdex.eu/doc/event.html#events
        # https://stackoverflow.com/questions/32289175/list-of-all-tkinter-events
        self.transcription_tree.bind("<ButtonRelease-1>", self._on_select_transcription_row)
        self.transcription_tree.menu.add_separator()
        self.transcription_tree.menu.add_command(label="Set player", command=self.set_player)

    def set_player(self):
        selected_values = self.transcription_tree.item(self.transcription_tree.rowID)
        values = selected_values.get("values")
        print("set_player",values)
        chrono = chrono_to_time_code(values[0])
        self.current_timecode_offset = chrono * 1000
        self._set_mixer_player_position_only(chrono)
        self._set_mixer_ui_position_only(chrono)

    def _on_select_transcription_row(self, event):
        row_selected_thread = threading.Thread(target=partial(self._select_transcription_row, event),
                                               name="row_selected_thread")
        row_selected_thread.start()

    def _select_transcription_row(self, event):
        tree = event.widget
        # selection = [tree.item(item)["text"] for item in tree.selection()]    # tree part
        row = [tree.item(item)["values"] for item in tree.selection()]
        print("selected items:", row)
        if row:
            current_sec = chrono_to_time_code(row[0][0])
            self.current_timecode_offset = current_sec * 1000
            # for MP3 - https://stackoverflow.com/questions/73089784/problem-mixer-music-get-pos-after-set-position-by-mixer-music-set-pos
            self.current_timecode = 0
            print("_on_select_transcription_line current", current_sec, self.current_timecode_offset)
            # self._set_mixer_player_position_only(self.current_timecode_offset)
            self.player_slider_value.set(current_sec)
            self._set_mixer_ui_position_only(current_sec)
            self.labelable_widget.set_text(row[0][1])
            # self._set_transcription_position(pos)

    def _do_player_play(self):
        # Loading Selected Song
        pygame.mixer.music.load(self.file_to_transcript)
        # Playing Selected Song
        self.player_slider_scale.configure(to=self.duration)
        if self.debug:
            print("duration updated", self.duration)
        self.current_timecode = 0
        self.pause_status = False
        pygame.mixer.music.play(loops=0, start=0)
        self.player_slider_scale.configure(from_=self.current_timecode)
        # self._on_timer_adapt_to_mixer_position()

    def _do_player_pause(self):
        pygame.mixer.music.pause()
        if self.refresh_player_position_job:
            self.pause_status = True
            self.frame.after_cancel(self.refresh_player_position_job)  # Loop every sec
            self.refresh_player_position_job = None

    def _do_player_unpause(self):
        self.pause_status = False
        # pygame.mixer.music.unpause()
        pygame.mixer.music.rewind()  # for MP3 only: https://docs.w3cub.com/pygame/ref/music#pygame.mixer.music.set_pos
        pygame.mixer.music.play(loops=0, start=self.current_timecode / 1000)
        self._on_timer_adapt_to_mixer_position()

    def _do_player_stop(self):
        pygame.mixer.music.stop()
        self.pause_status = True
        if self.refresh_player_position_job:
            self.frame.after_cancel(self.refresh_player_position_job)  # Loop every sec
            self.refresh_player_position_job = None

    def display_player_frame(self):
        player_labelframe = LabelFrame(self.frame, text="Audio player")
        player_labelframe.pack(fill=BOTH, expand=1, padx=5, pady=5)
        #
        # img = PhotoImage(file="img.png")
        # self.play_button = Button(root, image=img, borderwidth=0, command=self._do_play)
        # self.play_button = Button(root, text='|>', command=self._do_play)
        # # self.play_button.grid(row=3, column=0, padx=10)
        # self.play_button.pack()
        #
        # Inserting Play Button
        self.play_button = Button(player_labelframe, text="|>", command=self._do_player_play, width=10, height=1)
        self.play_button.grid(row=0, column=0, padx=5, pady=5)
        # Inserting Pause Button
        self.pause_button = Button(player_labelframe, text="||", command=self._do_player_pause, width=8, height=1)
        self.pause_button.grid(row=0, column=1, padx=5, pady=5)
        # Inserting Unpause Button
        self.unpause_button = Button(player_labelframe, text="UNPAUSE", command=self._do_player_unpause, width=10, height=1)
        self.unpause_button.grid(row=0, column=2, padx=5, pady=5)
        # Inserting Stop Button
        self.stop_button = Button(player_labelframe, text="STOP", command=self._do_player_stop, width=10, height=1)
        self.stop_button.grid(row=0, column=3, padx=5, pady=5)
        self.player_slider_value = DoubleVar()
        self.player_slider_scale = Scale(player_labelframe, to=self.duration if self.duration else 1, orient=HORIZONTAL,
                                         length=500, resolution=1,
                                         showvalue=True, tickinterval=self.duration // 10,
                                         variable=self.player_slider_value,
                                         command=self._on_select_player_position)
        self.player_slider_scale.grid(row=1, column=0, columnspan=4, padx=5, pady=5)

    def _on_select_player_position(self, event):
        """
        what to do when sliding the cursor
        todo: select line in treeview
        :param event:
        :return:
        """
        pos = self.player_slider_value.get()
        self.current_timecode_offset = pos * 1000
        # for MP3 - https://stackoverflow.com/questions/73089784/problem-mixer-music-get-pos-after-set-position-by-mixer-music-set-pos
        self.current_timecode = 0
        print("_on_update_player_position (sec)", pos)
        self._set_mixer_player_position_only(pos)
        self._set_mixer_ui_position_only(pos)
        # self._set_transcription_position(pos)

    def _set_mixer_ui_position_only(self, pos_sec: int):
        print("---_set_mixer_ui_position_only", pos_sec, pygame.mixer.music.get_pos())
        self.current_timecode = pos_sec * 1000
        self.player_slider_value.set(pos_sec)
        self._set_transcription_position(pos_sec)
        # self.pause_status = False
        # self._adapt_to_mixer_position()

    def _set_mixer_player_position_only(self, pos_sec):
        print("---_set_mixer_player_position_only", pos_sec, pygame.mixer.music.get_pos())
        self.current_timecode = pos_sec * 1000
        # pygame.mixer.music.set_pos(self.current_timecode)
        self._do_player_unpause()
        self._do_player_pause()
        # Tk.update(self.frame)

    def _on_timer_adapt_to_mixer_position(self):
        if not self.pause_status:
            self._set_mixer_ui_position_only((self.current_timecode_offset + self.current_timecode) / 1000)
            #
            print("pos update", pygame.mixer.music.get_busy())
            print("_refresh_player_position pos [in millisec]", pygame.mixer.music.get_pos())
            # if pygame.mixer.music.get_busy():
            self.current_timecode = pygame.mixer.music.get_pos()  # .get_pos() returns integer in millisec
            print('***** current ms = ', self.current_timecode_offset, self.current_timecode,
                  self.current_timecode_offset + self.current_timecode )
            # self.player_slider_value.set(self.current_timecode / 1000)  # .set_pos() works in seconds
            # print('slider_value = ', self.player_slider_value.get())
            # # update treeview selection
            # self._set_transcription_position(current_millisec)
            self.refresh_player_position_job = self.frame.after(1000,
                                                                lambda: self._on_timer_adapt_to_mixer_position())  # Loop every sec
            # self.player_slider_scale.set(self.player_slider_value.get())

    def _set_transcription_position(self, pos_sec: int):
        """
        select row in treeview
        todo : when using tree part for interview parts, see https://youtu.be/JM-HrhKIjWU to select children as well
        todo : implement dichotomy search
        :param pos_sec:
        :return:
        """
        prev_sec = 0
        prev_row_id = 0
        for row_id in self.time_line.keys():
            chrono = self.time_line[row_id][0]
            sec = chrono_to_time_code(chrono)
            if prev_sec <= pos_sec < sec:
                self.transcription_tree.selection_set(prev_row_id)
                self.transcription_tree.see(prev_row_id)
                break
            prev_sec = sec
            prev_row_id = row_id
        print("_set_transcription_position", pos_sec, prev_row_id)
