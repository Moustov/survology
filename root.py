import tkinter
from importlib.metadata import version
from tkinter import Label, Menu, messagebox, END
# https://www.youtube.com/watch?v=XhCfsuMyhXo&list=PLCC34OHNcOtoC6GglhF3ncJ5rLwQrLGnV&index=6
from tkinter.filedialog import askopenfilename

from audiofile_transcript import AudioFileTranscript
from live_transcript import LiveTranscript


class RootWindow(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.search_chords = None
        self.search_cadence = None
        self.live_hearing = None
        self.menu_bar = None
        self._set_layout()

    def _set_layout(self):
        self.title('Survology')
        self.geometry('800x600')
        self._add_menu()
        self._add_content()

    def _add_content(self):
        my_label = Label(self, text="Harmony tools")
        my_label.pack()

    def _add_menu(self):
        """
        https://koor.fr/Python/Tutoriel_Tkinter/tkinter_menu.wp
        :return:
        """
        self.menu_bar = Menu(self)

        menu_file = Menu(self.menu_bar, tearoff=0)
        menu_file.add_command(label="New", command=self.do_something)
        menu_file.add_command(label="Open", command=self.open_file)
        menu_file.add_command(label="Save", command=self.do_something)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", command=self.quit)
        self.menu_bar.add_cascade(label="File", menu=menu_file)

        menu_interview = Menu(self.menu_bar, tearoff=0)
        menu_interview.add_command(label="Live transcription", command=self.do_live_transcription)
        menu_interview.add_command(label="Transcript record", command=self.do_transcript_record)
        self.menu_bar.add_cascade(label="Interview", menu=menu_interview)

        menu_help = Menu(self.menu_bar, tearoff=0)
        menu_help.add_command(label="About", command=self.do_about)
        self.menu_bar.add_cascade(label="Help", menu=menu_help)
        self.config(menu=self.menu_bar)

    def do_live_transcription(self):
        transcript = LiveTranscript()
        transcript.display(self)

    def do_transcript_record(self):
        transcript = AudioFileTranscript()
        transcript.display(self)

    def do_about(self):
        messagebox.showinfo("Survology", f"(c) C. Moustier - 2023")

    def open_file(self):
        file = askopenfilename(title="Choose the file to open",
                               filetypes=[("PNG image", ".png"), ("GIF image", ".gif"), ("All files", ".*")])
        print(file)

    def do_something(self):
        print("Menu clicked")


if __name__ == "__main__":
    app = RootWindow()
    app.mainloop()
