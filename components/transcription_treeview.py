from tkinter import LabelFrame, Scrollbar, Frame
from tkinter.constants import *

from moustovtkwidgets_lib.mtk_edit_table import mtkEditTable, mtkEditTableListener

from components.color_utility import random_color


class TranscriptionTreeview(mtkEditTableListener):
    def __init__(self, frame: Frame):
        self.part_number = 0
        self.frame = frame
        self.horscrlbar = None
        self.verscrlbar = None
        self.transcription_treeview = None
        self.transcription_content_labelframe = None
        self.local_frame = None
        self.previous_part = None

    def get_transcription_treeview_label_frame(self, frame: Frame) -> LabelFrame:
        """
        return a transcription LabelFrame in a pack-like layout
        """
        self.transcription_content_labelframe = LabelFrame(frame, text='Transcription')
        return self.transcription_content_labelframe

    def right_click_fired(self, event):
        """
        event triggered by self.transcription_tree when a right_click is done and the menu is not yet displayed
        to update the menu
        """
        # adapt menu text to previous existing part
        self.previous_part = ""
        for i in self.transcription_treeview.get_children():
            print("i == self.transcription_tree.rowID", i, self.transcription_treeview.rowID)
            data = self.transcription_treeview.item(i)['text']
            if data:
                self.previous_part = data
            if i == self.transcription_treeview.rowID:
                break
        self.transcription_treeview.menu.entryconfig(6, label=f"Assign rows to part '{self.previous_part}'")
        #
        # disable "Assign rows to previous part" if not existing part
        if self.previous_part:
            self.transcription_treeview.menu.entryconfig(6, state="normal")
        else:
            self.transcription_treeview.menu.entryconfig(6, state="disabled")

    def get_ui_content(self, frame: Frame) -> Frame:
        self.local_frame = Frame(frame)
        col_ids = ('chrono', 'Text', 'tags')
        col_titles = ('chrono', 'Text', 'tags')
        self.transcription_treeview = mtkEditTable(self.local_frame, columns=col_ids, column_titles=col_titles)
        self.transcription_treeview.add_listener(self)
        self.transcription_treeview.debug = True
        self.transcription_treeview.column('chrono', anchor=CENTER, width=60, stretch=NO)
        self.transcription_treeview.column('Text', anchor=W, width=200, minwidth=100)
        self.transcription_treeview.column('tags', anchor=CENTER, width=0, stretch=YES)
        self.transcription_treeview.grid(row=0, column=0, columnspan=2, ipadx=200, padx=5, pady=5)
        self.transcription_treeview.column("#0", width=70, stretch=NO)
        #
        self.verscrlbar = Scrollbar(self.local_frame,
                                    orient="vertical",
                                    command=self.transcription_treeview.yview)
        self.verscrlbar.grid(row=0, column=2, sticky="ns")
        self.horscrlbar = Scrollbar(self.local_frame,
                                    orient="horizontal", width=20,
                                    command=self.transcription_treeview.xview)
        self.horscrlbar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.transcription_treeview.configure(xscrollcommand=self.horscrlbar.set, yscrollcommand=self.verscrlbar.set)

        self.transcription_treeview.menu.add_separator()
        self.transcription_treeview.menu.add_command(label="Add part", command=self.set_part)
        self.transcription_treeview.menu.add_command(label="Assign rows to previous part",
                                                     command=self._do_assign_to_part)
        return self.local_frame

    def _do_assign_to_part(self):
        """
        move all row into the previous part
        """
        # selected_row = self.transcription_tree.item(self.transcription_tree.rowID)
        print("_do_assign_to_part", self.transcription_treeview.rowID, self.previous_part)
        is_inside = False
        previous_part_id = None
        pos_in_part = 0
        for i in self.transcription_treeview.get_children():
            data = self.transcription_treeview.item(i)['text']
            if data and self.previous_part == data:
                is_inside = True
                previous_part_id = i
            if is_inside and i != previous_part_id:
                self.transcription_treeview.move(i, previous_part_id, pos_in_part)
                self.transcription_treeview.item(i, tags=self.previous_part)
                pos_in_part += 1
            if i == self.transcription_treeview.rowID:
                break

    def get_timeline(self) -> dict:
        data = self.transcription_treeview.get_data()
        res = {}
        for key in data.keys():
            if type(data[key]) is dict:
                for child_key in data[key].keys():
                    res[child_key] = data[key][child_key]
            else:
                res[key] = data[key]
        return res

    def set_part(self):
        """
        adds a part in the transcription at current rowID
        """
        selected_values = self.transcription_treeview.item(self.transcription_treeview.rowID)
        self.previous_part = self.transcription_treeview.rowID
        values = selected_values.get("values")
        self.part_number += 1
        part_name = f"Part#{self.part_number}".replace(" ", "")
        color = random_color()
        print(part_name, color)
        self.transcription_treeview.tag_configure(part_name, background=color)
        self.transcription_treeview.item(self.transcription_treeview.rowID, text=part_name,
                                         values=values, tags=part_name)

    def get_data(self) -> dict:
        return self.transcription_treeview.get_data()

    def set_data(self, transcription: dict):
        """
        loads a json transcription into self.transcription_tree with colored parts
        transcription = {
            "transcription": {
                "Part#1": {
                    "0": [
                        "00:00:00",
                        "il faut avoir en tête pourquoi veux-tu",
                        ""
                    ],
                    "1": [
                        "00:00:02",
                        "ces pays aussi",
                        ""
                    ],
            ...
                },
            "parts_colors": {},
            "transcription_labels": {
                "15": {
                    "1.109": {
                        "label": "here",
                        "end": "1.119",
                        "text": "associatif"
                    }
                }
            },
            "labels": {
                "here": {
                    "color": "#ABCDAB",
                    "description": "a description for the label 'here'"
                }
            }
        }
        """
        print("ttv set_data", transcription)
        self.transcription_treeview.set_data(transcription)
        for i in self.transcription_treeview.get_children():
            print("===", i)
            text = self.transcription_treeview.item(str(i))['text'].replace(" ", "")
            if text:
                color = random_color()
                print(text, color)
                self.transcription_treeview.tag_configure(text, background=color)
                self.transcription_treeview.item(str(i), tags=text)
                for j in self.transcription_treeview.get_children(str(i)):
                    self.transcription_treeview.item(str(j), tags=text)
