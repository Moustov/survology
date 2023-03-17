# https://www.tutorialspoint.com/python/tk_text.htm
from tkinter import Frame, Text, LabelFrame, Menu, Button
from tkinter.constants import *

from widgets.color_utility import random_color
from widgets.labelable_text_area_listener import LabelableTextAreaListener


class LabelableTextArea:
    def __init__(self, frame: Frame, listener: LabelableTextAreaListener):
        self.frame = frame
        self.listener = listener
        self.text = None
        self.local_frame = None
        self.local_content_labelframe = LabelFrame(self.frame, text='Text detail')
        self.local_frame = None
        self.menu = None
        self._add_ui_content()

    def hello(self):
        pass

    def get_frame_pack(self, fill=BOTH, expand=1) -> LabelFrame:
        """
        adds a transcription LabelFrame in a pack-like layout
        """
        self.local_content_labelframe.pack(fill=fill, expand=expand, padx=5, pady=5)
        return self.local_content_labelframe

    def get_frame_grid(self, row_pos: int, col_pos: int) -> LabelFrame:
        """
        adds a transcription LabelFrame in a grid-like layout
        """
        self.local_content_labelframe.grid(row=row_pos, column=col_pos, padx=5, pady=5)
        return self.local_content_labelframe

    def _do_validate_text(self):
        text = self.text.get(1.0, "end-1c")
        print("_do_validate_text", text)
        self.listener.set_new_text(text)

    def _add_ui_content(self):
        self.local_frame = Frame(self.local_content_labelframe)
        self.local_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew", ipadx=250, ipady=40)
        #
        self.text = Text(self.local_frame, height=5)
        self.text.grid(row=0, column=0, sticky="ns")

        self.text.insert(INSERT, "Hello.....")
        self.text.insert(END, "Bye Bye.....")

        self.text.tag_add("here", "1.0", "1.4")
        self.text.tag_add("start", "1.8", "1.13")
        self.text.tag_config("here", background=random_color())
        self.text.tag_config("start", background=random_color())
        #
        self.validate_text_button = Button(self.local_frame, text='Update', command=self._do_validate_text)
        self.validate_text_button.grid(row=0, column=1)
        #
        # right click menu - https://tkdocs.com/tutorial/menus.html
        self.menu = Menu(self.frame, tearoff=0)
        self.menu.add_command(label="Assign tag", command=self.hello)
        self.menu.add_command(label="Delete tag", command=self.hello)
        self.text.bind("<Button-3>", self._on_right_click)

    def set_text(self, text: str):
        self.text.delete('1.0', END)
        self.text.insert(END, text)

    def _on_right_click(self, event):
        print(event)
        self.menu.post(event.x_root, event.y_root)



