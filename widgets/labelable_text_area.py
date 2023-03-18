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
        self.tags_in_text = {}
        self.tags = {"here":
            {
                "color": "#ABCDAB",
                "description": "a description for the label 'here'"
            }
        }
        self._add_ui_content()

    def add_label_in_text(self):
        selected_text = self.text.selection_get()
        print("selected_text", selected_text)
        text = self.text.get(1.0, "end-1c")
        lines = text.split("\n")
        line_id = 1
        beg_pos = -1
        found = False
        # todo select all occurrencies of a selected text
        for line in lines:
            beg_pos = line.find(selected_text)
            if beg_pos >= 0:
                found = True
                break
            line_id += 1
        if found:
            end_pos = beg_pos + len(selected_text)
            print("here --", beg_pos, text.find(selected_text), line_id, selected_text, f"{line_id}.{beg_pos}",
                  f"{line_id}.{end_pos}")
            self.text.tag_add("here", f"{line_id}.{beg_pos}", f"{line_id}.{end_pos}")
            self.tags_in_text[f"{line_id}.{beg_pos}"] = {"label": "here", "end": f"{line_id}.{end_pos}",
                                                         "text": selected_text}
            print(f"tags_in_text[{line_id}.{beg_pos}]", self.tags_in_text[f"{line_id}.{beg_pos}"])
        else:
            raise ValueError(f"'{selected_text}' not in '{text}'")

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

    def _do_update_text_in_treeview(self):
        """
        updates the listener with the Text content, transcription labels & labels
        """
        text = self.text.get(1.0, "end-1c")
        print("_do_validate_text", text)
        self.listener.set_new_text(text)
        self.listener.set_transcription_labels(self.tags_in_text)
        self.listener.set_labels(self.tags)

    def _add_ui_content(self):
        self.local_frame = Frame(self.local_content_labelframe)
        self.local_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew", ipadx=250, ipady=40)
        #
        self.text = Text(self.local_frame, height=5)
        self.text.grid(row=0, column=0, sticky="ns")
        self.text.tag_config("here", background=self.get_tag_color("here"))
        #
        self.validate_text_button = Button(self.local_frame, text='Update', command=self._do_update_text_in_treeview)
        self.validate_text_button.grid(row=0, column=1)
        #
        # right click menu - https://tkdocs.com/tutorial/menus.html
        self.menu = Menu(self.frame, tearoff=0)
        self.menu.add_command(label="Assign tag", command=self.add_label_in_text)
        self.menu.add_command(label="Assign new tag", command=self.add_label)
        self.menu.add_separator()
        self.menu.add_command(label="Delete tag", command=self.noop)
        self.text.bind("<Button-3>", self._on_right_click)

    def noop(self):
        pass

    def add_label(self):
        new_color = random_color()
        self.tags[new_color] = {}
        self.tags[new_color]["color"] = new_color
        self.tags[new_color]["description"]: f"a description for the label '{new_color}'"

    def set_text(self, text: str, labeled_text: dict):
        # remove all previous tags in Text content
        for tag in self.text.tag_names():
            self.text.tag_remove(tag, "1.0", "end")
        # remove text content
        self.text.delete('1.0', END)
        # set to new text
        self.text.insert(END, text)
        # set tags
        for beg_key in labeled_text.keys():
            print("set_text", labeled_text[beg_key])
            self.text.tag_add(labeled_text[beg_key]["label"], beg_key, labeled_text[beg_key]["end"])
            self.tags_in_text[beg_key] = {"label": labeled_text[beg_key]["label"], "end": labeled_text[beg_key]["end"],
                                          "text": labeled_text[beg_key]["text"]}

    def _on_right_click(self, event):
        print(event)
        self.menu.post(event.x_root, event.y_root)

    def get_tag_color(self, tag: str):
        print("**** get_tag_color", tag, self.tags)
        if self.tags and tag in self.tags.keys():
            return self.tags[tag]["color"]
        raise ValueError(f"the tag {tag} does not exist")
