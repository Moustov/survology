import os
import threading
import tkinter
from tkinter import Label, Entry, Button, Frame
from tkinter.ttk import Progressbar

from moviepy.audio.io.AudioFileClip import AudioFileClip
from pytube import YouTube


class DownloadMP3Youtube(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.list_of_songs = None
        self.song = None
        self.youtube_url = None
        self.url_label = None
        self.search_button = None
        self.progress_bar = None

    def display(self, root: tkinter.Tk, grid_row: int = 0, grid_col: int = 0):
        self.frame = Frame(root)
        self.frame.grid(row=grid_row, column=grid_col)
        self.url_label = Label(self.frame, text="Youtube URL to download")
        self.url_label.pack(padx=5, pady=5)
        self.youtube_url = Entry(self.frame)
        self.youtube_url.pack(padx=5, pady=5)
        self.search_button = Button(self.frame, text='Search', command=self._do_download_mp3_from_url)
        self.search_button.pack(padx=5, pady=5)

        self.progress_bar = Progressbar(self.frame, orient='horizontal', mode='indeterminate', length=280)
        self.progress_bar.pack()

    def _do_download_mp3_from_url(self):
        download_thread = threading.Thread(target=self._download_mp3, name="_download_songs")
        download_thread.start()

    def _download_mp3(self):
        url = self.youtube_url.get()
        self.progress_bar.start()
        print(f"Collecting data from {url}")
        yt = YouTube(url)

        # extract only audio
        video = yt.streams.filter(only_audio=True).first()

        destination = "audio samples/"

        # download the file
        out_file = video.download(output_path=destination)
        if not out_file.lower().endswith("mp3"):
            audio = AudioFileClip(out_file)
            # save the file
            base, ext = os.path.splitext(out_file)
            new_file = base.replace("\\", "/") + '.mp3'
            audio.write_audiofile(new_file)
            audio.close()
            os.remove(out_file)
            # result of success
            print(yt.title + " has been successfully downloaded.")
            print("Download complete... {}".format(new_file))
        self.progress_bar.stop()

