import json
import os
import subprocess
import threading
import tkinter
from functools import partial
from tkinter import Label, Button, Frame, StringVar, LabelFrame, DoubleVar, Scale, Tk
from tkinter.constants import *
from tkinter.filedialog import askopenfilename
from tkinter.ttk import Progressbar

import pygame
# punctuation: https://github.com/benob/recasepunc
# models : https://alphacephei.com/vosk/models
from vosk import Model, KaldiRecognizer, SetLogLevel

# https://stackoverflow.com/questions/73089784/problem-mixer-music-get-pos-after-set-position-by-mixer-music-set-pos
from components.labelable_text_area import LabelableTextArea
from components.labelable_text_area_listener import LabelableTextAreaListener
from components.transcription_treeview import TranscriptionTreeview


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
    try:
        parts = hh_mm_ss.split(":")
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
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    for l in str(process.stdout).split("\\n"):
        if l.strip().startswith("Duration:"):
            d = l.split(",")
            duration = d[0].split(":")
            res = int(duration[1].strip()) * 3600 + int(duration[2]) * 60 + float(duration[3])
            return res


class AudioFileTranscript(tkinter.Tk, LabelableTextAreaListener):
    PROGRESS_BAR_ROW_POSTION = 2
    model = Model(lang="fr")
    SAMPLE_RATE = 16000
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    def __init__(self):
        # UI
        self.labelable_widget_frame = None
        self.labels_treeview = None
        self.transcription_content_widget_frame = None
        self.player_labelframe = None
        self.labelable_labelframe = None
        self.labelable_widget = None
        self.transcription_content_widget = None
        self.horscrlbar = None
        self.start_transcription_button = None
        self.player_slider_scale = None
        self.player_slider_value = DoubleVar()
        self.stop_button = None
        self.unpause_button = None
        self.play_button = None
        self.audio_file_label = None
        self.audio_file_text = StringVar(value="(no audio file)")
        self.resume_transcription_button = None
        self.transcription_content_labelframe = None
        self.transcription_controls_labelframe = None
        self.audio_file_labelframe = None
        self.duration_text = StringVar(value="duration unknown")
        self.duration_label = None
        self.transcription_frame = None
        self.labelable_content_labelframe = None
        self.verscrlbar = None
        self.title_label = None
        self.transcript_button = None
        self.transcription_treeview = None
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
        self.current_timecode = None  # in ms
        self.current_timecode_offset = 0
        # transcription
        self.timecode = None
        self.text_index = 0
        self.file_to_transcript = None
        self.json_labels = None
        self.time_line = None
        self.transcription_file_text = None
        self.json_transcription_labels = None
        self.json_parts_colors = None

        # sound
        SetLogLevel(0)
        self.sound = None
        #
        pygame.mixer.init()

    def get_ui_frame(self, root: tkinter.Tk) -> Frame:
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
        self.audio_file_labelframe = self.get_ui_audio_file_label_frame(self.frame)
        self.audio_file_labelframe.pack(fill=BOTH, expand=1, padx=5, pady=5)
        self.transcription_controls_labelframe = self.get_ui_transcription_controls_labelframe(self.frame)
        self.transcription_controls_labelframe.pack(fill=BOTH, expand=1, padx=5, pady=5)
        self.transcription_content_labelframe = self.get_ui_transcription_content_labelframe(self.frame)
        self.transcription_content_labelframe.pack(fill=BOTH, expand=1, padx=5, pady=5)
        self.labelable_content_labelframe = self.get_ui_labelable_content_labelframe(self.frame)
        self.labelable_content_labelframe.pack(fill=BOTH, expand=1, padx=5, pady=5)
        self.player_labelframe = self.get_player_labelframe(self.frame)
        self.player_labelframe.pack(fill=BOTH, expand=1, padx=5, pady=5)
        self.save_button = Button(self.frame, text='Save transcription', command=self.save_json)
        self.save_button.pack(padx=5, pady=5)
        return self.frame

    def _do_transcription_resume(self):
        self.carry_on = True
        listen_thread = threading.Thread(target=self._do_launch_transcription, name="_transcript")
        listen_thread.start()

    def save_json(self):
        transcription = self.transcription_content_widget.get_data()
        file = f"{self.file_to_transcript}.json"
        transcription_content = {"transcription": transcription,
                                 "parts_colors": self.json_parts_colors,
                                 "transcription_labels": self.json_transcription_labels, "labels": self.json_labels}
        print("save", transcription_content)
        with open(file, "w", encoding='utf-8') as file:
            json.dump(transcription_content, file, indent=4, ensure_ascii=False)

    def load_json(self, file: str):
        """
        loads a transcription formatted json
        """
        if os.path.exists(file):
            with open(file, "r", encoding='utf-8') as json_file:
                transcription_file_content_json = json.load(json_file)
                print("load_json", transcription_file_content_json)

                self.transcription_content_widget.set_data(transcription_file_content_json)

                self.json_parts_colors = transcription_file_content_json["parts_colors"]
                self.json_transcription_labels = transcription_file_content_json["transcription_labels"]
                self.json_labels = transcription_file_content_json["labels"]
                self.labelable_widget.set_label_list(self.json_labels)
                self.labelable_widget.set_text("", {},
                                               self.json_labels)

                for label_key in self.json_labels.keys():
                    print("row_key", label_key, self.labels_treeview.get_children())
                    labels_json = self.labels_treeview.get_data()
                    labels_json[label_key] = {"label": label_key, "description": self.json_labels[label_key]["description"],
                                              "color": self.json_labels[label_key]["color"]
                                              }
                    self.labels_treeview.set_data(labels_json)
                    # values = self.labels_treeview.item(str(label_key))['values']
                    # tags = []
                    # for pos_key in self.labels_treeview[str(label_key)].keys():
                    #     tags.append(self.labels_treeview[str(label_key)][pos_key]['label'])
                    # values[2] = "; ".join(list(dict.fromkeys(tags)))    # add unique labels
                    # self.labels_treeview.item(str(label_key), values=values)

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
            self.load_json(self.transcription_file_text)
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
        self.transcription_treeview.clear_data()
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
                            self.transcription_treeview.insert(parent="", index='end', iid=self.text_index, text="",
                                                               values=(time_code_to_chrono(self.timecode), txt['text']))
                            self.text_index += 1
                            self.transcription_treeview.yview_moveto(1.0)
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

    def get_ui_audio_file_label_frame(self, frame: Frame) -> LabelFrame:
        self.audio_file_labelframe = LabelFrame(frame, text='File')
        self.title_label = Label(self.audio_file_labelframe, text="Audio file")
        self.title_label.grid(row=0, column=0, padx=5, pady=5)
        self.select_file_button = Button(self.audio_file_labelframe, text='Select file',
                                         command=self._do_load_audio_file)
        self.select_file_button.grid(row=0, column=1, padx=5, pady=5)
        self.audio_file_label = Label(self.audio_file_labelframe, textvariable=self.audio_file_text)
        self.audio_file_label.grid(row=0, column=2, padx=5, pady=5)
        return self.audio_file_labelframe

    def get_ui_transcription_controls_labelframe(self, frame: Frame) -> LabelFrame:
        self.transcription_controls_labelframe = LabelFrame(frame, text='Transcription controls')
        self.progress_bar = Progressbar(self.transcription_controls_labelframe, orient='horizontal', mode='determinate',
                                        length=280)
        self.progress_bar.grid(row=0, column=0, columnspan=3, padx=5, pady=5)
        self.start_transcription_button = Button(self.transcription_controls_labelframe, text='start',
                                                 command=self._do_transcription_start)
        self.start_transcription_button.grid(row=1, column=0, padx=5, pady=5)
        self.freeze_transcription_button = Button(self.transcription_controls_labelframe, text='freeze',
                                                  command=self._do_transcription_freeze)
        self.freeze_transcription_button.grid(row=1, column=1, padx=5, pady=5)
        self.resume_transcription_button = Button(self.transcription_controls_labelframe, text='resume',
                                                  command=self._do_transcription_resume)
        self.resume_transcription_button.grid(row=1, column=2, padx=5, pady=5)
        self.duration_label = Label(self.transcription_controls_labelframe, textvariable=self.duration_text)
        self.duration_label.grid(row=1, column=3, padx=5, pady=5)
        return self.transcription_controls_labelframe

    def get_ui_labelable_content_labelframe(self, frame: Frame) -> LabelFrame:
        print("get_ui_labelable_content_labelframe")
        self.labelable_widget = LabelableTextArea(frame, self)
        self.labelable_widget_frame = self.labelable_widget.get_ui_content(frame)
        self.labels_treeview = self.labelable_widget.labels_treeview
        return self.labelable_widget_frame

    def get_ui_transcription_content_labelframe(self, frame: Frame) -> LabelFrame:
        self.transcription_content_widget = TranscriptionTreeview(frame)
        self.transcription_content_widget_frame = self.transcription_content_widget.get_ui_content(frame)
        self.transcription_treeview = self.transcription_content_widget.transcription_treeview
        # http://tkinter.fdex.eu/doc/event.html#events
        # https://stackoverflow.com/questions/32289175/list-of-all-tkinter-events
        self.transcription_treeview.bind("<ButtonRelease-1>", self._on_select_transcription_row)
        self.transcription_treeview.menu.add_separator()
        self.transcription_treeview.menu.add_command(label="Set player", command=self.set_player_from_current_tree_row)
        return self.transcription_content_widget_frame

    def set_new_text(self, text: str):
        """
        set the new edited text
        """
        values = self.transcription_treeview.item(self.transcription_treeview.rowID)['values']
        values[1] = text
        self.transcription_treeview.item(self.transcription_treeview.rowID, values=values)

    def set_labels(self, labels: dict):
        """
        set the new labels
        """
        self.json_labels = labels
        print("aft set_labels", self.json_labels)

    def set_transcription_labels(self, transcription_labels: dict):
        """
        set the new label positions in the text
        """
        self.json_transcription_labels[self.transcription_treeview.rowID] = transcription_labels

        values = self.transcription_treeview.item(self.transcription_treeview.rowID)['values']
        tags = []
        for beg_key in transcription_labels.keys():
            tags.append(transcription_labels[beg_key]['label'])
        values[2] = "; ".join(list(dict.fromkeys(tags)))  # add unique labels
        self.transcription_treeview.item(self.transcription_treeview.rowID, values=values)

    def set_player_from_current_tree_row(self):
        selected_values = self.transcription_treeview.item(self.transcription_treeview.rowID)
        values = selected_values.get("values")
        chrono = chrono_to_time_code(values[0])
        self.current_timecode_offset = chrono * 1000
        self._set_mixer_player_position_only(chrono)
        self._set_mixer_ui_position_only(chrono)

    def _on_select_transcription_row(self, event):
        row_selected_thread = threading.Thread(target=partial(self._on_update_widgets_from_selected_transcription_row,
                                                              event),
                                               name="row_selected_thread")
        row_selected_thread.start()

    def _on_update_widgets_from_selected_transcription_row(self, event):
        """
        updates all depending widget when a row is selected
        should be done in a thread
        """
        tree = event.widget
        print("_on_update_widgets_from_selected_transcription_row", event)
        # selection = [tree.item(item)["text"] for item in tree.selection()]    # tree part
        row = [tree.item(item)["values"] for item in tree.selection()]
        if row:
            self.transcription_treeview.rowID = tree.selection()[0]
            current_sec = chrono_to_time_code(row[0][0])
            self.current_timecode_offset = current_sec * 1000
            # for MP3 - https://stackoverflow.com/questions/73089784/problem-mixer-music-get-pos-after-set-position-by-mixer-music-set-pos
            self.current_timecode = 0
            # self._set_mixer_player_position_only(self.current_timecode_offset)
            self.player_slider_value.set(current_sec)
            self._set_mixer_ui_position_only(current_sec)
            print("self.transcription_labels", "'", self.transcription_treeview.rowID, "'",
                  self.json_transcription_labels)
            transcription = row[0][1]
            print("****", transcription)
            if self.transcription_treeview.rowID in self.json_transcription_labels.keys():
                self.labelable_widget.set_text(transcription,
                                               self.json_transcription_labels[self.transcription_treeview.rowID],
                                               self.json_labels)
            else:
                self.labelable_widget.set_text(transcription, {}, self.json_labels)
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

    def get_player_labelframe(self, frame) -> LabelFrame:
        self.player_labelframe = LabelFrame(frame, text="Audio player")
        #
        # img = PhotoImage(file="img.png")
        # self.play_button = Button(root, image=img, borderwidth=0, command=self._do_play)
        # self.play_button = Button(root, text='|>', command=self._do_play)
        # # self.play_button.grid(row=3, column=0, padx=10)
        # self.play_button.pack()
        #
        # # Inserting Play Button
        # self.play_button = Button(player_labelframe, text="|>", command=self._do_player_play, width=10, height=1)
        # self.play_button.grid(row=0, column=0, padx=5, pady=5)
        # Inserting Pause Button
        self.pause_button = Button(self.player_labelframe, text="||", command=self._do_player_pause, width=8, height=1)
        self.pause_button.grid(row=0, column=1, padx=5, pady=5)
        # Inserting Unpause Button
        self.unpause_button = Button(self.player_labelframe, text="UNPAUSE", command=self._do_player_unpause, width=10,
                                     height=1)
        self.unpause_button.grid(row=0, column=2, padx=5, pady=5)
        # # Inserting Stop Button
        # self.stop_button = Button(player_labelframe, text="STOP", command=self._do_player_stop, width=10, height=1)
        # self.stop_button.grid(row=0, column=3, padx=5, pady=5)

        self.player_slider_scale = Scale(self.player_labelframe, to=self.duration if self.duration else 1,
                                         orient=HORIZONTAL,
                                         length=500, resolution=1,
                                         showvalue=True, tickinterval=self.duration // 10,
                                         variable=self.player_slider_value,
                                         command=self._on_select_player_position)
        self.player_slider_scale.grid(row=1, column=0, columnspan=4, padx=5, pady=5)
        return self.player_labelframe

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
        self._set_mixer_player_position_only(pos)
        self._set_mixer_ui_position_only(pos)
        # self._set_transcription_position(pos)

    def _set_mixer_ui_position_only(self, pos_sec: int):
        self.current_timecode = pos_sec * 1000
        self.player_slider_value.set(pos_sec)
        self._set_transcription_position(pos_sec)
        # self.pause_status = False
        # self._adapt_to_mixer_position()

    def _set_mixer_player_position_only(self, pos_sec):
        self.current_timecode = pos_sec * 1000
        # pygame.mixer.music.set_pos(self.current_timecode)
        self._do_player_unpause()
        self._do_player_pause()
        # Tk.update(self.frame)

    def _on_timer_adapt_to_mixer_position(self):
        if not self.pause_status:
            self._set_mixer_ui_position_only((self.current_timecode_offset + self.current_timecode) / 1000)
            self.current_timecode = pygame.mixer.music.get_pos()  # .get_pos() returns integer in millisec
            self.refresh_player_position_job = self.frame.after(1000,
                                                                lambda: self._on_timer_adapt_to_mixer_position())  # Loop every sec

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
        if not self.time_line:
            self.time_line = self.transcription_content_widget.get_timeline()
        print("_set_transcription_position", "self.time_line", self.time_line)
        for row_id in self.time_line.keys():
            chrono = self.time_line[row_id][0]
            sec = chrono_to_time_code(chrono)
            if prev_sec <= pos_sec < sec:
                self.transcription_treeview.selection_set(prev_row_id)
                self.transcription_treeview.see(prev_row_id)
                break
            prev_sec = sec
            prev_row_id = row_id
