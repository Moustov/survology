import tkinter
from tkinter import Label, Menu, messagebox
# https://www.youtube.com/watch?v=XhCfsuMyhXo&list=PLCC34OHNcOtoC6GglhF3ncJ5rLwQrLGnV&index=6
from tkinter.filedialog import askopenfilename

from download_mp3_youtube import DownloadMP3Youtube
from transcription.audiofile_transcript import AudioFileTranscript
from live_transcript import LiveTranscript


class SurvologyRootWindow(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.audio_file_transcript = None
        self.record_youtube = None
        self.live_transcript = None
        self.menu_bar = None
        # https://stackoverflow.com/questions/1844995/how-to-add-a-scrollbar-to-a-window-with-tkinter
        self.horscrlbar = None
        self.verscrlbar = None
        self.display()

    def display(self):
        self.title('Survology')
        self.geometry('1024x768')
        # self.iconbitmap("resources/survology.ico")
        self._add_menu()
        self._add_toolbar()
        self._add_content()

    def _add_content(self):
        my_label = Label(self, text="Survology v0.1")
        my_label.grid(row=0, column=0)

    def do_youtube_mp3_grabbing(self):
        self.clear_root()
        self.record_youtube = DownloadMP3Youtube()
        self.record_youtube.display(self, grid_row=1, grid_col=0)

    def _add_menu(self):
        """
        https://koor.fr/Python/Tutoriel_Tkinter/tkinter_menu.wp
        :return:
        """
        self.menu_bar = Menu(self)

        menu_file = Menu(self.menu_bar, tearoff=0)
        menu_file.add_command(label="Youtube -> MP3", command=self.do_youtube_mp3_grabbing)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.quit)
        self.menu_bar.add_cascade(label="File", menu=menu_file)

        menu_interview = Menu(self.menu_bar, tearoff=0)
        menu_interview.add_command(label="Live transcription", command=self.do_live_transcription)
        menu_interview.add_command(label="Transcript record", command=self.do_transcript_record)
        self.menu_bar.add_cascade(label="Interview", menu=menu_interview)

        menu_help = Menu(self.menu_bar, tearoff=0)
        menu_help.add_command(label="Configure", command=self.do_configure)
        menu_help.add_command(label="About", command=self.do_about)
        self.menu_bar.add_cascade(label="Help", menu=menu_help)
        self.config(menu=self.menu_bar)

    def do_configure(self):
        # todo : open a config screen to download/set vosk dictionaries
        pass

    def do_live_transcription(self):
        self.clear_root()
        self.live_transcript = LiveTranscript()
        frame = self.live_transcript.get_ui_frame(self)
        frame.grid(row=1, column=0, columnspan=5, sticky='nsew', padx=5, pady=5)

    def do_transcript_record(self):
        self.clear_root()
        self.audio_file_transcript = AudioFileTranscript()
        frame = self.audio_file_transcript.get_ui_frame(self)
        frame.grid(row=1, column=0, columnspan=5, sticky='nsew', padx=5, pady=5)

    def do_about(self):
        messagebox.showinfo("Survology", f"(c) C. Moustier - 2023")

    def open_file(self):
        file = askopenfilename(title="Choose the file to open",
                               filetypes=[("PNG image", ".png"), ("GIF image", ".gif"), ("All files", ".*")])
        print(file)

    def do_something(self):
        print("Menu clicked")

    def _add_toolbar(self):
        pass

    def clear_root(self):
        if self.audio_file_transcript:
            self.audio_file_transcript.frame.grid_remove()
        if self.record_youtube:
            self.record_youtube.frame.grid_remove()
        if self.live_transcript:
            self.live_transcript.frame.grid_remove()


if __name__ == "__main__":
    app = SurvologyRootWindow()
    app.mainloop()
