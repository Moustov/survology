from tkinter import LabelFrame, Scrollbar, Frame, Menu
from tkinter.constants import *
from moustovtkwidgets_lib.mtk_edit_table import mtkEditTable, mtkEditTableListener


class TranscriptionTreeview(mtkEditTableListener):
    def __init__(self, frame: Frame):
        self.part_number = 0
        self.frame = frame
        self.horscrlbar = None
        self.verscrlbar = None
        self.transcription_tree = None
        self.transcription_content_labelframe = None
        self.local_frame = None
        self.previous_part = None

    def get_transcription_frame_pack(self, fill=BOTH, expand=1) -> LabelFrame:
        """
        adds a transcription LabelFrame in a pack-like layout
        """
        self.transcription_content_labelframe = LabelFrame(self.frame, text='Transcription')
        self.transcription_content_labelframe.pack(fill=fill, expand=expand, padx=5, pady=5)
        self._add_ui_content()
        return self.transcription_content_labelframe

    def get_transcription_frame_grid(self, row_pos: int, col_pos:int) -> LabelFrame:
        """
        adds a transcription LabelFrame in a grid-like layout
        """
        self.transcription_content_labelframe = LabelFrame(self.frame, text='Transcription')
        self.transcription_content_labelframe.grid(row=row_pos, column=col_pos)
        self._add_ui_content()
        return self.transcription_content_labelframe

    def right_click_fired(self, event):
        """
        event triggered by self.transcription_tree when a right_click is done and the menu is not yet displayed
        to update the menu
        """
        # adapt menu text to previous existing part
        self.previous_part = ""
        for i in self.transcription_tree.get_children():
            print("i == self.transcription_tree.rowID", i, self.transcription_tree.rowID)
            data = self.transcription_tree.item(i)['text']
            if data:
                self.previous_part = data
            if i == self.transcription_tree.rowID:
                break
        self.transcription_tree.menu.entryconfig(6, label=f"Assign rows to part '{self.previous_part}'")
        #
        # disable "Assign rows to previous part" if not existing part
        if self.previous_part:
            self.transcription_tree.menu.entryconfig(6, state="normal")
        else:
            self.transcription_tree.menu.entryconfig(6, state="disabled")

    def _add_ui_content(self):
        col_ids = ('chrono', 'Text', 'tags')
        col_titles = ('chrono', 'Text', 'tags')
        self.local_frame = Frame(self.transcription_content_labelframe)
        self.local_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew", ipadx=250, ipady=40)
        self.transcription_tree = mtkEditTable(self.local_frame, columns=col_ids, column_titles=col_titles)
        self.transcription_tree.add_listener(self)
        self.transcription_tree.debug = True
        self.transcription_tree.column('chrono', anchor=CENTER, width=60, stretch=NO)
        self.transcription_tree.column('Text', anchor=W, width=200, minwidth=100)
        self.transcription_tree.column('tags', anchor=CENTER, width=0, stretch=YES)
        self.transcription_tree.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.transcription_tree.column("#0", width=70, stretch=NO)
        #
        self.verscrlbar = Scrollbar(self.transcription_content_labelframe,
                                    orient="vertical",
                                    command=self.transcription_tree.yview)
        self.verscrlbar.grid(row=0, column=2, sticky="ns")
        self.horscrlbar = Scrollbar(self.transcription_content_labelframe,
                                    orient="horizontal", width=20,
                                    command=self.transcription_tree.xview)
        self.horscrlbar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.transcription_tree.configure(xscrollcommand=self.horscrlbar.set, yscrollcommand=self.verscrlbar.set)

        self.transcription_tree.menu.add_separator()
        self.transcription_tree.menu.add_command(label="Add part", command=self.set_tag)
        self.transcription_tree.menu.add_command(label="Assign rows to previous part",
                                                 command=self._do_assign_to_part)

    def _do_assign_to_part(self):
        """
        move all row into the previous part
        """
        # selected_row = self.transcription_tree.item(self.transcription_tree.rowID)
        print("_do_assign_to_part", self.transcription_tree.rowID, self.previous_part)
        is_inside = False
        previous_part_id = None
        pos_in_part = 0
        for i in self.transcription_tree.get_children():
            print("i", i, self.transcription_tree.rowID)
            data = self.transcription_tree.item(i)['text']
            if data and self.previous_part == data:
                is_inside = True
                previous_part_id = i
            if is_inside and i != previous_part_id:
                print("add sibling", i, previous_part_id, pos_in_part)
                self.transcription_tree.move(i, previous_part_id, pos_in_part)
                pos_in_part += 1
            if i == self.transcription_tree.rowID:
                break

    def set_tag(self):
        selected_values = self.transcription_tree.item(self.transcription_tree.rowID)
        self.previous_part = self.transcription_tree.rowID
        values = selected_values.get("values")
        self.part_number += 1
        print(self.part_number)
        self.transcription_tree.item(self.transcription_tree.rowID, text=f"Part #{self.part_number}", values=values)

