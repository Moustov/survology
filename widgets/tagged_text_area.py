# https://www.tutorialspoint.com/python/tk_text.htm
from tkinter import Frame, Text, LabelFrame, Menu
from tkinter.constants import *

from widgets.color_utility import random_color


class TaggedTextArea:
    def __init__(self, frame: Frame):
        self.frame = frame
        self.text = None
        self.transcription_content_labelframe = None
        self.menu = None

    def hello(self):
        pass

    def get_frame_pack(self, fill=BOTH, expand=1) -> LabelFrame:
            """
            adds a transcription LabelFrame in a pack-like layout
            """
            self.transcription_content_labelframe = LabelFrame(self.frame, text='Text detail')
            self.transcription_content_labelframe.pack(fill=fill, expand=expand, padx=5, pady=5)
            self._add_ui_content()
            return self.transcription_content_labelframe

    def _add_ui_content(self):
        self.text = Text(self.frame, height=5)
        self.text.insert(INSERT, "Hello.....")
        self.text.insert(END, "Bye Bye.....")
        self.text.pack()
        self.text.tag_add("here", "1.0", "1.4")
        self.text.tag_add("start", "1.8", "1.13")
        self.text.tag_config("here", background=random_color())
        self.text.tag_config("start", background=random_color())
        # right click menu - https://tkdocs.com/tutorial/menus.html
        self.menu = Menu(self.frame, tearoff=0)
        self.menu.add_command(label="Assign tag", command=self.hello)
        self.menu.add_command(label="Delete tag", command=self.hello)
        self.frame.bind("<Button-3>", self._on_right_click)

    def set_text(self, text: str):
        self.text.delete('1.0', END)
        self.text.insert(END, text)

    def _on_right_click(self, event):
        print(event)
        self.menu.post(event.x_root, event.y_root)



